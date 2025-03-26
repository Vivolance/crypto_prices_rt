import asyncio
import json
from typing import AsyncGenerator, Any

import aiohttp
from aiohttp import ClientWebSocketResponse, WSMessage

"""
Coinbase, unlike Binance, do not provide a live stream of all its products. To solve this:
1. Get a list of all products from coinbase rest api: https://api.pro.coinbase.com/products
2. After getting the list of products, use it as part of the subscribe message to coinbase stream api:
wss://ws-feed.pro.coinbase.com

Subscribe message:
{
  "type": "subscribe",
  "product_ids": ["ETH-USD", "ETH-EUR"],
  "channels": [
    "level2",
    "heartbeat",
    {
      "name": "ticker",
      "product_ids": ["ETH-BTC", "ETH-USD"]
    }
  ]
}

Response 1: (Confirmation)
{
    "type": "subscriptions",
    "channels": [
        {
            "name": "ticker",
            "product_ids": [
                "BTC-USD",
                "ETH-USD",
                "... (other products)"
            ]
        }
    ]
}


Response 2:
{
    "type": "ticker",
    "sequence": 123456789,
    "product_id": "BTC-USD",
    "price": "30000.00",
    "open_24h": "29500.00",
    "volume_24h": "1200.00",
    "low_24h": "29000.00",
    "high_24h": "31000.00",
    "best_bid": "29995.00",
    "best_ask": "30005.00",
    "side": "buy",         // Indicates whether the last trade was a buy or sell
    "time": "2025-03-25T16:34:17.058Z",
    "trade_id": 987654,
    "last_size": "0.01"
}

"""


BULLET_URL: str = "https://api.kucoin.com/api/v1/bullet-public"


async def get_kucoin_ws_details() -> dict[str, Any]:
    async with aiohttp.ClientSession() as sess:
        async with sess.post(BULLET_URL) as response:
            data: dict[str, Any] = await response.json()
            # {
            #   "code": "200000",
            #   "data": {
            #       "instanceServers": [
            #           {
            #               "endpoint": "wss://ws-xxx.kucoin.com/endpoint",
            #               "protocol": "websocket",
            #               "encrypt": True,
            #               "pingInterval": 18000,
            #               "pingTimeout": 10000
            #           }
            #       ],
            #       "token": "xxx"
            #   }
            # }
            return data["data"]


async def socket_request() -> AsyncGenerator[dict[str, Any], None]:
    # Get the bullet details (endpoint + token)
    bullet_data: dict[str, Any] = await get_kucoin_ws_details()
    ws_endpoint = bullet_data["instanceServers"][0]["endpoint"]
    token: str = bullet_data["token"]
    connection_string: str = f"{ws_endpoint}?token={token}"

    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.ws_connect(connection_string) as ws:
                # Subscribe to the ticker channel for specific products
                subscribe_message = {
                    "id": "1",  # Unique identifier for the subscription.
                    "type": "subscribe",
                    "topic": "/market/ticker:all",  # Global ticker feed for all trading pairs.
                    "response": True  # Ask for a confirmation response.
                }
                await ws.send_json(subscribe_message)
                print("Subscription message sent.")
                async for msg in ws:
                    msg: WSMessage
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data: dict[str, Any] = json.loads(msg.data)
                        yield data
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        raise ValueError("WebSocket connection closed.")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        raise ValueError("WebSocket encountered an error.")
    except aiohttp.ClientError as e:
        raise Exception(f"Client error occurred: {e}") from e
    except Exception as e:
        raise Exception(f"Unexpected error occurred: {e}") from e


async def main() -> None:
    async for ticker in socket_request():
        print(ticker)


if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(main())
