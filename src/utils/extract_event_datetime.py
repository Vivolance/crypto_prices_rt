from datetime import datetime
from typing import Literal


"""
Converts UNIX timestamp retrieved from Binance and Kucoin into datetime format
"""


def extract_event_datetime(
    source: Literal["kucoin", "binance"], message: dict
) -> datetime:
    """
    Extracts the event time of each message from binance and kucoin
    - binance: timestamp is at message["E"]
    - kucoin: timestamp is at message["data"]["time"]
    """
    if source == "kucoin":
        timestamp_ms = message["data"]["time"]  # in ms
    elif source == "binance":
        timestamp_ms = message["E"]  # in ms
    else:
        raise ValueError(f"Unknown source: {source}")

    return datetime.utcfromtimestamp(timestamp_ms / 1000)
