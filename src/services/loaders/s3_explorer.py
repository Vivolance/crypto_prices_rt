import json
import logging
import os
from datetime import datetime
from typing import Iterator
import re

import boto3
from dotenv import load_dotenv
from mypy_boto3_s3 import ListObjectsV2Paginator

from src.utils.generic_logger import logger_setup

logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)


class S3Explorer:
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

    def download_batch(
        self, source: str, start_time: datetime, end_time: datetime = datetime.utcnow()
    ) -> list[dict]:
        """
        Downloads and returns a list[dict] given source and a range of time
        """
        all_records: list[dict] = []
        for key in self.list_files_with_range(source, start_time, end_time):
            # get_object reads file in memory
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            content = response["Body"].read()
            records = json.loads(content)
            all_records.extend(records)
        return all_records

    def list_files_with_range(
        self, source: str, start_time: datetime, end_time: datetime = datetime.utcnow()
    ) -> Iterator[str]:
        """
        List all files under a given prefix and time range and return a generator of file paths
        """
        prefix: str = f"{source}/"
        regex: re.Pattern = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})\.json$")

        # S3 limits the number of results per API call (usually 1000 objects per request).
        # If you have more than 1000 files in a folder/prefix, a single list_objects_v2 call will not return everything.
        # The paginator transparently makes multiple requests behind the scenes, so you can process all files matching
        # your filter.
        paginator: ListObjectsV2Paginator = self.client.get_paginator("list_objects_v2")
        # paginate creates an iterator that paginate the response
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            # iterate through objects of each page
            for obj in page.get("Contents", []):
                match = regex.search(obj["Key"])
                if not match:
                    continue
                file_time: datetime = datetime.strptime(
                    match.group(1), "%Y-%m-%dT%H-%M-%S"
                )
                if start_time <= file_time <= end_time:
                    yield obj["Key"]


if __name__ == "__main__":
    load_dotenv()
    start: datetime = datetime(2025, 5, 23, 00, 00, 00)
    end: datetime = datetime(2025, 5, 24, 00, 00, 00)
    my_s3_explorer: S3Explorer = S3Explorer()
    records = my_s3_explorer.download_batch("binance", start, end)
    for r in records[:3]:
        print(r)
    print(
        f"Downloaded {len(records)} records from binance between 23rd May 2025 and 24th May 2025"
    )
