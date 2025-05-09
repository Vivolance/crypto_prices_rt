from datetime import datetime


def build_s3_key(source: str, event_dt: datetime) -> str:
    """
    Builds a structured s3 key path using source and timestamp.
    E.g raw/kucoin/2025/05/07/data_20250507T15.json.gz
    """
    year: str = event_dt.strftime("%Y")
    month: str = event_dt.strftime("%m")
    day: str = event_dt.strftime("%d")
    hour: str = event_dt.strftime("%H")
    timestamp_str: str = event_dt.strftime("%Y%m%dT%H")

    return f"raw/{source}/{year}/{month}/{day}/{hour}/data_{timestamp_str}.json.gz"
