from sqlalchemy import (
    create_engine,
    Table,
    Column,
    text,
    Boolean,
    Integer,
    String,
    Date,
    Sequence,
    Float,
    PrimaryKeyConstraint,
    ForeignKey,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Boolean
from stock_price import StockInfo
import pandas as pd
import talib

# --------------------------- Database schema / ORM -------------------------- #

Base = declarative_base()


class StockList(Base):
    __tablename__ = "stock_list"
    stock_id = Column(Integer, Sequence("stock_id_seq"), primary_key=True)
    code = Column(String, nullable=False)
    code_name = Column(String, nullable=False)
    prices = relationship("StockPrices", backref="stock", lazy="dynamic")


class StockPrices(Base):
    __tablename__ = "stock_prices"
    price_id = Column(Integer, Sequence("price_id_sq"), primary_key=True)
    stock_id = Column(Integer, ForeignKey("stock_list.stock_id"))
    date = Column(Date)
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    pctChg = Column(Float)
    volume = Column(Integer)
    amount = Column(Float)
    turn = Column(Float)


class CandlePatterns(Base):
    __tablename__ = "candle_patterns"
    pattern_id = Column(Integer, Sequence("pattern_id_sq"), primary_key=True)
    pattern_code = Column(String, nullable=False)
    pattern_name = Column(String, nullable=False)
    is_top = Column(Boolean, nullable=False)
    prices = relationship("StockMomentums", backref="patterns", lazy="dynamic")


class StockMomentums(Base):
    __tablename__ = "stock_momentums"
    momentum_id = Column(Integer, Sequence("momentum_id_seq"), primary_key=True)
    pattern_id = Column(Integer, ForeignKey("candle_patterns.pattern_id"))
    price_id = Column(Integer, ForeignKey("stock_prices.price_id"))
    value = Column(Float)


# ------------------------------ Populates data ------------------------------ #

# engine = create_engine("sqlite:///app.db", echo=True, future=True)
# # build schema
# with engine.connect() as conn:
#     conn.execute(text("DROP TABLE IF EXISTS stock_list"))
#     conn.execute(text("DROP TABLE IF EXISTS stock_prices"))
#     conn.execute(text("DROP TABLE IF EXISTS candle_patterns"))
#     conn.execute(text("DROP TABLE IF EXISTS stock_momentums"))

# Base.metadata.create_all(engine)

# stock_info = StockInfo()

# # Table stock_list
# df_stock_list = stock_info.fetchStockList()
# df_stock_list.drop(columns=["updateDate"], inplace=True)
# df_stock_list["stock_id"] = df_stock_list.index

# # Table stock_prices
# df_prices = stock_info.fetchStocksData(
#     start_date="2010-1-1",
#     end_date="2021-12-31",
#     stock_codes=df_stock_list.code,
# )
# df_prices["stock_id"] = df_prices["code"].map(
#     dict(df_stock_list[["code", "stock_id"]].values)
# )
# df_prices["price_id"] = df_prices.index
# df_prices.drop(columns=["code"], inplace=True)

# # Table candle_patterns
# df_patterns = pd.DataFrame(
#     candel_patterns.items(), columns=["pattern_code", "pattern_name"]
# )
# df_patterns["pattern_id"] = df_patterns.index

# # Table stock_momentums
# df_momentums = pd.DataFrame(columns=["pattern_id", "price_id", "value"])
# for pattern in candel_patterns.keys():
#     print(f"recognizing pattern {candel_patterns[pattern]} ....")
#     pattern_func = getattr(talib, pattern)
#     for stock_id in df_prices.stock_id.value_counts().index:
#         data = df_prices[df_prices.stock_id == stock_id].copy()
#         # print(pattern_func(data.open, data.high, data.low, data.close))
#         data.loc[:, ["value"]] = pattern_func(
#             data.open, data.high, data.low, data.close
#         )
#         data.loc[:, ["pattern_id"]] = dict(
#             zip(df_patterns.pattern_code, df_patterns.pattern_id)
#         )[pattern]

#         data.drop(data[data.value == 0].index, axis=0, inplace=True)
#         data = data.loc[:, ["pattern_id", "price_id", "value"]]

#         df_momentums = pd.concat([df_momentums, data], ignore_index=True)

# df_momentums["momentum_id"] = df_momentums.index


# df_stock_list.to_sql("stock_list", engine, if_exists="append", index=False)
# df_prices.to_sql("stock_prices", engine, if_exists="append", index=False)
# df_patterns.to_sql("candle_patterns", engine, if_exists="append", index=False)
# df_momentums.to_sql("stock_momentums", engine, if_exists="append", index=False)

# stock_info.logout()
