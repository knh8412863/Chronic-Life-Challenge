import asyncio
import signal

from tortoise import Tortoise

from ai_worker.core import default_logger
from app.core.db.databases import TORTOISE_ORM
from app.models.predictions import PredictionStatus, PredictionTask
from app.services.predictions import PredictionService

POLL_INTERVAL_SECONDS = 3


class PredictionWorker:
    def __init__(self, service: PredictionService | None = None) -> None:
        self.service = service or PredictionService()

    async def process_once(self) -> bool:
        task = (
            await PredictionTask.filter(status=PredictionStatus.PENDING)
            .order_by("requested_at", "id")
            .only("id", "task_uuid", "user_id")
            .first()
        )
        if task is None:
            return False

        default_logger.info("prediction task picked: task_uuid=%s user_id=%s", task.task_uuid, task.user_id)
        await self.service.process_task(task.task_uuid, task.user_id)
        default_logger.info("prediction task processed: task_uuid=%s", task.task_uuid)
        return True

    async def run_forever(self, stop_event: asyncio.Event) -> None:
        default_logger.info("ai worker started")
        while not stop_event.is_set():
            try:
                processed = await self.process_once()
                if not processed:
                    await asyncio.wait_for(stop_event.wait(), timeout=POLL_INTERVAL_SECONDS)
            except TimeoutError:
                continue
            except Exception:
                default_logger.exception("ai worker loop failed")
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
        default_logger.info("ai worker stopped")


async def main() -> None:
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    await Tortoise.init(config=TORTOISE_ORM)
    try:
        await PredictionWorker().run_forever(stop_event)
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
