# Dashboard frontend

React/Vite dashboard for the Act Aware detection benchmark (docs/04-dashboard.md).
Reuses the visual theme (colors, fonts, glass-card styling) from
`../../frontend` (aware-security-hub) for continuity with Act Aware's
existing SOC dashboard aesthetic, without modifying that repo.

## Run locally

```bash
cd benchmark/dashboard_frontend
bun install
cp .env.example .env.local   # VITE_API_BASE, defaults to http://localhost:8000
bun dev
```

Requires the backend running locally (see `../dashboard_backend/README.md`).

## Deploy (Vercel)

`vercel.json` is set up for a static Vite build. Set the `VITE_API_BASE`
environment variable in the Vercel project to the deployed backend's URL
before building.
