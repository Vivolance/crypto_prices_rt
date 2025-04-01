from datetime import datetime

from numpy import double
from pydantic import BaseModel


class KucoinCryptoData(BaseModel):
    bestAsk: str
    bestAskSize: str
    bestBid: str
    price: str
    sequence: str
    size: str
    time: int  # Matching time of the latest transaction


class KucoinRawData(BaseModel):
    topic: str
    type: str
    subject: str
    data: KucoinCryptoData


class KucoinTransformedData(BaseModel):
    symbol: str
    price: double
    time: datetime
    source: str