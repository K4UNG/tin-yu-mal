from litestar import Controller, get
from litestar.status_codes import HTTP_200_OK


class HealthController(Controller):
    path = "/health"
    tags = ["Health"]

    @get("/", status_code=HTTP_200_OK)
    async def health(self) -> dict[str, str]:
        return {"status": "ok"}
