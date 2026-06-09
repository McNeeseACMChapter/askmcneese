# Frontend — AskMcNeese (Sprint 1)

> Owner: **Frontend teammate**
> Status: **Not implemented yet — left intentionally for the Frontend role.**

This folder is reserved for the React + Vite + Tailwind CSS application shell.

## Sprint 1 deliverables for this folder

Per `README.md` and the Sprint 1 plan, the Frontend role is responsible for:

1. Scaffolding a Vite + React app.
2. Adding Tailwind CSS.
3. Building a **mobile-first** AskMcNeese chat shell.
4. Handling empty, loading, and error states.
5. Pinging the backend `GET /health` endpoint and displaying its status.

## Suggested starting structure (not yet created)

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   └── ChatShell.tsx
│   ├── hooks/
│   │   └── useHealth.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css           # Tailwind directives
├── index.html
├── package.json
├── tailwind.config.js
├── postcss.config.js
├── vite.config.ts
└── README.md               # (this file)
```

## Notes

- Keep the first version **mobile-first** and readable — it does not need to be a full chatbot UI yet.
- Read the backend URL from an environment variable (`VITE_BACKEND_URL`) — see `.env.example` at the repo root once added.
- Do not embed answer-generation logic in Sprint 1; this is just a shell.

---

*This README is a placeholder so the folder exists in git and the Frontend teammate has a clear starting point.*
