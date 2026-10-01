# Backend

FastAPI + SQLite. One folder per pipeline step under `app/domains/`, each with
its router, schemas and logic:

| Domain | Step | What it owns |
|---|---|---|
| `intake` | 1–2 | The five-axis question spine (`spec.py`), adaptive follow-ups (`followups.py`), free-text mapping |
| `vision` | 3 | Runs `vision/detect` on a photo, the quality gate, signals, magnitude, suggested signature |
| `causes` | 4 | The cause vocabulary (`golden/causes.json`) and evidence for/against |
| `ranking` | 5 | Pass 1 rules (`rules.py`, each citing its source), the LLM critic, Gates A and B, T1–T4 |
| `retrieval` | 2b, 5b | Coarse matching on answers, fine matching on signals, the precedent tally |
| `checks` | 6 | The troubleshooting loop and suggested checks |
| `report` | 7 | The report, the written explanation, re-measurement (`verify.py`) |
| `cases` | 8 | The case record, who writes which half of the fingerprint, the close rule (`close.py`) |

```bash
uv run python -m app.reset_demo               # rebuild the demo database, offline
uv run uvicorn app.main:app --port 8001       # API docs at http://localhost:8001/docs
uv run pytest                                 # 52 tests, offline
uv run python -m app.seed_demo_case           # integration test against the running API
```

Configuration comes from the environment or `.env` in this folder (see
`.env.example`): `GROQ_API_KEY` turns on the optional LLM steps, and
`LLM_ENABLED=false` turns them off again without removing the key.

Two invariants the tests pin down, because the close rule rests on them:

- **The measured half of a fingerprint belongs to the photo.** Signals are written only
  by `POST /cases/{id}/vision`, and the latest photo replaces them wholesale. A client
  saving answers can't overwrite them.
- **Close-record fields are written only by the step endpoints.** Rank, check-results,
  verify and close are the only writers. `PATCH /cases/{id}` refuses `tier`,
  `diagnosis`, `verification`, `ranking` and the rest with a 422.
