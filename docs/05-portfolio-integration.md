# Portfolio Integration

## Current state (as of this writing)

The Act Aware entry lives entirely in one file in the portfolio repo:
`Vedika Portfolio/src/data/content.ts`, lines 48-83 (project entry, slug `act-aware`),
plus shorter mentions at lines 214, 241 (achievements/milestones) and 291-303
(`githubRepos` descriptions for `hack_o_hire` and `aware-security-hub`).

Current description is entirely qualitative: architecture/tech-stack summary, no
performance numbers, no links beyond the two GitHub repos, no live demo.

## What changes when this project finishes

In `content.ts`'s Act Aware entry:
- Add real metrics (precision/recall/F1, per-category recall caveat for R2L/U2R) from
  [03-eval-harness.md](03-eval-harness.md)'s output — a short "Benchmarked against
  NSL-KDD/CICIDS2017" line with the headline numbers, not a full metrics dump (the
  dashboard is where full detail lives).
- Add a link to the hosted live-replay dashboard
  ([04-dashboard.md](04-dashboard.md)).
- Keep the existing architecture/tech-stack description largely as-is — this project
  adds evidence on top of the existing description, it doesn't replace the story of
  what Act Aware is.
- Consider whether the achievements/milestones lines (214, 241) should also gain a
  short mention of the benchmark work, separate from the original hackathon
  achievement.

## What does not change

- The two existing GitHub repo links stay (backend/frontend source).
- `src/components/diagrams/index.tsx`'s `ActAwareFlow`/`ActAwareDiagram` components —
  these describe the production log-ingestion pipeline, which this benchmark doesn't
  modify. No changes needed here unless a diagram of the benchmark/dashboard itself is
  later wanted as a separate visual.

## Status

Not started — this is the last phase, done once real numbers and a live dashboard
exist to link to. Do not add placeholder/estimated numbers to the portfolio before the
benchmark actually produces them.
