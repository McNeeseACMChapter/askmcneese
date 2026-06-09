# AskMcNeese

**Built by McNeese ACM**

AskMcNeese is a campus-assistant project designed to help students find trusted public McNeese information through a structured retrieval workflow.

The long-term goal is to support students with reliable, source-grounded answers about campus resources, events, forms, deadlines, and general university information.

---

## Project Status

This repository is currently in **Sprint 1: Foundation**.

Sprint 1 is focused on building the project base layer, not the final assistant experience. At this stage, the team is establishing:

* repository structure
* backend health check
* frontend shell
* source approval workflow
* retrieval pipeline proof
* QA review process

This repository should be understood as an **early-stage foundation project**.

It is **not yet a production-ready chatbot**, and it does **not yet claim to answer live student questions**.

---

## Why This Project Exists

Students often need quick access to public campus information, but important details are spread across many pages, departments, and update cycles.

AskMcNeese is intended to reduce that friction by organizing trusted university information into a retrieval-ready system that can later support a safe and useful assistant experience.

The emphasis of this project is not just convenience. It is also correctness.

The project is designed to:

* use approved public sources
* avoid private or restricted data
* preserve traceable source metadata
* support future citation, freshness checks, and review workflows

---

## Sprint 1 Objective

The purpose of Sprint 1 is to make the project real enough for every role to start working from the same foundation.

By the end of this sprint, the team should have:

* a clear repository structure
* a FastAPI `GET /health` endpoint
* a React + Tailwind frontend shell connected to that endpoint
* a source registry of approved public McNeese URLs
* a crawler → cleaner → chunker proof for approved pages
* a local ChromaDB ingest proof
* QA smoke tests and sprint review evidence

Sprint 1 is about **foundation, alignment, and proof of workflow**.

---

## What Sprint 1 Includes

### Foundation Setup

* repository organization
* branch workflow
* local setup documentation
* environment variable template

### Backend Foundation

* FastAPI bootstrap
* `GET /health` endpoint
* basic backend structure for future services

### Frontend Foundation

* React + Vite application shell
* Tailwind CSS setup
* mobile-first AskMcNeese chat interface mock shell
* backend health status display

### Retrieval Pipeline Proof

* approved-source input file
* public-page fetch proof
* clean text extraction proof
* chunk generation proof
* local ChromaDB ingest proof

### QA and Project Control

* setup validation
* PR checklist
* smoke tests
* sprint review notes and evidence

---

## What Sprint 1 Does Not Include

The following items are intentionally out of scope for this sprint:

* Canvas integration
* Microsoft SSO
* LLM answer generation
* full-site crawling
* production deployment
* private student data
* login-only or authenticated sources

These are excluded on purpose so the team can first establish a clean, safe, testable base.

---

## Planned Repository Structure

The target structure for Sprint 1 is:

```text
askmcneese/
├── backend/
├── crawler/
├── docs/
├── frontend/
├── knowledge/
├── scripts/
└── tests/
```

This layout separates application code, retrieval work, knowledge inputs, project documentation, and test artifacts so each role can work without confusion.

---

## Planned Technology Direction

The current Sprint 1 plan uses the following stack:

| Area             | Technology                           |
| ---------------- | ------------------------------------ |
| Backend          | FastAPI                              |
| Frontend         | React + Vite + Tailwind CSS          |
| Pipeline tooling | Python crawler, cleaner, and chunker |
| Vector storage   | Local ChromaDB                       |

This is the working direction for the foundation sprint. It should not be described as final production architecture until the implementation is in place and validated.

---

## Team Workstreams

### PM / Full-Stack

* create and maintain repository structure
* define branch and review workflow
* bootstrap backend health endpoint
* draft initial data model
* provide setup and environment documentation

### Backend

* fetch approved public pages only
* clean extracted text
* split content into retrieval-ready chunks
* attach required metadata
* prove local ChromaDB ingest

### Frontend

* build the AskMcNeese shell
* support empty, loading, and error states
* connect to backend `/health`
* keep the first version mobile-first and readable

### Content / Knowledge

* create the approved source registry
* identify initial public McNeese URLs
* assign categories and trust tiers
* prepare starter test questions

### DevOps / QA

* validate setup from a fresh clone
* define PR checklist
* create smoke tests
* collect review evidence and status notes

---

## Branch Strategy

The intended branch workflow for this project is:

| Branch      | Purpose                    |
| ----------- | -------------------------- |
| `main`      | stable reviewed milestones |
| `dev`       | active integration         |
| `feature/*` | focused task work          |

Example branch names:

```text
feature/backend-health
feature/frontend-chat-shell
feature/content-source-registry
feature/chromadb-ingest
```

---

## Data and Safety Rules

This project follows a strict Week 1 boundary:

* only approved public McNeese URLs may be processed
* no private, student-record, or authenticated content may be used
* no unapproved source should be treated as trusted
* no fake institutional answers should be presented as real answers
* every retrieval chunk should keep enough metadata for future citation and freshness review

These rules are part of the foundation, not optional cleanup work for later.

---

## Definition of Done for Sprint 1

Sprint 1 is complete when:

* the repository structure is in place
* the backend `/health` endpoint runs locally
* the frontend can display backend health status
* the approved source registry exists
* the crawler, cleaner, and chunker proof exists for approved sources
* local ChromaDB ingest is demonstrated
* QA smoke tests and sprint review proof are documented

If those conditions are not met, the project should still be treated as in-progress foundation work.

---

## Current README Scope

This README is intentionally written as a project foundation document.

It explains:

* what AskMcNeese is supposed to become
* what Sprint 1 is trying to establish
* what work is in scope right now
* what technical and governance boundaries the team is following

It does not claim that the full assistant already works.

---

## Immediate Next Steps

1. Create the target folder structure.
2. Add backend FastAPI bootstrap with `GET /health`.
3. Scaffold the frontend chat shell.
4. Create the approved source registry under `knowledge/`.
5. Add crawler, cleaner, chunker, and ingest proof files.
6. Add QA checklists and sprint review documentation.

---

## Attribution

AskMcNeese is built by the **McNeese ACM Student Chapter** as a student-led software project focused on trusted campus information access.
