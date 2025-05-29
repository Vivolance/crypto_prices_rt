import asyncio
import logging
from datetime import datetime
from queue import Queue
from typing import Any
import toml
from dotenv import load_dotenv

from src.kafka.producers import RawKucoinProducer, RawBinanceProducer
from src.models.kucoin_model import KucoinRawData
from src.services.batcher.generic_batcher import GenericBatcher
from src.services.extractors.binance_extractor import (
    BinanceExtractor,
    BinanceExtractorParams,
)
from src.services.extractors.kucoin_extractor import (
    KucoinExtractor,
    KucoinExtractorParams,
)
from src.services.loaders.s3_explorer import S3Explorer
from src.services.loaders.s3_explorer_thread import S3ExplorerThread
from src.utils.generic_logger import logger_setup

logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)


class RawExtractorProcess:
    """
    This is a high level orchestrator that is responsible for:
    1. Calling extract on binance
    2. Calling extract on kucoin
    3. Batcher that batches kucoin
    4. Producing by RawKucoinProducer
    5. Producing by RawBinanceProducer
    6. Spinning up S3Uploader as background thread
    """

    def __init__(
        self,
        producer_config: dict[str, Any],
    ) -> None:
        kucoin_kafka_config = producer_config["kafka"]["producer"]["kucoin_raw"]
        binance_kafka_config = producer_config["kafka"]["producer"]["binance_raw"]
        kucoin_formatted_producer_config: dict[str, Any] = {
            key.replace("_", "."): value for key, value in kucoin_kafka_config.items()
        }
        binance_formatted_producer_config: dict[str, Any] = {
            key.replace("_", "."): value for key, value in binance_kafka_config.items()
        }
        self._kucoin_batcher = GenericBatcher[KucoinRawData](
            batch_size=50, batch_timeout_s=1
        )
        self._kucoin_producer = RawKucoinProducer(
            producer_config=kucoin_formatted_producer_config
        )
        self._binance_producer = RawBinanceProducer(
            producer_config=binance_formatted_producer_config
        )
        self._kucoin_extractor = KucoinExtractor()
        self._binance_extractor = BinanceExtractor()
        self._s3_queue = Queue()
        self._s3_uploader_thread = S3ExplorerThread(
            queue=self._s3_queue,
            uploader=S3Explorer(),
            batch_size=99999999,
            batch_timeout_s=60,
        )

    async def _run_kucoin_ws(self) -> None:
        try:
            async for record in self._kucoin_extractor.extract_async(
                KucoinExtractorParams()
            ):
                try:
                    self._kucoin_batcher.append(record)
                    if self._kucoin_batcher.batch_ready():
                        batch: list[KucoinRawData] = self._kucoin_batcher.get_batch()
                        self._kucoin_producer.produce(batch)
                        self._s3_queue.put(
                            (
                                [record.model_dump() for record in batch],
                                datetime.utcnow(),
                                "kucoin",
                            )
                        )
                        self._kucoin_batcher.reset_batch()
                except Exception as e:
                    print(f"[Kucoin] ERROR (inner): {e}")
            print("[Kucoin] extraction loop exited.")
        except Exception as e:
            print(f"[Kucoin] ERROR (outer): {e}")

    async def _run_binance_ws(self) -> None:
        async for records in self._binance_extractor.extract_async(
            BinanceExtractorParams()
        ):
            self._binance_producer.produce(records)

            # Enqueue batch for S3 Upload
            batch = [record.model_dump() for record in records]
            self._s3_queue.put((batch, datetime.utcnow(), "binance"))

    async def start(self) -> None:
        """
        Starts the Kucoin + Binance extraction pipelines concurrently.
        """
        print("Extractor Process Started")
        self._s3_uploader_thread.start()
        try:
            # Start Extraction
            await asyncio.gather(
                self._run_kucoin_ws(),
                self._run_binance_ws(),
            )
        finally:
            self._s3_uploader_thread.stop()
            self._s3_uploader_thread.join()
            print("Extractor Process Stopped and S3UploaderThread joined.")


if __name__ == "__main__":
    load_dotenv()
    try:
        config: dict[str, Any] = toml.load("src/config/config.toml")
        # print("Producer config passed to Kafka:", config)
        extractor_process: RawExtractorProcess = RawExtractorProcess(
            producer_config=config
        )
        asyncio.run(extractor_process.start())
    except KeyboardInterrupt:
        print("Keyboard interrupted")
