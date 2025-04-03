import time
from typing import TypeVar, Generic

SingleMessage = TypeVar("SingleMessage")


class GenericBatcher(Generic[SingleMessage]):
    def __init__(self, batch_size: int = 100, batch_timeout_s: int = 1):
        self._batch_start: float = -1
        self._batch: list[SingleMessage] = []
        self._batch_size: int = batch_size
        self._batch_timeout_s: int = batch_timeout_s

    def append(self, message: SingleMessage) -> None:
        """
        Appends message into a batch, if first message, start timer
        """
        if not self._batch:
            # time counter to measure duration, to be used later in timeout
            self._batch_start = time.perf_counter()
        self._batch.append(message)

    def batch_ready(self) -> bool:
        """
        Check if the batch is ready to be flush and produced
        """
        hit_size: bool = len(self._batch) >= self._batch_size
        hit_timeout: bool = (
            self._batch_start > 0
            and (time.perf_counter() - self._batch_start) >= self._batch_timeout_s
        )
        return hit_size or hit_timeout

    def reset_batch(self) -> None:
        """
        Clears the batch and resets the timer
        """
        self._batch.clear()
        self._batch_start = -1

    def get_batch(self) -> list[SingleMessage]:
        return self._batch
