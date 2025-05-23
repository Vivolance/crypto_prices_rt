import json
import logging
import os
from datetime import datetime

import boto3

from src.utils.generic_logger import logger_setup

logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)


class S3Uploader:
    """
    Handles uploading of batched raw data to Minio. Uploads raw data stream from
    kucoin and binance.
    """

    def __init__(self):
        self.bucket = os.getenv("MINIO_BUCKET", "cryptopricesrt")
        self.client = boto3.client(
            "s3",
            endpoint_url=os.getenv("MINIO_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
        )

    def upload_batch(
        self,
        source: str,
        records: list[dict],
        timestamp: datetime,
    ) -> None:
        """
        Uploads a batch of raw results to s3 given the source folder

        - source (str) "binance" or "kucoin"
        - records (list[dict]): Raw data
        - timestamp (datetime): UTC ingestion timestamp used as filename
        """
        folder: str = f"{source}/"
        filename: str = timestamp.strftime("%Y-%m-%dT%H-%M-%S.json")
        key: str = folder + filename

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(records).encode("utf-8"),
            ContentType="application/json",
        )
