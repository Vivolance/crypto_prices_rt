# Identifying exchanges that provides live ticker information feed
1. Binance:
Offers a robust WebSocket API with streams for mini tickers, trade updates, order book changes, etc.

2. Coinbase Pro (now Coinbase Advanced Trade):
Provides a WebSocket feed where you can subscribe to channels (like ticker or level2 data) for specific products.

3. Kraken:
Has a WebSocket API that delivers live updates for trades, order book changes, and ticker information.

4. Bitfinex:
Offers a WebSocket API that streams real‑time market data, including price ticks and order book snapshots.

5. Bitstamp:
Provides a WebSocket feed for live trading data, including tickers and order book updates.

6. Huobi:
Features a WebSocket API delivering real‑time trade data and market depth information.

7. OKEx (now OKX):
Supplies a WebSocket API for streaming live data on trades, tickers, and order books.

8. KuCoin:
Also offers a WebSocket API for real‑time market data across various trading pairs.

## Verdict

### Binance API
Allows a global WebSocket subscription that streams real time ticker data for every instrument in one feed:
Binance’s !miniTicker@arr
connection_string: str = "wss://stream.binance.com:9443/ws/!miniTicker@arr"

Response:
Payload: list[dict]
```
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
```

### Kucoin
Requires a POST message to obtain a ws_endpoint and a token
Response 1:
```
{
"code": "200000",
"data": {
  "instanceServers": [
      {
          "endpoint": "wss://ws-xxx.kucoin.com/endpoint",
          "protocol": "websocket",
          "encrypt": True,
          "pingInterval": 18000,
          "pingTimeout": 10000
      }
  ],
  "token": "xxx"
}
}
```
connection_string: str = f"{ws_endpoint}?token={token}"

Response 2: 
```
{
    "topic": "/market/ticker:all",
    "type": "message",
    "subject": "BTC-USDT",
    "data": {
        "bestAsk": "67218.7",
        "bestAskSize": "1.92318539",
        "bestBid": "67218.6",
        "bestBidSize": "0.01045638",
        "price": "67220",
        "sequence": "14691455768",
        "size": "0.00004316",
        "time": 1729757723612 //The matching time of the latest transaction
    }
}    
```

## Points to note:
1. Kucoin gives all ticker pairs that exist on the chain, we are only interested in pairs against USDT
2. Kucoin symbol / instrument id differs from Binance's, requires normalization
3. Conversion of Unix timestamp to UTC, note Kucoin's timestamp represents last transacted price
coin_id: string
coin_name: string
coin_symbol: string
timestamp: datetime
price: double
source: string