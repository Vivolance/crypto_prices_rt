"""
Consumer class which serves 2 usages
1. S3 uploader consumer class which consumes raw binance / kucoin data to be upload as a file to S3
2. Spark consumer class which consumes
"""

import json
from json import JSONDecodeError
from typing import TypeVar, Generic, Any, Type, Optional

from confluent_kafka import Consumer, Message
from pydantic import BaseModel

from src.models.binance_model import BinanceRawData, BinanceTransformedData
from src.models.kucoin_model import KucoinRawData, KucoinTransformedData

ConsumerRecord = TypeVar("ConsumerRecord", bound=BaseModel)


class GenericConsumer(Generic[ConsumerRecord]):
    def __init__(
        self,
        consumer_config: dict[str, Any],
        topic_name: str,
        model: Type[ConsumerRecord],
    ) -> None:
        self._consumer: Consumer = Consumer(consumer_config)
        self._topic_name: str = topic_name
        self._consumer.subscribe([self._topic_name])
        self._model: Type[ConsumerRecord] = model

    def consume(
        self, num_messages: int = 1, timeout: float = 1.0
    ) -> list[ConsumerRecord]:
        """
        Consumes a single Kafka message from topic, expecting JSON array
        """
        messages: list[Message] = self._consumer.consume(
            num_messages=num_messages, timout=timeout
        )
        return self.deserialize_batch(messages)

    def deserialize_batch(self, messages: list[Message]) -> list[ConsumerRecord]:
        batch_messages: list[ConsumerRecord] = []
        for raw_message in messages:
            message_bytes: Optional[str | bytes] = raw_message.value()
            if not isinstance(message_bytes, bytes):
                raise Exception(
                    f"Message is not in bytes: {message_bytes} (returned type: {type(message_bytes)})"
                )

            message_str: str = message_bytes.decode("utf-8")
            try:
                raw_message_list: list[dict[str, Any]] = json.loads(message_str)
            except JSONDecodeError as err:
                print(
                    f"Encountered error : {err} when decoding message on Generic Consumer"
                )
                raise err
            message_list: list[ConsumerRecord] = []
            for single_message_dict in raw_message_list:
                try:
                    single_record: ConsumerRecord = self._model.model_validate(
                        single_message_dict
                    )
                    message_list.append(single_record)
                except Exception as e:
                    print(f"Exception: {e} raised at messages: {single_message_dict}")
                    raise
            batch_messages.extend(message_list)
        return batch_messages

    def commit(self) -> None:
        # manually commit the offsets
        self._consumer.commit()


class KucoinRawConsumer(GenericConsumer[KucoinRawData]):
    def __init__(self, consumer_config: dict[str, Any]) -> None:
        super().__init__(
            consumer_config=consumer_config,
            topic_name="kucoin_raw_data",
            model=KucoinRawData
        )


class BinanceRawConsumer(GenericConsumer[BinanceRawData]):
    def __init__(self, consumer_config: dict[str, Any]) -> None:
        super().__init__(
            consumer_config=consumer_config,
            topic_name="binance_raw_data",
            model=BinanceRawData
        )


class KucoinTransformedConsumer(GenericConsumer[KucoinTransformedData]):
    def __init__(self, consumer_config: dict[str, Any]) -> None:
        super().__init__(
            consumer_config=consumer_config,
            topic_name="kucoin_transformed_data",
            model=KucoinTransformedData
        )


class BinanceTransformedConsumer(GenericConsumer[BinanceTransformedData]):
    def __init__(self, consumer_config: dict[str, Any]) -> None:
        super().__init__(
            consumer_config=consumer_config,
            topic_name="binance_transformed_data",
            model=BinanceTransformedData
        )