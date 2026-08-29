"""Background tasks for SAQ workers."""

from __future__ import annotations


async def sample_task(ctx: dict, *, message: str = "ping") -> str:
    # ponytail: ctx is the SAQ job context; name used for enqueue is the function __name__
    return f"done: {message}"
