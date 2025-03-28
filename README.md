# Real time pipeline for extracting live crypto prices

## Summary Flow
![img.png](./images/img.png)


## Extractors

### Binance
- Takes in a connection string, spins up web socket connection
- Deserialize JSON -> list[dict] -> list[BinanceRawData]
Raw Data:
[{'e': '24hrMiniTicker', 'E': 1743147448467, 's': 'BTCUSDT', 'c': '85439.99000000', 'o': '87304.35000000', 'h': '87728.27000000', 'l': '85300.01000000', 'v': '20230.79019000', 'q': '1754434346.25694750'},
{'e': '24hrMiniTicker', 'E': 1743147448251, 's': 'ETHUSDT', 'c': '1916.44000000', 'o': '2024.24000000', 'h': '2035.92000000', 'l': '1900.00000000', 'v': '518500.55270000', 'q': '1028765226.27080600'}]


### Kucoin
- First fires a REST API using BULLET URL to get confirmation response
- Filter the response to get token and ws_endpoint
- Spin up web socket connection with connection_string using token and ws_endpoint obtained
- Subscribe to all tickers channel with a subscribe message
subscribe_message = {
    "id": "1",  # Unique identifier for the subscription.
    "type": "subscribe",
    "topic": "/market/ticker:all",  # Global ticker feed for all trading pairs.
    "response": True,  # Ask for a confirmation response.
}
- Deserialize JSON -> dict[str, Any] -> KucoinRawData
Raw Data:
{'topic': '/market/ticker:all', 'type': 'message', 'subject': 'CRO-USDT', 'data': {'bestAsk': '0.10605', 'bestAskSize': '2522.2', 'bestBid': '0.10596', 'bestBidSize': '2160', 'price': '0.10604', 'sequence': '915875484', 'size': '159.3256', 'time': 1743147198992}}
{'topic': '/market/ticker:all', 'type': 'message', 'subject': 'POLYX-USDT', 'data': {'bestAsk': '0.1386', 'bestAskSize': '436.0723', 'bestBid': '0.1385', 'bestBidSize': '7650', 'price': '0.1388', 'sequence': '329205844', 'size': '516.554', 'time': 1743146640946}}


### Questions
1. Kucoin returns a single instance of a dataclass while Binance returns
a list[dataclass]. Do I want to batch Kucoin's output so that my produce method
in Kafka can be consistent? If so, what are the criteria for batching? So
far, Binance batches a list of all tickers per second, but i do not know
exactly where Kucoin cutoff is for its entire list of tickers. They both
comes in a consistent stream





