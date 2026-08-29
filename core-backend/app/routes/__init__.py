from litestar import Router

from app.routes.auth import AuthController
from app.routes.courses import CoursesController
from app.routes.health import HealthController
from app.routes.tasks import TasksController
from app.routes.uploads import UploadsController

api_router = Router(
    path="",
    route_handlers=[
        HealthController,
        AuthController,
        TasksController,
        CoursesController,
        UploadsController,
    ],
)
