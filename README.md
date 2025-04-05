# Real time pipeline for extracting live crypto prices

## Summary Flow
![img.png](./images/img.png)

## ===== CHECKPOINT 1 =======
1. Created Kucoin Websocket
Payload: firehose of dicts
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

2. Created Binance Websocket
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

### Binance tidbits
- Takes in a connection string, spins up web socket connection
- Deserialize JSON -> list[dict] -> list[BinanceRawData]
Raw Data:
[{'e': '24hrMiniTicker', 'E': 1743147448467, 's': 'BTCUSDT', 'c': '85439.99000000', 'o': '87304.35000000', 'h': '87728.27000000', 'l': '85300.01000000', 'v': '20230.79019000', 'q': '1754434346.25694750'},
{'e': '24hrMiniTicker', 'E': 1743147448251, 's': 'ETHUSDT', 'c': '1916.44000000', 'o': '2024.24000000', 'h': '2035.92000000', 'l': '1900.00000000', 'v': '518500.55270000', 'q': '1028765226.27080600'}]


### Kucoin tidbits
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
1. Kucoin returns a single instance of a dataclass while Binance returns a list[dataclass]. Do I want to batch Kucoin's output so that my produce method
in Kafka can be consistent? If so, what are the criteria for batching? So far, Binance batches a list of all tickers per second, but i do not know
exactly where Kucoin cutoff is for its entire list of tickers. They both comes in a consistent stream.

Goal: Define a batching logic for Kucoin so it makes sense to call produce(batch) at the right time without wasting 
resources, introducing latency, or sending too few/too many messages per Kafka write.

Problem:
Binance returns a list[dict] while Kucoin returns a firehose of dict.
Binance is simple as the list[dict] is already batched and ready to be produced to Kafka
However the discussion lies:
Option 1: Batch Kucoin results first before producing
Option 2: Producing it first then batch in the consumer

Option 1 Pros:
- Fewer overhead, less resources for spinning up as a single message is a batch
- s3 uploader logic is simpler as it already gets a list[dict] from both data source
- More efficient for Spark downstream as it is batched already

Option 1 Cons:
- Needs batching logic inside extractor (SRP?)

Option 2 Pros:
- Extractor do not require batching logic.

Option 2 Cons:
- Batching logic required in consumer class (Spark)
- Easy to overwhelm broker as a single message is a dict, overhead for i/o increases
- Spark stream consumption is more overwhelmed

Proposal:
Per-symbol time window batching between kucoin extractor and producer.
Creates a buffer batch which "batches" the kucoin data coming in by 2 conditions:
1. Only produce to topic when a symbol has collected 100 messages:
2. Produce to topic every 1 second.

This prevents:
1. Reduces strain on Kafka and kafka only produces when batch is ready
2. Reduces message writes to Kafka, less i/o
3. Kafka do not have to scan thousands of messages from a topic in a period (needle in a haystack problem)

Conclusion: Option 1

## ===== CHECKPOINT 2 =======
1. Created kucoin websocket -> returns firehose of dicts
2. Created binance websocket -> returns list[dicts]
3. Serialized 1 and 2 into dataclass and list[dataclass] respectively
4. Batched 1 into a list[dataclass]
5. In the produce method, deserialized list[dataclass] into JSONArray
6. Successfully produced JSONArray to kucoin_raw_topic and binance_raw_topic

Steps to run up till now:
1. Start Zookeeper by navigating to directory where Kafka is installed
```commandline
bin/zookeeper-server-start.sh config/zookeeper.properties
```

2. Start Kafka by navigating to directory where Kafka is installed
```commandline
bin/kafka-server-start.sh config/server.properties
```

3. Manual consume from a kucoin_raw_data topic to see the messages
```commandline
bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic kucoin_raw_data \
  --from-beginning \
  --property print.key=true \
  --property print.value=true \
  --property print.timestamp=true

```