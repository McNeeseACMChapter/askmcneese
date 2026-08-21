# RCCS Web Mode Wiring — Repair Report

See also: `RCCS_WEB_MODE_WIRING_AUDIT.md`, `docs/pm/sprint3/rccs_implementation_record.md`.

## Root Cause

1. “Can you do web search?” was treated as a campus RAG question; Claude denied capability from empty evidence.
2. RCCS env flags were not persisted for local/dev.
3. Frontend lacked capability-aware Web toggle and mode-specific status copy.

The Sources toggle itself already sent `use_web_search` correctly.

## End-to-End Request Contract

```ts
{ question, stream: true, use_web_search: sourceScope === "web" }
```

Backend: `AskRequest.use_web_search: bool`.

## Runtime Configuration (active local)

```
RCCS_ENABLED=1
RCCS_HYBRID_ENABLED=1
RCCS_COMPANIONS_ENABLED=0
RCCS_RMP_ENABLED=0
RCCS_SOCIAL_LINKS_ENABLED=0
```

## Browser / API Proof (2026-07-12)

| Mode | Payload | Effective | Channels | web_search_executed |
|------|---------|-----------|----------|---------------------|
| Knowledge | `use_web_search=false` | knowledge | kb | false |
| Web | `use_web_search=true` | official_web | kb,official_live | true |
| Capability | web selected | capability | [] | false (short-circuit Yes) |

## Tests

- `python -m unittest discover -s tests/unit -v` → 59 OK  
- `npm run test -- --run src/web-mode-wiring.test.tsx` → 4 OK  

## Servers

- Backend http://127.0.0.1:8001  
- Frontend http://127.0.0.1:5173  
