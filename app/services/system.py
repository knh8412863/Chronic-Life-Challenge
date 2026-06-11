from datetime import UTC, datetime

from tortoise import Tortoise

from app.dtos.system import LivenessResponse, ReadinessResponse


class SystemService:
    async def liveness(self) -> LivenessResponse:
        return LivenessResponse(status="ok", timestamp=datetime.now(UTC))

    async def readiness(self) -> ReadinessResponse:
        checks = {"database": "unknown", "redis": "not_configured", "model": "available"}
        try:
            conn = Tortoise.get_connection("default")
            await conn.execute_query("SELECT 1")
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"
        status = "ready" if checks["database"] == "ok" else "not_ready"
        return ReadinessResponse(status=status, checks=checks)
