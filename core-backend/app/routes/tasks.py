from litestar import Controller, post
from litestar_saq import TaskQueues

from app.tasks import sample_task


class TasksController(Controller):
    path = "/tasks"
    tags = ["Tasks"]

    @post("/sample")
    async def enqueue_sample(self, task_queues: TaskQueues) -> dict[str, str | None]:
        queue = task_queues.get("default")
        job = await queue.enqueue(sample_task.__name__, message="hello from api")
        return {"job_id": getattr(job, "id", None), "status": "queued"}
