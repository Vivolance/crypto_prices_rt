import asyncio
import json
from typing import AsyncGenerator, Any

import aiohttp
from aiohttp import ClientWebSocketResponse, WSMessage

"""
Stream from Binance all ticker stream, documentation: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams

Payload: list[dict]
[
  {
    "e": "24hrMiniTicker",  // Event type
    "E": 1672515782136,     // Event time
    "s": "BNBBTC",          // Symbol
    "c": "0.0025",          // Close price
    "o": "0.0010",          // Open price
    "h": "0.0025",          // High price
    "l": "0.0010",          // Low price
    "v": "10000",           // Total traded base asset volume
    "q": "18"               // Total traded quote asset volume
  },
]

"""


async def socket_request() -> AsyncGenerator[list[dict[str, Any]], None]:
    connection_string: str = "wss://stream.binance.com:9443/ws/!miniTicker@arr"
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.ws_connect(connection_string) as ws:
                ws: ClientWebSocketResponse
                async for msg in ws:
                    msg: WSMessage
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        msg_string: str = msg.data
                        msg_dict: list[dict[str, Any]] = json.loads(msg_string)
                        yield msg_dict
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        raise ValueError("WebSocket connection closed.")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        raise ValueError("WebSocket encountered an error.")
    except aiohttp.ClientError as e:
        raise Exception(f"Client error occurred: {e}") from e
    except Exception as e:
        raise Exception(f"Unexpected error occurred: {e}") from e


async def main() -> None:
    async for event in socket_request():
        print(event)


if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(main())
