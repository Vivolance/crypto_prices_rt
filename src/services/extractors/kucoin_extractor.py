import json
import logging
import threading
import os
from typing import AsyncGenerator, Any

import aiohttp
import asyncio
from aiohttp import WSMessage
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed

from src.common.generic_extractor import AsyncExtractor
from src.models.kucoin_model import KucoinRawData
from src.utils.generic_logger import logger_setup

"""
Sample Response message:

{'id': 'zmlD9FsJJw', 'type': 'welcome'} # Welcome message
{'id': '1', 'type': 'ack'}              # Welcome messages
{'topic': '/market/ticker:all', 'type': 'message', 'subject': 'CKB-USDT', 'data': {'bestAsk': '0.005651', 'bestAskSize': '20700', 'bestBid': '0.00565', 'bestBidSize': '20700', 'price': '0.005648', 'sequence': '1058128692', 'size': '4664.89', 'time': 1743064920774}}
{'topic': '/market/ticker:all', 'type': 'message', 'subject': 'AVAX3L-USDT', 'data': {'bestAsk': '0.00713865', 'bestAskSize': '4574.6298', 'bestBid': '0.00707098', 'bestBidSize': '1463.0438', 'price': '0.00710735', 'sequence': '433799932', 'size': '13593.3459', 'time': 1743063437192}}
{'topic': '/market/ticker:all', 'type': 'message', 'subject': 'ADA-USDC', 'data': {'bestAsk': '0.741', 'bestAskSize': '459', 'bestBid': '0.7406', 'bestBidSize': '229.5', 'price': '0.7413', 'sequence': '1163816212', 'size': '55.71', 'time': 1743064848551}}
"""


logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)


class KucoinExtractorParams(BaseModel):
    pass


class KucoinWSData:
    @staticmethod
    @retry(wait=wait_fixed(0.01), stop=stop_after_attempt(5), reraise=True)
    async def get_kucoin_ws_details() -> dict[str, Any]:
        BULLET_URL: str = os.getenv("BULLET_URL_KUCOIN")
        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.post(BULLET_URL) as response:
                    data: dict[str, Any] = await response.json()
                    return data
        except aiohttp.ClientError as e:
            logger.error(e)
            raise e


class KucoinExtractor(AsyncExtractor[KucoinExtractorParams, KucoinRawData]):
    def __init__(self):
        # 1. threading.Event() because we want external threads to trigger stop, not from within the async loop
        # 2. To allow the thread to stop gracefully, finishing thoroughly and cleaning up all resources before stopping
        self.stop_event: threading.Event = threading.Event()

    def request_stop(self):
        self.stop_event.set()

    @retry(wait=wait_fixed(0.01), stop=stop_after_attempt(5), reraise=True)
    async def extract_async(
        self,
        kucoin_extractor_params: KucoinExtractorParams,
    ) -> AsyncGenerator[KucoinRawData, None]:
        # Kucoin requires to get WS details to subscribe to the WS
        # Creating connection string from the returned bullet_data
        while not self.stop_event.is_set():
            try:
                bullet_data: dict[str, Any] = await KucoinWSData.get_kucoin_ws_details()
                ws_endpoint = bullet_data["data"]["instanceServers"][0]["endpoint"]
                token: str = bullet_data["data"]["token"]
                connection_string: str = f"{ws_endpoint}?token={token}"

                async with aiohttp.ClientSession() as sess:
                    async with sess.ws_connect(connection_string) as ws:
                        # Subscribe to the ticker channel for specific products
                        subscribe_message = {
                            "id": "1",  # Unique identifier for the subscription.
                            "type": "subscribe",
                            "topic": "/market/ticker:all",  # Global ticker feed for all trading pairs.
                            "response": True,  # Ask for a confirmation response.
                        }
                        await ws.send_json(subscribe_message)
                        print("Subscription message sent.")
                        async for msg in ws:
                            if self.stop_event.is_set():
                                print("Stop event received — breaking WebSocket loop.")
                                break
                            msg: WSMessage
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                msg_string: str = msg.data
                                msg_dict: dict[str, Any] = json.loads(msg_string)
                                # To filter the welcome message
                                if "subject" in msg_dict and "data" in msg_dict:
                                    kucoin_ticker = KucoinRawData.model_validate(
                                        msg_dict
                                    )
                                    yield kucoin_ticker
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                raise ValueError("WebSocket connection closed.")
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                raise ValueError("WebSocket encountered an error.")
                print("WARNING: WebSocket session ended, will retry after short delay.")
                await asyncio.sleep(1)
            except aiohttp.ClientError as e:
                raise Exception(f"Client error occurred: {e}") from e
            except Exception as e:
                raise Exception(f"Unexpected error occurred: {e}") from e


async def main() -> None:
    kucoin_extractor_params: KucoinExtractorParams = KucoinExtractorParams()
    async for ticker in KucoinExtractor.extract_async(kucoin_extractor_params):
        print(ticker)


if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(main())
