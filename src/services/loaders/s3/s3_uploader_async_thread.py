import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from src.services.loaders.s3.s3_explorer import S3Explorer
from src.utils.generic_logger import logger_setup

"""
NOT USED, FOR PRACTICE AND REFERENCE

This is alternative way to spin up background uploading to S3, buy using asyncio native library to spin up background tasks
using asyncio.create_task() and run_in_executor()
"""

logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)


class RawS3UploaderThreaded:
    def __init__(self, uploader: S3Explorer) -> None:
        self.uploader = uploader
        self.queue: asyncio.Queue = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        # do not wait as this is a background task to be created
        consume = asyncio.create_task(self._consume())
        await consume

    async def _consume(self):
        while not self._shutdown_event.is_set():
            try:
                item = await self.queue.get()

                # Unpack for logging
                source = item["source"]
                timestamp = item["timestamp"]

                # Run this in a separate thread to prevent blocking the event loop by using run_in_executor()
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, lambda: self.uploader.upload_batch(**item)
                )
                print(f"S3 Upload Successful for {source} at {timestamp}")
            except Exception as e:
                print(f"Background S3 Uploader Error: {e}")
                raise e

    def submit_upload(self, source: str, records: list[dict], timestamp: datetime):
        self.queue.put_nowait(
            {
                "source": source,
                "records": records,
                "timestamp": timestamp,
            }
        )

    async def stop(self) -> None:
        self._shutdown_event.set()
        self.executor.shutdown(wait=True)
