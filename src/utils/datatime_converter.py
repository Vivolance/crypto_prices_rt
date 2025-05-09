from datetime import datetime, timezone


class DatatimeConverter:
    """
    Converts UNIX timestamp retrieved from Binance and Kucoin into datetime format
    """

    @staticmethod
    def unix_to_utc(ts_ms: int) -> datetime:
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
