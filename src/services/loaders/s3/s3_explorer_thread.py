import logging
from datetime import datetime
from queue import Queue, Empty
from threading import Thread, Event

from src.models.s3_batch_item import S3BatchItem
from src.services.batcher.generic_batcher import GenericBatcher
from src.services.loaders.s3.s3_explorer import S3Explorer
from src.utils.generic_logger import logger_setup

logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)


class S3ExplorerThread(Thread):
    """
    No async required here yet:
    1. Upload is the only blocking method
    2. Responsible for sending batches in the queue to S3 (I/O)

    Only required if we are doing uploads in parallel. TBC
    """
    def __init__(
        self, queue: Queue, uploader: S3Explorer, batch_size: int, batch_timeout_s: int
    ) -> None:
        """
        Background thread that batches and uploads to S3
        """
        super().__init__()
        self._queue: Queue = queue
        self._shutdown_event: Event = Event()
        self._uploader: S3Explorer = uploader
        self._batchers: dict[str, GenericBatcher[S3BatchItem]] = {
            "kucoin": GenericBatcher(batch_size, batch_timeout_s),
            "binance": GenericBatcher(batch_size, batch_timeout_s),
        }

    def _flush_batcher(
        self, batcher: GenericBatcher[S3BatchItem], label: str = "", force: bool = False
    ) -> None:
        batch = batcher.get_batch()
        should_flush: bool = (batcher.batch_ready() and batch) or (force and batch)
        if should_flush:
            batch_source: str = batch[0].source
            batch_timestamp: datetime = batch[0].timestamp
            batch_records: list[dict] = [item.data for item in batch]
            try:
                self._uploader.upload_batch(
                    source=batch_source,
                    records=batch_records,
                    timestamp=batch_timestamp,
                )
                print(f"{batch_source} upload to S3 Successful{label}")
            except Exception as e:
                print(f"[S3UploaderThread] Error during upload{label}: {e}")
            batcher.reset_batch()

    def run(self):
        while not self._shutdown_event.is_set():
            try:
                records, timestamp, source = self._queue.get(timeout=1)
                for record in records:
                    self._batchers[source].append(
                        S3BatchItem(data=record, timestamp=timestamp, source=source)
                    )
            except Empty:
                pass
            except Exception as e:
                print(f"[S3UploaderThread] Error during get: {e}")

            for source, batcher in self._batchers.items():
                self._flush_batcher(batcher)

        # Final flush for each source
        print("S3UploaderThread: Running final flush after shutdown event.")
        for source, batcher in self._batchers.items():
            self._flush_batcher(batcher, label=" (final flush)", force=True)

    def stop(self) -> None:
        self._shutdown_event.set()
