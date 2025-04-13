import asyncio
import json
from typing import Generic, TypeVar, Optional, Any

from confluent_kafka import Producer, KafkaError, Message
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from src.services.extractors.binance_extractor import (
    BinanceExtractor,
    BinanceExtractorParams,
)


class FailedToProduceError(Exception):
    pass


ProduceMessage = TypeVar("ProduceMessage", bound=BaseModel)


class AbstractProducer(Generic[ProduceMessage]):
    def __init__(self, producer_config: dict[str, str], topic_name: str) -> None:
        self._producer: Producer = Producer(producer_config)
        self._topic_name: str = topic_name

    @retry(
        retry=retry_if_exception_type(FailedToProduceError),
        stop=stop_after_attempt(5),
        wait=wait_fixed(0.01),
        reraise=True,
    )
    def produce(self, batch: list[ProduceMessage]) -> None:
        """
        Takes in a list[dataclass], serialize it and produce
        """
        if not isinstance(batch, list):
            raise ValueError("Expected a list of BaseModels")
        # all messages to be produced must be serialized
        # model.dumps(list[dataclass] -> list[dict])
        # json.dumps (list[dict] -> str), each str json array is a type list[dict]
        serialized_batch: str = json.dumps(
            [single_item.model_dump() for single_item in batch]
        )
        self._producer.produce(
            topic=self._topic_name, value=serialized_batch, on_delivery=self.log_error
        )
        self._producer.flush()

    @staticmethod
    def log_error(err: Optional[KafkaError], msg: Message) -> None:
        """
        :param err: The KafkaError to log
        :param msg: Message you produced that failed
        :return:
        """
        if err is not None:
            # Raise Error
            print(f"Delivery failed for message: {err}")
        else:
            # Optional
            print(
                f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
            )


class RawBinanceProducer(AbstractProducer["BinanceRawData"]):
    def __init__(self, producer_config: dict[str, str]) -> None:
        super().__init__(producer_config=producer_config, topic_name="binance_raw_data")


class RawKucoinProducer(AbstractProducer["KucoinRawData"]):
    def __init__(self, producer_config: dict[str, str]) -> None:
        super().__init__(producer_config=producer_config, topic_name="kucoin_raw_data")


class TransformedBinanceProducer(AbstractProducer["BinanceTransformedData"]):
    def __init__(self, producer_config: dict[str, str]) -> None:
        super().__init__(
            producer_config=producer_config, topic_name="binance_transformed_data"
        )


class TransformedKucoinProducer(AbstractProducer["KucoinTransformedData"]):
    def __init__(self, producer_config: dict[str, str]) -> None:
        super().__init__(
            producer_config=producer_config, topic_name="kucoin_transformed_data"
        )


# Test run for Binance extractor and producer
async def main() -> None:
    extractor: BinanceExtractor = BinanceExtractor()
    producer_config: dict[str, Any] = {
        "bootstrap.servers": "localhost:9092",
        "acks": "all",
        "compression.type": "gzip",
    }
    params: BinanceExtractorParams = BinanceExtractorParams()
    producer: RawBinanceProducer = RawBinanceProducer(producer_config)
    async for event in extractor.extract_async(params):
        producer.produce(event)


if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(main())
