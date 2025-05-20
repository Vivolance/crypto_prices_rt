from sqlalchemy import MetaData, TEXT, Table, Column, FLOAT, DateTime

metadata: MetaData = MetaData()


kucoin_table: Table = Table(
    "kucoin_result",
    metadata,
    Column("symbol", TEXT, primary_key=True),
    Column("price", FLOAT, nullable=False),
    Column("time", DateTime, nullable=False),
    Column("source", TEXT, nullable=False),
    Column("created_at", DateTime, nullable=False),
)
"""

"""


binance_table: Table = Table(
    "kucoin_result",
    metadata,
    Column("symbol", TEXT, primary_key=True),
    Column("price", FLOAT, nullable=False),
    Column("time", DateTime, nullable=False),
    Column("source", TEXT, nullable=False),
    Column("created_at", DateTime, nullable=False),
)
