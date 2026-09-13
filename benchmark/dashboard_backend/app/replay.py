"""Replay session logic (docs/04-dashboard.md).

A visitor starts a session (POST /api/replay/sessions) then opens an SSE
stream (GET /api/replay/sessions/{id}/stream) that reveals pre-scored rows
at a paced interval, updating a running confusion matrix and
precision/recall/F1 as it goes — this convergence toward the static
benchmark numbers is the demo. Session state (which row a visitor is on,
their running counts) lives only in-memory, keyed by session_id, with no
persistence and no state shared between visitors — matches the "session-
scoped state only" guardrail.
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query
from starlette.responses import StreamingResponse

from .store import store

router = APIRouter(prefix="/api/replay", tags=["replay"])

SESSION_TTL_SECONDS = 3600
MAX_SESSIONS = 500  # bounded resource use — caps total in-memory replay sessions


@dataclass
class ReplaySession:
    dataset: str
    created_at: float = field(default_factory=time.time)


_sessions: Dict[str, ReplaySession] = {}


def _purge_expired():
    now = time.time()
    expired = [sid for sid, s in _sessions.items() if now - s.created_at > SESSION_TTL_SECONDS]
    for sid in expired:
        _sessions.pop(sid, None)


@router.post("/sessions")
def create_session(dataset: str = Query(...)):
    if dataset not in store.available_datasets():
        raise HTTPException(status_code=404, detail=f"Unknown dataset '{dataset}'. Available: {store.available_datasets()}")

    _purge_expired()
    if len(_sessions) >= MAX_SESSIONS:
        raise HTTPException(status_code=503, detail="Too many active replay sessions, try again shortly.")

    session_id = str(uuid.uuid4())
    _sessions[session_id] = ReplaySession(dataset=dataset)
    rows = store.get_replay_rows(dataset)
    return {"session_id": session_id, "dataset": dataset, "n_rows": len(rows)}


def _row_stream(rows: List[dict], interval_seconds: float):
    tp = fp = tn = fn = 0
    for row in rows:
        predicted_attack = row["predicted_label"] == "anomaly"
        actual_attack = row["ground_truth_label"] == "attack"
        if predicted_attack and actual_attack:
            tp += 1
        elif predicted_attack and not actual_attack:
            fp += 1
        elif not predicted_attack and actual_attack:
            fn += 1
        else:
            tn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        payload = {
            "row": row,
            "running": {
                "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "n_seen": tp + fp + tn + fn,
                "n_total": len(rows),
            },
        }
        yield payload


@router.get("/sessions/{session_id}/stream")
async def stream_session(session_id: str, interval_ms: int = Query(300, ge=50, le=5000)):
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown or expired session_id")

    rows = store.get_replay_rows(session.dataset)
    if not rows:
        raise HTTPException(status_code=404, detail="No replay data for this dataset")

    async def event_generator():
        for payload in _row_stream(rows, interval_ms / 1000.0):
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(interval_ms / 1000.0)
        yield f"data: {json.dumps({'done': True})}\n\n"
        _sessions.pop(session_id, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
