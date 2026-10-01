# Frontend

Next.js (App Router) + Tailwind + shadcn/ui. Every page is a client component
talking to the backend through `lib/api/`.

```bash
pnpm install --frozen-lockfile
pnpm build && pnpm exec next start -H 0.0.0.0 -p 3001   # what the demo runs
pnpm dev --port 3001                                    # while developing
```

The browser calls `/api` on this server, and `next.config.ts` forwards it to the
backend (`API_PROXY_TARGET`, default `http://127.0.0.1:8001`). So the backend
can stay on localhost while a phone on the same network uses the app.

Photos are shrunk to 1600 px on the long side in the browser before upload
(`lib/photo.ts`). The backend lines the recipe up with the photo at any scale,
so measurement is unaffected.

| Path | |
|---|---|
| `/` | Line status, proven vs unproven fixes, cases waiting for an engineer |
| `/troubleshoot` | Open a case |
| `/troubleshoot/[id]` | The wizard — chat on the left, live artifacts on the right |
| `/cases`, `/cases/[id]` | Case history and detail, with the engineer review panel |
| `/cases/[id]/report` | The printable report |
| `/catalog`, `/profiles` | Stations, materials and dispense profiles |

Rule citations are shown through `lib/sources.ts`, which expands "matc82 sec 3.5
p.18-19" to "NPL guide §3.5, p.18–19" and names the sources wherever they're cited.
