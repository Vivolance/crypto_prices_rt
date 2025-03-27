import json
import logging
from typing import AsyncGenerator, Any

import aiohttp
import asyncio
from aiohttp import ClientWebSocketResponse, WSMessage
from pydantic import BaseModel
from tenacity import retry, wait_fixed, stop_after_attempt

from src.common.generic_extractor import AsyncExtractor
from src.models.binance_model import BinanceCryptoData
from src.utils.generic_logger import logger_setup

logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)


class BinanceExtractorParams(BaseModel):
    pass


class BinanceExtractor(AsyncExtractor[BinanceExtractorParams, BinanceCryptoData]):
    @staticmethod
    @retry(
        wait=wait_fixed(0.01),  # ~10ms between attempts
        stop=stop_after_attempt(5),  # 5 retries
        reraise=True,
    )
    async def extract_async(
        extractor_params: BinanceExtractorParams,
    ) -> AsyncGenerator[list[BinanceCryptoData], None]:
        connection_string: str = "wss://stream.binance.com:9443/ws/!miniTicker@arr"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(connection_string) as ws:
                    ws: ClientWebSocketResponse
                    async for msg in ws:
                        msg: WSMessage
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            msg_string: str = msg.data
                            # Deserialize from json to list[dict]
                            msg_dict: list[dict[str, Any]] = json.loads(msg_string)
                            # Deserialize from list[dict] into list[BinanceCryptoData], Validation step
                            binance_ticker_list = [BinanceCryptoData.parse_obj(item) for item in msg_dict]
                            yield binance_ticker_list
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            raise ValueError("WebSocket connection closed unexpectedly")
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            raise ValueError("WebSocket encountered error")
        except aiohttp.ClientSession as e:
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
