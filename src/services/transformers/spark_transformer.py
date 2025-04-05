from typing import Any

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import types as T, functions as F

from src.models.binance_model import BinanceTransformedData
from src.models.kucoin_model import KucoinTransformedData


class SparkTransformer:
    def __init__(self) -> None:
        self.spark: SparkSession = SparkSession.builder.appName(
            "CryptoTickerTransformer"
        ).getOrCreate()
        self._kucoin_schema = T.StructType(
            [
                T.StructField("subject", T.StringType()),
                T.StructField(
                    "data",
                    T.StructType(
                        [
                            T.StructField("price", T.StringType()),
                            T.StructField("time", T.LongType()),
                        ]
                    ),
                ),
            ]
        )

        self._binance_schema = T.StructType(
            [
                T.StructField("s", T.StringType()),
                T.StructField("c", T.StringType()),
                T.StructField("E", T.LongType()),
            ]
        )

    def transform_kucoin(
        self, kucoin_records: list[dict[str, Any]]
    ) -> list[KucoinTransformedData]:
        """
        Be sure to let the consumer deserialize from Jsonarray -> list[dict] using json_loads before passing here
        """
        df: DataFrame = self.spark.createDataFrame(kucoin_records, schema=self._kucoin_schema)  # type: ignore[arg-type]
        transformed_df: DataFrame = (
            df.withColumn("symbol", F.regexp_replace("subject", "-", ""))
            .filter(
                (F.col("symbol").endswith("USDT")) | (F.col("symbol").endswith("USDC"))
            )
            .withColumn("price", F.col("data.price").cast("float"))
            .withColumn("time", F.expr("to_timestamp(data.time / 1000)"))
            .withColumn("source", F.lit("kucoin"))
            .select("symbol", "price", "time", "source")
        )  # select only necessary column
        # Converts Spark DF into pydantic dataclass by calling asDict() on every row. collect() gives back a list[row]
        return [
            KucoinTransformedData(**row.asDict()) for row in transformed_df.collect()
        ]

    def transform_binance(
        self, binance_records: list[dict[str, Any]]
    ) -> list[BinanceTransformedData]:
        """
        Be sure to let the consumer deserialize from Jsonarray -> list[dict] using json_loads before passing here
        """
        df: DataFrame = self.spark.createDataFrame(binance_records, schema=self._binance_schema)  # type: ignore[arg-type]

        transformed_df = (
            df.filter((F.col("s").endswith("USDT")) | (F.col("s").endswith("USDC")))
            .withColumnRenamed("s", "symbol")
            .withColumn("price", F.col("c").cast("double"))
            .withColumn("time", F.expr("to_timestamp(E / 1000)"))
            .withColumn("source", F.lit("binance"))
            .select("symbol", "price", "time", "source")
        )

        return [
            BinanceTransformedData(**row.asDict()) for row in transformed_df.collect()
        ]
