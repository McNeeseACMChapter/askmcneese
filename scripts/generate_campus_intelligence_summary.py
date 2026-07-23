"""Generate the systemic AskMcNeese campus-intelligence architecture PDF.

The PDF intentionally contains architecture and measured baseline behavior only.
It does not embed time-sensitive university facts.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge" / "campus_intelligence"
OUT = ROOT / "output" / "pdf" / "AskMcNeese_Campus_Intelligence_Architecture.pdf"

NAVY = colors.HexColor("#071B33")
BLUE = colors.HexColor("#0057B8")
GOLD = colors.HexColor("#F2B705")
ICE = colors.HexColor("#EEF4FA")
INK = colors.HexColor("#152235")
MUTED = colors.HexColor("#5B6B7E")
GREEN = colors.HexColor("#19734A")
RED = colors.HexColor("#A63A3A")
WHITE = colors.white


class SectionBand(Flowable):
    def __init__(self, label: str, title: str, width: float, height: float = 46):
        super().__init__()
        self.label = label
        self.title = title
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        c.setFillColor(NAVY)
        c.roundRect(0, 0, self.width, self.height, 7, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(13, self.height - 15, self.label.upper())
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(13, 11, self.title)


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DeckTitle", fontName="Helvetica-Bold", fontSize=27, leading=31, textColor=WHITE, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="DeckSub", fontName="Helvetica", fontSize=11, leading=16, textColor=colors.HexColor("#D7E4F3")))
    styles.add(ParagraphStyle(name="Kicker", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=GOLD, spaceAfter=7))
    styles.add(ParagraphStyle(name="H2x", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=NAVY, spaceBefore=8, spaceAfter=6))
    styles.add(ParagraphStyle(name="Bodyx", fontName="Helvetica", fontSize=8.7, leading=12.4, textColor=INK, spaceAfter=5))
    styles.add(ParagraphStyle(name="Smallx", fontName="Helvetica", fontSize=7.2, leading=9.6, textColor=MUTED))
    styles.add(ParagraphStyle(name="Cell", fontName="Helvetica", fontSize=6.4, leading=8.1, textColor=INK))
    styles.add(ParagraphStyle(name="CellWhite", fontName="Helvetica-Bold", fontSize=6.4, leading=8.1, textColor=WHITE, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="Metric", fontName="Helvetica-Bold", fontSize=18, leading=20, textColor=NAVY, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="MetricLabel", fontName="Helvetica", fontSize=6.8, leading=8.5, textColor=MUTED, alignment=TA_CENTER))
    return styles


S = _styles()


def P(text: str, style: str = "Bodyx") -> Paragraph:
    return Paragraph(text, S[style])


def table(data, widths, header=True, font=6.4, row_bgs=True):
    cooked = []
    for r, row in enumerate(data):
        cooked.append([P(str(v), "CellWhite" if header and r == 0 else "Cell") for v in row])
    t = Table(cooked, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#C9D6E3")),
    ]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
    if row_bgs:
        for idx in range(1 if header else 0, len(data)):
            if idx % 2 == 0:
                commands.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#F6F9FC")))
    t.setStyle(TableStyle(commands))
    return t


def metric(value, label):
    t = Table([[P(value, "Metric")], [P(label, "MetricLabel")]], colWidths=[1.27 * inch], rowHeights=[0.35 * inch, 0.36 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ICE),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C9DA")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def page_header(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFillColor(NAVY)
        canvas.rect(0, letter[1] - 25, letter[0], 25, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawString(36, letter[1] - 16, "ASKMCNEESE  /  CAMPUS INTELLIGENCE ARCHITECTURE")
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(letter[0] - 36, 20, f"{doc.page:02d}")
    canvas.restoreState()


def cover(story):
    story.append(Spacer(1, 0.55 * inch))
    band = Table([[P("SYSTEMIC BACKEND CONTRACT", "Kicker")]], colWidths=[6.6 * inch])
    band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GOLD), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.append(band)
    hero = Table([[P("AskMcNeese<br/>Campus Intelligence Architecture", "DeckTitle")], [P("A domain-general compiler, executable route policy, governed evidence model, and non-black-box operating contract.", "DeckSub")]], colWidths=[6.6 * inch])
    hero.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY), ("LEFTPADDING", (0, 0), (-1, -1), 24), ("RIGHTPADDING", (0, 0), (-1, -1), 24), ("TOPPADDING", (0, 0), (-1, 0), 30), ("BOTTOMPADDING", (0, 0), (-1, 0), 14), ("TOPPADDING", (0, 1), (-1, 1), 0), ("BOTTOMPADDING", (0, 1), (-1, 1), 30)]))
    story.append(hero)
    story.append(Spacer(1, 0.28 * inch))
    story.append(P("CONTROLLING PRINCIPLE", "Kicker"))
    story.append(P("AskMcNeese is an intelligent operational interface to McNeese - not a website-search wrapper and not a collection of category-specific workflows.", "H2x"))
    story.append(P("Employment and admissions are proof domains. The same interpretation, routing, retrieval, evidence, freshness, rendering, and telemetry framework applies to the full campus ecosystem.", "Bodyx"))
    story.append(Spacer(1, 0.25 * inch))
    story.append(table([
        ["Contract", "What this PDF fixes"],
        ["Universal query representation", "Natural language becomes domain + intent + audience + freshness + risk + required fields."],
        ["Executable heat map", "Every route is REQUIRED, PRIMARY, CONDITIONAL, FALLBACK, FORBIDDEN, or NOT_APPLICABLE - with a reason."],
        ["Evidence before prose", "Validated fields, freshness, ownership, citations, and action links determine whether an answer may be rendered."],
        ["Inspectable operation", "Executed, skipped, failed, and rejected routes are correlated to one query trace."],
    ], [1.65*inch, 4.95*inch]))


def build_story():
    packs = json.loads((DATA / "domain_packs.json").read_text(encoding="utf-8-sig"))["packs"]
    taxonomy = json.loads((DATA / "domain_taxonomy.json").read_text(encoding="utf-8-sig"))["domains"]
    groups = json.loads((DATA / "source_groups.json").read_text(encoding="utf-8-sig"))["groups"]
    policies = json.loads((DATA / "route_policies.json").read_text(encoding="utf-8-sig"))
    failures = json.loads((DATA / "failure_taxonomy.json").read_text(encoding="utf-8-sig"))["failures"]
    traces = json.loads((ROOT / "docs" / "backend_architecture" / "baseline_traces.json").read_text(encoding="utf-8-sig"))["traces"]
    story = []
    cover(story)
    story.append(PageBreak())

    story.append(SectionBand("01 / diagnosis", "What the current system proves", 6.6*inch))
    story.append(Spacer(1, 12))
    story.append(Table([[metric("4,733", "governed registry rows") , metric("4,700", "runtime-eligible sources"), metric("186", "rows with ingest time"), metric("1,500", "live Chroma chunks")]], colWidths=[1.65*inch]*4))
    story.append(Spacer(1, 12))
    story.append(P("Registry breadth is not retrieval coverage", "H2x"))
    story.append(P("A registered URL, a successfully fetched source, a chunk in the active collection, and evidence accepted for one query are four different states. The current system has no single manifest that reconciles them, so link volume can look like capability while answers remain shallow.", "Bodyx"))
    rows=[["Proof query","Observed","Architectural diagnosis"]]
    for t in traces:
        if t["domain"] in {"capability_discovery","employment","admissions","academic_calendar","catalog","forms","directory","policy"}:
            rows.append([t["question"], f"{t.get('wall_ms','?')} ms", t["observed_result"]])
    story.append(table(rows, [2.0*inch, 0.72*inch, 3.88*inch]))
    story.append(PageBreak())

    story.append(SectionBand("02 / target system", "One compiler, many configurations", 6.6*inch))
    story.append(Spacer(1, 14))
    pipeline = [[P(x,"CellWhite") for x in ["Natural language","Campus Query","Route policy","Retrieval primitives","Evidence gate","Answer shape"]]]
    pt=Table(pipeline, colWidths=[1.1*inch]*6, rowHeights=[0.55*inch])
    pt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),BLUE),("GRID",(0,0),(-1,-1),1,WHITE),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    story.append(pt)
    story.append(Spacer(1, 12))
    story.append(P("The compiler produces a campus operation", "H2x"))
    story.append(P("Topic alone is insufficient. The operation includes domain, subdomain, reusable intent, action, entities, audience, freshness class, risk, answer shape, source groups, required evidence fields, confidence, ambiguities, and whether clarification is materially necessary.", "Bodyx"))
    story.append(table([
        ["Layer","Configuration - not a duplicate workflow"],
        ["Domain pack","Vocabulary, supported intents, defaults, source groups, evidence fields, clarification and cache rules."],
        ["Route policy","Channel state, reason, condition, precedence, bounded concurrency, and fallback."],
        ["Source group","Owner, trust, content type, structure, freshness, crawl/parse strategy, authentication, action-link expectation."],
        ["Specialist","Optional shared-interface adapter only when stable record structure improves accuracy or latency."],
        ["Renderer","Template selected by validated answer shape; LLM synthesis only where evidence-supported prose is useful."],
    ], [1.2*inch, 5.4*inch]))
    story.append(Spacer(1, 12))
    story.append(P(f"Current contract: <b>{len(taxonomy)}</b> taxonomy entries -> <b>{len(packs)}</b> shared domain packs -> <b>{len(groups)}</b> governed source groups.", "Bodyx"))
    story.append(PageBreak())

    story.append(SectionBand("03 / route heat map", "From flags to explainable policy", 6.6*inch))
    story.append(Spacer(1, 10))
    current = [
        ["Intent","KB","Official","Specialist","Companion","Agentic"],
        ["Academic calendar","OFF","PRIMARY","PRIMARY","OFF","OFF"],
        ["Degree plan","OFF","PRIMARY","PRIMARY","OFF","OFF"],
        ["Course catalog","OFF","PRIMARY","PRIMARY","OFF","OFF"],
        ["Policy / suspension","OFF","PRIMARY","COND.","OFF","OFF"],
        ["Form lookup","OFF","PRIMARY","PRIMARY","OFF","OFF"],
        ["Career / Handshake","OFF","PRIMARY","PRIMARY","OFF","OFF"],
        ["Faculty identity","PRIMARY","PRIMARY","PRIMARY","OFF","OFF"],
        ["Faculty ratings","PRIMARY","PRIMARY","COND.","PRIMARY","OFF"],
        ["Organization","OFF","OFF","COND.","PRIMARY","OFF"],
        ["Social profile","OFF","OFF","OFF","PRIMARY","OFF"],
        ["Athletics / current","OFF","PRIMARY","COND.","OFF","OFF"],
        ["General campus","PRIMARY","PRIMARY","OFF","OFF","OFF"],
    ]
    story.append(P("Current representative matrix", "H2x"))
    story.append(table(current, [1.55*inch, 0.75*inch, 1.0*inch, 1.0*inch, 1.0*inch, 0.9*inch]))
    story.append(Spacer(1, 9))
    story.append(P("Systemic interpretation", "H2x"))
    story.append(P("OFF is sometimes an authority boundary and sometimes missing implementation. Multiple PRIMARY routes can cause duplicate work, ranking ambiguity, citation clutter, and tail latency. The replacement policies resolve every channel to a state plus reason and condition; they do not blindly enable everything.", "Bodyx"))
    story.append(table([
        ["State","Operational meaning"],
        ["REQUIRED","Must succeed before the answer can make the material claim without qualification."],
        ["PRIMARY","Preferred acquisition route; precedence decides who runs first."],
        ["CONDITIONAL","Allowed only when its machine-readable condition evaluates true."],
        ["FALLBACK","Runs only after a recorded insufficiency or failure."],
        ["FORBIDDEN","Authority, safety, privacy, or product-policy boundary."],
        ["NOT_APPLICABLE","No semantic role for this operation."],
    ], [1.25*inch, 5.35*inch]))
    story.append(PageBreak())

    story.append(SectionBand("04 / policy", "Routing by information characteristic", 6.6*inch))
    story.append(Spacer(1, 10))
    rows=[["Template","Precedence","Why"]]
    why={
      "static_fact":"Start with governed indexed evidence; verify only when weak, stale, current, or actionable.",
      "term_fact":"Use version/term records and require current official confirmation for material claims.",
      "live_fact":"Prefer freshness-aware records and require timestamped official/approved-owner verification.",
      "action_request":"Require an owned, active, validated link; broad web synthesis is forbidden.",
      "high_risk_policy":"Require direct official evidence; companions and broad agentic synthesis are forbidden.",
      "personal":"Only an authenticated connector can establish personal status; public routes explain process only.",
      "capability":"Generate from active configuration with no retrieval and no LLM call."
    }
    for name, cfg in policies["templates"].items():
        rows.append([name.replace("_"," "), " -> ".join(cfg["precedence"]), why[name]])
    story.append(table(rows,[1.1*inch,2.35*inch,3.15*inch]))
    story.append(Spacer(1, 10))
    story.append(P("Precedence before fanout", "H2x"))
    story.append(P("A route may run concurrently only when the policy declares a bounded concurrency group, such as a term specialist plus direct official verification. Otherwise, the next route waits for a typed insufficiency. This makes latency, fallback, and failure causally explainable.", "Bodyx"))
    story.append(PageBreak())

    story.append(SectionBand("05 / evidence", "Required fields decide when the system may answer", 6.6*inch))
    story.append(Spacer(1, 10))
    story.append(table([
      ["Operation","Minimum evidence contract"],
      ["Admissions requirements","Correct audience; official requirement source; current deadline only when asked; application link when actionable."],
      ["Employment discovery","Current source; category; opportunity or verified portal; application link; last-verified timestamp."],
      ["Form lookup","Correct form; active URL; owning office; content type; current validation state."],
      ["Contact lookup","Correct person/office; official role evidence; at least one usable contact method."],
      ["Policy / suspension","Direct policy support; owner; effective/version information when available; each material claim traceable."],
      ["Event","Date/time; location or format; official/approved owner; freshness verification."],
      ["Degree requirements","Program/concentration; catalog year; structured requirements; explicit public-rule vs personal-progress boundary."],
    ],[1.45*inch,5.15*inch]))
    story.append(Spacer(1, 10))
    story.append(P("The evidence result is diagnostic", "H2x"))
    story.append(P("It records accepted and rejected evidence, rejection reasons, source-group coverage, field coverage, trust and freshness checks, action-link validation, attempted routes, next permitted route, and whether only a qualified partial answer is safe. One weak admissions chunk can no longer satisfy an employment list query.", "Bodyx"))
    story.append(P("Specialists never bypass this gate. They return records and evidence through one shared envelope; shared validation determines what can be rendered.", "Bodyx"))
    story.append(PageBreak())

    story.append(SectionBand("06 / failure", "Precise, safe, and operationally useful", 6.6*inch))
    story.append(Spacer(1, 10))
    fr=[]
    for code, cfg in failures.items():
        fr.append([code, "yes" if cfg["retry"] else "no", "yes" if cfg["clarification_may_help"] else "no", cfg["user_message"]])
    story.append(table([["Failure class","Retry","Clarify","Safe meaning"]]+fr,[1.7*inch,0.45*inch,0.5*inch,3.95*inch]))
    story.append(Spacer(1, 8))
    story.append(P("Internal traces retain the diagnostic code, routes, source failures, field gaps, and next safe action. User responses never expose stack traces, credentials, private URLs, or raw provider output.", "Bodyx"))
    story.append(PageBreak())

    story.append(SectionBand("07 / observability", "Make every decision answerable", 6.6*inch))
    story.append(Spacer(1, 10))
    story.append(table([
      ["Stage","Trace fields"],
      ["Compile","Original/normalized query; domain/subdomain; intent/action; audience; entities; freshness; risk; confidence; ambiguities; reasons."],
      ["Policy","Allowed/forbidden/skipped channels; machine reason; precedence; concurrency group; fallback trigger."],
      ["Acquire","Source group; source ID; registered/indexed/cache state; fetch outcome; timeout; parse status; latency."],
      ["Validate","Accepted/rejected evidence; rejection reason; field coverage; trust/freshness result; action-link status; conflicts."],
      ["Render","Answer shape; deterministic vs evidence-synthesis mode; claims-to-evidence map; citations emitted; qualification/partial reason."],
    ],[1.0*inch,5.6*inch]))
    story.append(Spacer(1, 12))
    story.append(P("One query correlation ID spans the complete operation. Default production logs remain privacy-aware; deeper fields are gated and redacted. Observability remains best-effort and cannot take down `/ask`.", "Bodyx"))
    story.append(PageBreak())

    story.append(SectionBand("08 / coverage", "Evaluate operations - not prose similarity", 6.6*inch))
    story.append(Spacer(1, 10))
    matrix=[]
    with (ROOT / "docs" / "backend_architecture" / "evaluation_coverage.csv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            matrix.append([row["suite"],row["domain"],row["intent"],row["freshness"],row["risk"],row["expected_route"]])
    story.append(P(f"The initial matrix contains <b>{len(matrix)}</b> cross-domain operation fixtures and expands through paraphrase, misspelling, ambiguity, action-link, failure, security, and latency variants.", "Bodyx"))
    story.append(table([["Suite","Domain","Intent","Fresh","Risk","Expected route"]]+matrix,[0.8*inch,1.15*inch,1.35*inch,0.65*inch,0.5*inch,2.15*inch]))
    story.append(PageBreak())

    story.append(SectionBand("09 / implementation", "Dependency order and rollback boundary", 6.6*inch))
    story.append(Spacer(1, 10))
    steps=[
      ("1","Freeze contracts","Baseline traces, schemas, taxonomies, source groups, route policy, answer shapes, and failure classes."),
      ("2","Load + validate","Versioned configuration with schema checks, fail-closed policy handling, and last-known-good behavior."),
      ("3","Compile + trace","Universal query compiler and policy resolver run before retrieval; legacy path remains available."),
      ("4","Prove shortcuts","Capability discovery derives from runtime configuration with no retrieval or LLM call."),
      ("5","Gate evidence","Shared field/freshness/trust/action checks and precise failures behind a feature flag."),
      ("6","Migrate proofs","Admissions, employment, calendar, catalog, forms, directory, and policy use the shared contracts."),
      ("7","Unify coverage","One governed registry reader plus source/index/freshness manifest before broad backfill."),
      ("8","Expand safely","Add domain packs and specialists only where measured structure or coverage justifies them."),
      ("9","Release on evidence","Replay fixed suites; compare routes, sources, field coverage, citations, action links, security, and latency."),
    ]
    story.append(table([["#","Dependency","Acceptance"]]+steps,[0.35*inch,1.3*inch,4.95*inch]))
    story.append(Spacer(1, 12))
    story.append(P("Rollback", "H2x"))
    story.append(P("The new layer is additive and versioned. `CAMPUS_INTELLIGENCE_ENABLED` controls the compiler/policy/evidence path while preserving the existing API contract and legacy classifier/hybrid route. Disabling the flag restores legacy behavior without deleting registries, manifests, or evaluation evidence.", "Bodyx"))
    story.append(Spacer(1, 7))
    story.append(P("Non-negotiable", "H2x"))
    story.append(P("No dates, deadlines, fees, positions, policies, university facts, or delivery timelines are hardcoded. Domain packs contain routing semantics and source ownership; answers contain validated evidence.", "Bodyx"))
    return story


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=letter, rightMargin=0.45*inch, leftMargin=0.45*inch, topMargin=0.48*inch, bottomMargin=0.38*inch, title="AskMcNeese Campus Intelligence Architecture", author="AskMcNeese engineering")
    doc.build(build_story(), onFirstPage=page_header, onLaterPages=page_header)
    print(OUT)


if __name__ == "__main__":
    main()

