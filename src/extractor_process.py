import asyncio
import logging
from typing import Any
import toml

from src.kafka.producers import RawKucoinProducer, RawBinanceProducer
from src.models.kucoin_model import KucoinRawData
from src.services.batcher.batcher_service import GenericBatcher
from src.services.extractors.binance_extractor import (
    BinanceExtractor,
    BinanceExtractorParams,
)
from src.services.extractors.kucoin_extractor import (
    KucoinExtractor,
    KucoinExtractorParams,
)
from src.utils.generic_logger import logger_setup

logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)


BATCH_SIZE: int = 100
BATCH_TIMEOUT: int = 1


class RawExtractorProcess:
    """
    This is a high level orchestrator that deals with:
    1. Calling extract on binance
    2. Calling extract on kucoin
    3. Batcher that batches kucoin
    4. RawKucoinProducer
    5. RawBinanceProducer
    """

    def __init__(
        self,
        producer_config: dict[str, Any],
        batch_size: int = 50,
        batch_timeoust_s: int = 1,
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
            batch_size=batch_size, batch_timeout_s=batch_timeoust_s
        )
        self._kucoin_producer = RawKucoinProducer(
            producer_config=kucoin_formatted_producer_config
        )
        self._binance_producer = RawBinanceProducer(
            producer_config=binance_formatted_producer_config
        )
        self._kucoin_extractor = KucoinExtractor()
        self._binance_extractor = BinanceExtractor()

    async def _run_kucoin_ws(self) -> None:
        async for record in self._kucoin_extractor.extract_async(
            KucoinExtractorParams()
        ):
            self._kucoin_batcher.append(record)
            if self._kucoin_batcher.batch_ready():
                batch: list[KucoinRawData] = self._kucoin_batcher.get_batch()
                self._kucoin_producer.produce(batch)
                self._kucoin_batcher.reset_batch()

    async def _run_binance_ws(self) -> None:
        async for batch in self._binance_extractor.extract_async(
            BinanceExtractorParams()
        ):
            self._binance_producer.produce(batch)

    async def start(self) -> None:
        """
        Starts the Kucoin + Binance extraction pipelines concurrently.
        """
        print("Extractor Process Started")
        await asyncio.gather(
            self._run_kucoin_ws(),
            self._run_binance_ws(),
        )


if __name__ == "__main__":
    try:
        config: dict[str, Any] = toml.load("src/config/config.toml")
        # print("Producer config passed to Kafka:", config)
        extractor_process: RawExtractorProcess = RawExtractorProcess(
            producer_config=config
        )
        asyncio.run(extractor_process.start())
    except KeyboardInterrupt:
        print("Keyboard interrupted")
