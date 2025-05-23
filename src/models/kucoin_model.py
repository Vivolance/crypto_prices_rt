from datetime import datetime

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
    price: float
    time: datetime
    source: str
    created_at: datetime
