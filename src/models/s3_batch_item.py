from pydantic import BaseModel
from datetime import datetime


class S3BatchItem(BaseModel):
    data: dict
    timestamp: datetime
    source: str
