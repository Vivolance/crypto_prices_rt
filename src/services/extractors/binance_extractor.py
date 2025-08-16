import json
import logging
import os
import threading
from typing import AsyncGenerator, Any

import aiohttp
import asyncio
from aiohttp import ClientWebSocketResponse, WSMessage
from pydantic import BaseModel
from tenacity import retry, wait_fixed, stop_after_attempt

from src.common.generic_extractor import AsyncExtractor
from src.models.binance_model import BinanceRawData
from src.utils.generic_logger import logger_setup

logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)


class BinanceExtractorParams(BaseModel):
    pass


class BinanceExtractor(AsyncExtractor[BinanceExtractorParams, BinanceRawData]):
    def __init__(self):
        # 1. threading.Event() because we want external threads to trigger stop, not from within the async loop
        # 2. To allow the thread to stop gracefully, finishing thoroughly and cleaning up all resources before stopping
        self.stop_event: threading.Event = threading.Event()

    # External callable for tests to stop the session
    def request_stop(self):
        self.stop_event.set()

    @retry(
        wait=wait_fixed(0.01),  # ~10ms between attempts
        stop=stop_after_attempt(5),  # 5 retries
        reraise=True,
    )
    async def extract_async(
        self,
        binance_extractor_params: BinanceExtractorParams,
    ) -> AsyncGenerator[list[BinanceRawData], None]:
        connection_string: str = os.getenv("BINANCE_CONNECTION")
        while not self.stop_event.is_set():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(connection_string) as ws:
                        ws: ClientWebSocketResponse
                        async for msg in ws:
                            if self.stop_event.is_set():
                                print("Stop event received — breaking WebSocket loop.")
                                break
                            msg: WSMessage
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                msg_string: str = msg.data
                                # Deserialize from json to list[dict]
                                msg_dict: list[dict[str, Any]] = json.loads(msg_string)
                                # Deserialize from list[dict] into list[BinanceRawData], Validation step
                                binance_ticker_list = [
                                    BinanceRawData.model_validate(item)
                                    for item in msg_dict
                                ]
                                yield binance_ticker_list
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                raise ValueError(
                                    "WebSocket connection closed unexpectedly"
                                )
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                raise ValueError("WebSocket encountered error")
                print("WARNING: WebSocket session ended, will retry after short delay.")
                await asyncio.sleep(1)
            except aiohttp.ClientError as e:
                raise Exception(f"Client error occurred: {e}") from e
            except Exception as e:
                raise Exception(f"Unexpected error occurred {e}")


async def main() -> None:
    binance_extractor_params: BinanceExtractorParams = BinanceExtractorParams()
    async for event in BinanceExtractor.extract_async(binance_extractor_params):
        print(event)


if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(main())
