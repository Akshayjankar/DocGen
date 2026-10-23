from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.jobs import job_store

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    data = job.to_public()
    data["structured_by"] = job.meta.get("structured_by")
    data["diffs"] = job.diffs
    data["lint"] = job.lint
    return data


@router.get("/{job_id}/events")
async def job_events(job_id: str) -> StreamingResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    queue = job_store.subscribe(job)

    async def gen():
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                except TimeoutError:
                    yield "event: ping\ndata: {}\n\n"
                    continue
                # Default `message` event (EventSource.onmessage) + named `progress`
                yield f"data: {payload}\n\n"
                yield f"event: progress\ndata: {payload}\n\n"
                if '"status": "done"' in payload or '"status": "failed"' in payload:
                    break
        finally:
            if queue in job.subscribers:
                job.subscribers.remove(queue)

    return StreamingResponse(gen(), media_type="text/event-stream")
