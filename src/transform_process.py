import logging
from typing import Any

from src.kafka.consumers import KucoinRawConsumer, BinanceRawConsumer
from src.utils.generic_logger import logger_setup


logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)


class TransformerProcess:
    """
    High level orchestrator for consuming raw data from raw topic and transforming them:
    1. Consume from binance_raw_data and kucoin_raw_data topics
    2. Deserialize them to list[dict] using json_loads
    3. Call transform_kucoin and transform binance from transformer class
    4. Serialize list[KucoinTransformedData] and list[BinanceTransformedData]
    5. Produce to binance_transformed_data and kucoin_transformed_data topics
    """

    def __init__(self, consumer_config: dict[str, Any]) -> None:
        kucoin_consumer_config: dict[str, str] = consumer_config["kafka"]["consumer"][
            "kucoin_raw"
        ]
        binance_consumer_config: dict[str, str] = consumer_config["kafka"]["consumer"][
            "binance_raw"
        ]
        self.kucoin_consumer = KucoinRawConsumer(kucoin_consumer_config)
        self.binance_consumer = BinanceRawConsumer(binance_consumer_config)
