from litestar import Router

from app.routes.auth import AuthController
from app.routes.health import HealthController
from app.routes.tasks import TasksController

api_router = Router(
    path="",
    route_handlers=[HealthController, AuthController, TasksController],
)
