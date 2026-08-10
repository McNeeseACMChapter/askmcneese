"""SQL-native Class Planner repository for SQLite development and PostgreSQL production."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib, json, os, re
from pathlib import Path
from typing import Iterable, Sequence
from uuid import uuid4

from sqlalchemy import and_, case, delete, distinct, exists, func, insert, or_, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from .db import (availability_overlays, course_activity, courses, database_url_from_environment,
    datasets, instructors, make_engine, meetings, section_instructors, section_notes,
    sections, subjects, sync_locks, sync_runs, sync_subjects, terms)
from .models import SectionRecord, SubjectOption, TermOption


def _now() -> str: return datetime.now(UTC).isoformat()
def _norm(value: str) -> str: return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


class ClassPlannerStore:
    def __init__(self, location: str | Path | Engine) -> None:
        if isinstance(location, Engine):
            self.engine, self.path = location, None
            return
        raw = str(location)
        if "://" not in raw:
            path = Path(raw).resolve(); path.parent.mkdir(parents=True, exist_ok=True)
            raw, self.path = f"sqlite:///{path.as_posix()}", path
        else: self.path = None
        self.engine = make_engine(raw)

    @classmethod
    def from_environment(cls) -> "ClassPlannerStore":
        url = database_url_from_environment()
        return cls(make_engine(url, initialize_local=os.getenv("CLASS_DATA_MODE", "staging") != "live"))

    def _upsert(self, table, values, keys, changed):
        if self.engine.dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as dialect_insert
        else:
            from sqlalchemy.dialects.sqlite import insert as dialect_insert
        stmt = dialect_insert(table).values(**values)
        return stmt.on_conflict_do_update(index_elements=[table.c[key] for key in keys],
            set_={key: getattr(stmt.excluded, key) for key in changed})

    def acquire_sync_lock(self, term_id: str, scope: str = "full") -> str | None:
        key, token = f"{scope}:{term_id}", uuid4().hex
        try:
            with self.engine.begin() as db:
                db.execute(delete(sync_locks).where(sync_locks.c.acquired_at < (datetime.now(UTC)-timedelta(hours=2)).isoformat()))
                db.execute(insert(sync_locks).values(lock_key=key, acquired_at=_now(), owner_token=token))
            return token
        except IntegrityError: return None

    def release_sync_lock(self, term_id: str, owner_token: str | None = None, scope: str = "full") -> None:
        condition = sync_locks.c.lock_key == f"{scope}:{term_id}"
        if owner_token: condition = and_(condition, sync_locks.c.owner_token == owner_token)
        with self.engine.begin() as db: db.execute(delete(sync_locks).where(condition))

    def start_sync(self, term_id: str, source_url: str, parser_version: str) -> int:
        with self.engine.begin() as db:
            result = db.execute(insert(sync_runs).values(source_term_id=term_id, source_url=source_url,
                parser_version=parser_version, started_at=_now(), status="running", details_json="{}"))
            return int(result.inserted_primary_key[0])

    def finish_sync(self, sync_id: int, status: str, details: dict[str, object]) -> None:
        with self.engine.begin() as db: db.execute(update(sync_runs).where(sync_runs.c.id == sync_id).values(
            status=status, finished_at=_now(), details_json=json.dumps(details, sort_keys=True)))

    def record_subject_sync(self, sync_id: int, subject: str, *, started_at: str,
        status: str, section_count: int, duration_ms: int, content_hash: str = "",
        error: str | None = None) -> None:
        """Persist one bounded subject fetch outcome without storing source HTML."""
        with self.engine.begin() as db:
            db.execute(insert(sync_subjects).values(
                sync_id=sync_id, subject=subject, started_at=started_at,
                finished_at=_now(), status=status, section_count=section_count,
                content_hash=content_hash, duration_ms=max(0, duration_ms),
                error=error[:1000] if error else None,
            ))

    def active_dataset_id(self, term_id: str) -> int | None:
        with self.engine.connect() as db:
            value = db.execute(select(terms.c.active_dataset_id).where(
                terms.c.source_term_id == term_id
            )).scalar_one_or_none()
        return int(value) if value is not None else None

    def active_hashes(self, term_id: str) -> dict[str, str]:
        stmt = select(sections.c.id, sections.c.normalized_hash).select_from(
            sections.join(terms, terms.c.active_dataset_id == sections.c.dataset_id)).where(terms.c.source_term_id == term_id)
        with self.engine.connect() as db: rows = db.execute(stmt).all()
        return {str(key): str(value) for key, value in rows}

    def mark_metadata_verified(self, term_id: str, verified_at: str) -> None:
        with self.engine.begin() as db:
            db.execute(update(terms).where(terms.c.source_term_id == term_id).values(
                last_synced_at=verified_at
            ))

    def publish(self, *, term: TermOption, records: Iterable[SectionRecord], fetched_at: str,
        source_url: str, parser_version: str, subject_options: Iterable[SubjectOption] = ()) -> int:
        staged = tuple(records); options = {item.code: item for item in subject_options}
        for item in staged: options.setdefault(item.subject, SubjectOption(item.subject, item.subject))
        digest = hashlib.sha256("".join(sorted(item.normalized_hash for item in staged)).encode()).hexdigest()
        with self.engine.begin() as db:
            result = db.execute(insert(datasets).values(source_term_id=term.source_term_id, fetched_at=fetched_at,
                source_url=source_url, parser_version=parser_version, section_count=len(staged),
                content_hash=digest, lifecycle="active", created_at=_now()))
            dataset_id = int(result.inserted_primary_key[0])
            first = {}
            for item in staged: first.setdefault(item.course_id, item)
            if options: db.execute(insert(subjects), [{"dataset_id":dataset_id,"code":item.code,
                "display_name":item.display_name,"normalized_name":_norm(item.display_name)} for item in options.values()])
            if first: db.execute(insert(courses), [{"id":key,"dataset_id":dataset_id,"source_term_id":item.term_id,
                "subject":item.subject,"course_number":item.course_number,"title":item.title,
                "normalized_code":_norm(f"{item.subject} {item.course_number}"),"normalized_title":_norm(item.title)}
                for key,item in first.items()])
            if staged: db.execute(insert(sections), [{"id":item.id,"dataset_id":dataset_id,"course_id":item.course_id,
                "source_term_id":item.term_id,"crn":item.crn,"section_code":item.section_code,"credits":item.credits,
                "level":item.level,"capacity":item.capacity,"enrolled":item.enrolled,"available":item.available,
                "status":item.status,"part_of_term":item.part_of_term,"source_url":item.source_url,
                "raw_status":item.raw_status,"normalized_hash":item.normalized_hash,"attributes_json":json.dumps(item.attributes)}
                for item in staged])
            meeting_values=[{"dataset_id":dataset_id,"section_id":item.id,"sequence":n,"days_json":json.dumps(m.days),
                "start_time":m.start_time,"end_time":m.end_time,"start_date":m.start_date,"end_date":m.end_date,
                "building_code":m.building_code,"room":m.room,"is_online":m.is_online,"is_tba":m.is_tba,
                "raw_days":m.raw_days,"raw_time":m.raw_time,"raw_dates":m.raw_dates}
                for item in staged for n,m in enumerate(item.meetings)]
            if meeting_values: db.execute(insert(meetings), meeting_values)
            names=sorted({name for item in staged for name in item.instructors})
            if names:
                db.execute(insert(instructors), [{"dataset_id":dataset_id,"source_name":name,
                    "display_name":name,"normalized_name":_norm(name)} for name in names])
                ids={name:int(identifier) for identifier,name in db.execute(select(instructors.c.id,instructors.c.source_name)
                    .where(instructors.c.dataset_id==dataset_id)).all()}
                db.execute(insert(section_instructors), [{"dataset_id":dataset_id,"section_id":item.id,
                    "instructor_id":ids[name]} for item in staged for name in item.instructors])
            notes=[]
            for item in staged:
                for category, values in (("registration",item.registration_notes),("corequisite",item.corequisites),("restriction",item.restrictions)):
                    notes += [{"dataset_id":dataset_id,"section_id":item.id,"category":category,"sequence":n,"text":value}
                        for n,value in enumerate(values)]
            if notes: db.execute(insert(section_notes), notes)
            for item in staged:
                value={"source_term_id":item.term_id,"section_id":item.id,"capacity":item.capacity,
                    "enrolled":item.enrolled,"available":item.available,"status":item.status,"verified_at":fetched_at,
                    "verification_status":"verified","source_url":item.source_url}
                db.execute(self._upsert(availability_overlays,value,("source_term_id","section_id"),
                    ("capacity","enrolled","available","status","verified_at","verification_status","source_url")))
            old=db.execute(select(terms.c.active_dataset_id).where(terms.c.source_term_id==term.source_term_id)).scalar_one_or_none()
            value={"source_term_id":term.source_term_id,"display_name":term.display_name,"active_dataset_id":dataset_id,
                "last_synced_at":fetched_at,"availability_verified_at":fetched_at}
            db.execute(self._upsert(terms,value,("source_term_id",),
                ("display_name","active_dataset_id","last_synced_at","availability_verified_at")))
            if old: db.execute(update(datasets).where(datasets.c.id==old).values(lifecycle="previous"))
        self.cleanup_retention(term.source_term_id)
        return dataset_id

    def cleanup_retention(self, term_id: str, keep: int = 4) -> None:
        with self.engine.begin() as db:
            active=db.execute(select(terms.c.active_dataset_id).where(terms.c.source_term_id==term_id)).scalar_one_or_none()
            ids=list(db.execute(select(datasets.c.id).where(datasets.c.source_term_id==term_id)
                .order_by(datasets.c.created_at.desc())).scalars())
            stale=[item for item in ids[keep:] if item!=active]
            if stale: db.execute(delete(datasets).where(datasets.c.id.in_(stale)))

    def rollback(self, term_id: str, dataset_id: int) -> None:
        """Atomically promote a retained last-known-good dataset for one term."""
        with self.engine.begin() as db:
            target = db.execute(select(
                datasets.c.id, datasets.c.fetched_at
            ).where(and_(
                datasets.c.id == dataset_id,
                datasets.c.source_term_id == term_id,
            ))).mappings().first()
            if target is None:
                raise ValueError("rollback dataset does not belong to the requested term")
            current = db.execute(select(terms.c.active_dataset_id).where(
                terms.c.source_term_id == term_id
            )).scalar_one_or_none()
            if current and current != dataset_id:
                db.execute(update(datasets).where(datasets.c.id == current).values(lifecycle="previous"))
            db.execute(update(datasets).where(datasets.c.id == dataset_id).values(lifecycle="active"))
            db.execute(update(terms).where(terms.c.source_term_id == term_id).values(
                active_dataset_id=dataset_id,
                last_synced_at=target["fetched_at"],
                availability_verified_at=target["fetched_at"],
            ))
            db.execute(delete(availability_overlays).where(
                availability_overlays.c.source_term_id == term_id
            ))

    def list_terms(self) -> list[dict[str, object]]:
        stmt=select(terms.c.source_term_id,terms.c.display_name,datasets.c.section_count,datasets.c.source_url,
            datasets.c.fetched_at).select_from(terms.join(datasets,datasets.c.id==terms.c.active_dataset_id))
        with self.engine.connect() as db: rows=db.execute(stmt.order_by(terms.c.source_term_id.desc())).mappings().all()
        return [{"id":r["source_term_id"],"label":r["display_name"],"sectionCount":r["section_count"],
            "fetchedAt":r["fetched_at"],"sourceUrl":r["source_url"]} for r in rows]

    def _canonical(self, db, term_id: str, query: str) -> str:
        needle=_norm(query)
        aliases=db.execute(select(subjects.c.code,subjects.c.normalized_name).select_from(
            subjects.join(terms,terms.c.active_dataset_id==subjects.c.dataset_id)).where(terms.c.source_term_id==term_id)).all()
        candidates: dict[str, set[str]] = {}
        for code, name in aliases:
            words = str(name).split()
            for alias in (str(name), "".join(word[0] for word in words if word)):
                if len(alias) >= 2:
                    candidates.setdefault(alias, set()).add(str(code))
        for alias in sorted(candidates, key=len, reverse=True):
            codes = candidates[alias]
            if len(codes) == 1 and (needle == alias or needle.startswith(alias + " ")):
                return _norm(next(iter(codes)) + needle[len(alias):])
        return needle

    def search_courses(self, term_id: str, *, query: str = "", open_only: bool = False,
        online_only: bool = False, days: tuple[str,...] = (), time_of_day: str = "any", limit: int = 40) -> list[dict[str,object]]:
        joined=courses.join(terms,terms.c.active_dataset_id==courses.c.dataset_id).join(sections,and_(
            sections.c.dataset_id==courses.c.dataset_id,sections.c.course_id==courses.c.id)).outerjoin(
            availability_overlays,and_(availability_overlays.c.source_term_id==sections.c.source_term_id,
            availability_overlays.c.section_id==sections.c.id))
        with self.engine.connect() as db:
            needle=self._canonical(db,term_id,query); conditions=[terms.c.source_term_id==term_id]
            effective=func.coalesce(availability_overlays.c.status,sections.c.status)
            fuzzy_score = None
            if needle:
                person=exists(select(1).select_from(section_instructors.join(instructors,
                    instructors.c.id==section_instructors.c.instructor_id)).where(and_(
                    section_instructors.c.dataset_id==sections.c.dataset_id,
                    section_instructors.c.section_id==sections.c.id,instructors.c.normalized_name.like(f"%{needle}%"))))
                matches = [
                    courses.c.normalized_code.like(f"%{needle}%"),
                    courses.c.normalized_title.like(f"%{needle}%"),
                    sections.c.crn.like(f"%{needle}%"),
                    person,
                ]
                if self.engine.dialect.name == "postgresql" and len(needle) >= 3:
                    fuzzy_score = func.greatest(
                        func.similarity(courses.c.normalized_code, needle),
                        func.similarity(courses.c.normalized_title, needle),
                    )
                    matches.append(fuzzy_score >= 0.28)
                conditions.append(or_(*matches))
            if open_only: conditions.append(effective=="open")
            if online_only: conditions.append(exists(select(1).where(and_(meetings.c.dataset_id==sections.c.dataset_id,
                meetings.c.section_id==sections.c.id,meetings.c.is_online.is_(True)))))
            for day in days: conditions.append(exists(select(1).where(and_(meetings.c.dataset_id==sections.c.dataset_id,
                meetings.c.section_id==sections.c.id,meetings.c.days_json.like(f'%"{day}"%')))))
            if time_of_day!="any":
                windows={"morning":(None,"12:00"),"afternoon":("12:00","17:00"),"evening":("17:00",None)}; start,end=windows[time_of_day]
                checks=[meetings.c.dataset_id==sections.c.dataset_id,meetings.c.section_id==sections.c.id,meetings.c.start_time.is_not(None)]
                if start: checks.append(meetings.c.start_time>=start)
                if end: checks.append(meetings.c.start_time<end)
                conditions.append(exists(select(1).where(and_(*checks))))
            stmt=select(courses.c.id,courses.c.subject,courses.c.course_number,courses.c.title,
                func.min(sections.c.credits).label("credits"),func.count(distinct(sections.c.id)).label("section_count"),
                func.sum(case((effective=="open",1),else_=0)).label("open_count")).select_from(joined).where(and_(*conditions))
            stmt=stmt.group_by(courses.c.id,courses.c.subject,courses.c.course_number,courses.c.title)
            order = [
                case((courses.c.normalized_code == needle, 0), else_=1) if needle else courses.c.subject,
            ]
            if fuzzy_score is not None:
                order.append(fuzzy_score.desc())
            order.extend((courses.c.subject, courses.c.course_number))
            rows=db.execute(stmt.order_by(*order).limit(max(1,min(limit,100)))).mappings().all()
        result=[{"id":r["id"],"subject":r["subject"],"courseNumber":r["course_number"],"title":r["title"],
            "credits":float(r["credits"] or 0),"sectionCount":int(r["section_count"] or 0),"openCount":int(r["open_count"] or 0),"sections":[]} for r in rows]
        if needle: result.sort(key=lambda x:(0 if _norm(f"{x['subject']} {x['courseNumber']}")==needle else 1,_norm(str(x["title"]))))
        return result

    def get_course(self, term_id: str, course_id: str) -> dict[str,object] | None:
        query=" ".join(course_id.split(":")[-2:])
        return next((x for x in self.search_courses(term_id,query=query,limit=100) if x["id"]==course_id),None)

    def get_course_sections(self,term_id:str,course_id:str,*,limit:int=6,offset:int=0,selected_ids:Sequence[str]=())->dict[str,object]:
        all_items=self._hydrate(self._rows(term_id,course_id=course_id))
        selected=self._hydrate(self._rows(term_id,section_ids=selected_ids)) if selected_ids else []
        all_items.sort(key=lambda x:(2 if self._conflicts(x,selected) else 0,1 if x["status"]=="closed" else 0,str(x["sectionNumber"])))
        limit=max(1,min(limit,24)); offset=max(0,offset); page=all_items[offset:offset+limit]
        self.mark_course_opened(term_id,course_id)
        return {"sections":page,"total":len(all_items),"limit":limit,"offset":offset,
            "hasMore":offset+len(page)<len(all_items),"nextOffset":offset+len(page) if offset+len(page)<len(all_items) else None}

    def get_section(self,section_id:str)->dict[str,object]|None:
        items=self._hydrate(self._rows(section_id.split(":",1)[0],section_ids=(section_id,)))
        return items[0] if items else None

    def _rows(self,term_id:str,*,course_id:str|None=None,section_ids:Sequence[str]=())->list[dict[str,object]]:
        joined=sections.join(terms,terms.c.active_dataset_id==sections.c.dataset_id).join(datasets,datasets.c.id==sections.c.dataset_id).join(
            courses,and_(courses.c.dataset_id==sections.c.dataset_id,courses.c.id==sections.c.course_id)).outerjoin(availability_overlays,and_(
            availability_overlays.c.source_term_id==sections.c.source_term_id,availability_overlays.c.section_id==sections.c.id))
        stmt=select(sections,courses.c.subject,courses.c.course_number,courses.c.title,datasets.c.fetched_at,
            availability_overlays.c.capacity.label("ocap"),availability_overlays.c.enrolled.label("oenr"),
            availability_overlays.c.available.label("oavail"),availability_overlays.c.status.label("ostatus"),
            availability_overlays.c.verified_at.label("verified"),availability_overlays.c.verification_status).select_from(joined).where(terms.c.source_term_id==term_id)
        if course_id: stmt=stmt.where(sections.c.course_id==course_id)
        if section_ids: stmt=stmt.where(sections.c.id.in_(tuple(section_ids)))
        with self.engine.connect() as db: return [dict(x) for x in db.execute(stmt.order_by(sections.c.section_code)).mappings().all()]

    def _hydrate(self,rows:list[dict[str,object]])->list[dict[str,object]]:
        if not rows:return []
        dataset_id=int(rows[0]["dataset_id"]); ids=[str(x["id"]) for x in rows]
        with self.engine.connect() as db:
            mrows=db.execute(select(meetings).where(and_(meetings.c.dataset_id==dataset_id,meetings.c.section_id.in_(ids))).order_by(meetings.c.section_id,meetings.c.sequence)).mappings().all()
            irows=db.execute(select(section_instructors.c.section_id,instructors.c.display_name).select_from(section_instructors.join(instructors,instructors.c.id==section_instructors.c.instructor_id)).where(and_(section_instructors.c.dataset_id==dataset_id,section_instructors.c.section_id.in_(ids)))).all()
            nrows=db.execute(select(section_notes.c.section_id,section_notes.c.category,section_notes.c.text).where(and_(section_notes.c.dataset_id==dataset_id,section_notes.c.section_id.in_(ids))).order_by(section_notes.c.sequence)).all()
        mm={key:[] for key in ids}; im={key:[] for key in ids}; nm={key:{} for key in ids}
        for m in mrows:mm[str(m["section_id"])].append({"type":"Online" if m["is_online"] else "Class","days":json.loads(str(m["days_json"])),"startTime":m["start_time"],"endTime":m["end_time"],"startDate":m["start_date"],"endDate":m["end_date"],"building":m["building_code"],"room":m["room"],"isOnline":bool(m["is_online"]),"isTba":bool(m["is_tba"])})
        for key,name in irows:im[str(key)].append(str(name))
        for key,category,text in nrows:nm[str(key)].setdefault(str(category),[]).append(str(text))
        result=[]
        for r in rows:
            key=str(r["id"]); flags=[m["isOnline"] for m in mm[key]]; verified=r["verified"] or r["fetched_at"]
            value=lambda overlay,base:r[overlay] if r[overlay] is not None else r[base]
            result.append({"id":key,"courseId":r["course_id"],"termId":r["source_term_id"],"crn":r["crn"],"sectionNumber":r["section_code"],
                "subject":r["subject"],"courseNumber":r["course_number"],"title":r["title"],"credits":r["credits"],"capacity":value("ocap","capacity"),
                "enrolled":value("oenr","enrolled"),"available":value("oavail","available"),"seatsRemaining":value("oavail","available"),
                "status":r["ostatus"] or r["status"],"partOfTerm":r["part_of_term"],"instructor":", ".join(im[key]) or None,"meetings":mm[key],
                "modality":"Online" if flags and all(flags) else "Hybrid" if any(flags) else "In person","updatedAt":verified,"metadataUpdatedAt":r["fetched_at"],
                "availabilityVerifiedAt":verified,"availabilityStatus":r["verification_status"] or "snapshot","sourceUrl":r["source_url"],
                "registrationNotes":nm[key].get("registration",[]),"corequisites":nm[key].get("corequisite",[]),"restrictions":nm[key].get("restriction",[])})
        return result

    @staticmethod
    def _conflicts(candidate,selected)->bool:
        for other in selected:
            if other["courseId"]==candidate["courseId"]:continue
            for a in candidate["meetings"]:
                for b in other["meetings"]:
                    if a.get("startTime") and b.get("startTime") and set(a["days"])&set(b["days"]) and a["startTime"]<b["endTime"] and b["startTime"]<a["endTime"]:return True
        return False

    def mark_course_opened(self,term_id:str,course_id:str)->None:
        value={"source_term_id":term_id,"course_id":course_id,"last_opened_at":_now()}
        with self.engine.begin() as db:db.execute(self._upsert(course_activity,value,("source_term_id","course_id"),("last_opened_at",)))

    def active_courses(self,term_id:str,*,since_minutes:int=60,limit:int=30)->list[str]:
        cutoff=(datetime.now(UTC)-timedelta(minutes=since_minutes)).isoformat()
        stmt=select(course_activity.c.course_id).where(and_(course_activity.c.source_term_id==term_id,
            course_activity.c.last_opened_at>=cutoff)).order_by(course_activity.c.last_opened_at.desc()).limit(limit)
        with self.engine.connect() as db:return list(db.execute(stmt).scalars())

    def update_availability(self,records:Iterable[SectionRecord],verified_at:str,*,status:str="verified")->int:
        items=tuple(records)
        with self.engine.begin() as db:
            for item in items:
                value={"source_term_id":item.term_id,"section_id":item.id,"capacity":item.capacity,"enrolled":item.enrolled,"available":item.available,
                    "status":item.status,"verified_at":verified_at,"verification_status":status,"source_url":item.source_url}
                db.execute(self._upsert(availability_overlays,value,("source_term_id","section_id"),("capacity","enrolled","available","status","verified_at","verification_status","source_url")))
            if items:db.execute(update(terms).where(terms.c.source_term_id.in_({x.term_id for x in items})).values(availability_verified_at=verified_at))
        return len(items)

    def freshness(self,term_id:str)->dict[str,object]|None:
        stmt=select(datasets.c.fetched_at,datasets.c.source_url,datasets.c.section_count,datasets.c.parser_version,terms.c.last_synced_at,terms.c.availability_verified_at).select_from(terms.join(datasets,datasets.c.id==terms.c.active_dataset_id)).where(terms.c.source_term_id==term_id)
        with self.engine.connect() as db:r=db.execute(stmt).mappings().first()
        if not r:return None
        availability=r["availability_verified_at"] or r["fetched_at"]; age=max(0,(datetime.now(UTC)-datetime.fromisoformat(str(availability))).total_seconds())
        return {"name":"McNeese Class Search","url":r["source_url"],"fetchedAt":r["fetched_at"],"metadataVerifiedAt":r["last_synced_at"] or r["fetched_at"],
            "availabilityVerifiedAt":availability,"availabilityState":"fresh" if age<=int(os.getenv("CLASS_AVAILABILITY_FRESH_SECONDS","900")) else "stale",
            "availabilityAgeSeconds":int(age),"sectionCount":r["section_count"],"parserVersion":r["parser_version"],"mode":os.getenv("CLASS_DATA_MODE","staging")}
