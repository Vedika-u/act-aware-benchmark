# Project instructions for Claude Code

This repo is a portfolio piece: a hackathon SIEM-SOAR platform (`backend/`,
`frontend/` — reference only, untouched, not tracked in this repo's git
history) being independently benchmarked (`benchmark/`) against public
intrusion-detection datasets. See `README.md` and `docs/00-overview.md` for
the full framing before making changes.

## Mandatory: keep docs and README in sync with code

Follow `CONTRIBUTING.md`'s table exactly: any change to `benchmark/src/`,
`benchmark/dashboard_backend/`, `benchmark/dashboard_frontend/`, dataset
handling, setup/run steps, dependencies, or headline results **must** update
the matching file in `docs/` and/or the root `README.md`'s "Results" /
"Status" sections in the same change — never as a separate follow-up task.
Before ending a turn that touched any of those areas, check whether
`README.md` or a `docs/*.md` file now describes something that is no longer
true, and fix it.

## Never report numbers that don't exist yet

Don't add placeholder, estimated, or "should be around X" metrics anywhere.
A dataset's status stays `🚧 pending` in the README until
`benchmark/results/{dataset}.json` actually contains the real, computed
number from `python run_benchmarks.py`.

## Secrets

`backend/.env` has been redacted (it previously contained a real
Elasticsearch host/password and Ollama host — see `backend/.env.example`
for the variable names). Never reintroduce real credentials into a tracked
file; if real infra is needed for local testing, use a local `.env` that
stays gitignored.
