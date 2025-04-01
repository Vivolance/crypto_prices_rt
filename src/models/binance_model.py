from datetime import datetime

from numpy import double
from pydantic import BaseModel


class BinanceRawData(BaseModel):
    e: str  # Event type
    E: int  # Event time
    s: str  # Symbol
    c: str  # Close
    o: str  # Open
    h: str  # High
    l: str  # Low
    v: str  # Total traded base asset volume
    q: str  # Total traded quote asset volume


class BinanceTransformedData(BaseModel):
    symbol: str
    price: double
    time: datetime
    source: str
