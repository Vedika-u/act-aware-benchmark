"""Minimal per-IP sliding-window rate limiter (docs/04-dashboard.md's
guardrail: "Rate limiting per IP/session on the replay-control endpoints").

In-memory only — fine for the small single-instance deployment this
dashboard runs on (docs/04-dashboard.md's hosting section); it resets on
restart and is not shared across instances, which is an acceptable trade-off
for a low-traffic portfolio demo, not a production multi-tenant API.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limited_prefixes=("/api/replay",), max_requests=30, window_seconds=60):
        super().__init__(app)
        self.limited_prefixes = limited_prefixes
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in self.limited_prefixes):
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            hits = self._hits[client_ip]
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()
            if len(hits) >= self.max_requests:
                raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
            hits.append(now)
        return await call_next(request)
