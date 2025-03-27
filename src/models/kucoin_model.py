from pydantic import BaseModel


class KucoinCryptoData(BaseModel):
    bestAsk: str
    bestAskSize: str
    bestBid: str
    price: str
    sequence: str
    size: str
    time: str  # Matching time of the latest transaction


class KucoinRawData(BaseModel):
    topic: str
    type: str
    subject: str
    data: KucoinCryptoData
