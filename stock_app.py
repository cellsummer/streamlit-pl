from mimetypes import init
from typing import Any
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
from datetime import date
from time import time
from stock_data import StockList, StockPrices, StockMomentums, CandlePatterns
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


class DataLoader:
    table_names = ["all_stocks", "candle_patterns", "top_patterns"]
    scalar_names = ["today", "earliest_date"]
    tables = {}
    scalars = {}

    def __init__(self, connection) -> None:
        self.connection = connection
        for t in self.table_names:
            self.tables[t] = self.load_table_data(t)
        for s in self.scalar_names:
            self.scalars[s] = self.load_scalar_data(s)

    def create_db_session(self):
        engine = create_engine(self.connection, echo=False, future=False)
        return sessionmaker(bind=engine)()

    def load_scalar_data(self, scalar="today") -> Any:
        if scalar == "today":
            return date(2021, 5, 20)

        if scalar == "earliest_date":
            return date(2020, 1, 1)

        print(f"Scalar data {scalar} loading is not implemented!")
        return

    def load_table_data(self, table="all_stocks") -> Any:
        with self.create_db_session() as session:
            if table == "all_stocks":
                print("loading all_stocks...")
                return pd.read_sql_query(
                    session.query(StockList).statement,
                    session.bind,
                    index_col="stock_id",
                )

            if table == "candle_patterns":
                print("loading candlepatterns...")
                return pd.read_sql_query(
                    session.query(CandlePatterns).statement,
                    session.bind,
                    index_col="pattern_id",
                )

            if table == "top_patterns":
                print("loading top patterns...")
                return pd.read_sql_query(
                    session.query(CandlePatterns).filter(
                        CandlePatterns.is_top == True).statement,
                    session.bind,
                    index_col="pattern_id",
                )

        print(f"Table data {table} loading is not implemented!")


class App:
    def __init__(self) -> None:
        pass

    def run(self):
        start_time = time()
        data_loader = DataLoader(connection="sqlite:///app.db")

        st.set_page_config(
            page_title="Streamlit Stock App",
            page_icon="💰",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        page_maker = PageMaker(data_loader)
        page = page_maker.make_menu()

        if page == "Home":
            page_maker.make_home_page()

        elif page == "View Stocks":
            page_maker.make_display_page()

        else:
            print("Not implemented!")

        print(f"run time is {time() - start_time}")


class PageMaker:
    def __init__(self, data_loader) -> None:
        self.data_loader = data_loader

    def make_menu(self):
        # Side bar layout
        navigation_menu = ["Home", "View Stocks"]
        page = st.sidebar.selectbox("Page", options=navigation_menu)

        return page

    def make_sidebar_display(self, ):
        # need all_stocks: index, code, code_name
        all_stocks = self.data_loader.tables["all_stocks"]

        with st.sidebar.form("stock_display"):
            stock_pool = st.selectbox(
                "Choose stock ticker to display:",
                options=list(all_stocks.index),
                format_func=
                (lambda x:
                 f'{all_stocks.loc[x, "code"]}:{all_stocks.loc[x, "code_name"]}'
                 ),
            )
            display_btn = st.form_submit_button("Display stocks")

        return {"stock_pool": stock_pool, "display": display_btn}

    def make_sidebar_home(self, ):
        candle_patterns = self.data_loader.tables["candle_patterns"]

        earliest_date = self.data_loader.scalars["earliest_date"]
        today = self.data_loader.scalars["today"]

        with st.sidebar.form("date_range"):
            pattern_selector = st.selectbox(
                "Select Pattern:",
                options=list(candle_patterns.index),
                format_func=lambda x: str(candle_patterns.loc[x, "pattern_name"
                                                              ]),
            )
            col1, col2 = st.beta_columns(2)
            start_date_slider = col1.date_input("Start Date:", earliest_date)
            end_date_slider = col2.date_input("End Date:", today)
            date_input = st.date_input(
                "Pattern Detection Date:",
                today,
            )
            submit_btn = st.form_submit_button("Scan Selected Pattern")
            scan_btn = st.form_submit_button("Scan All Top Patterns")

        st.sidebar.write(
            "For candlestick patterns, visit: http://thepatternsite.com/CandleVisual.html"
        )

        return {
            "start_date": start_date_slider,
            "end_date": end_date_slider,
            "mark_date": date_input,
            "patterns": [pattern_selector],
            "scan_pattern": submit_btn,
            "scan_all": scan_btn,
        }

    def get_page_data(
        self,
        input_info: dict,
        page="Home",
        use_single_pattern=True,
    ):
        if page == "Home":
            mark_date = input_info["mark_date"]
            patterns = (input_info["patterns"] if use_single_pattern else
                        self.data_loader.tables["top_patterns"].index)

            with self.data_loader.create_db_session() as session:
                stocks = (session.query(
                    StockList, StockMomentums.value,
                    CandlePatterns).select_from(StockList).join(StockPrices).
                          join(StockMomentums).join(CandlePatterns).filter(
                              CandlePatterns.pattern_id.in_(patterns),
                              StockPrices.date == mark_date,
                          ).all())
            return stocks

        elif page == "Display":
            return
        else:
            print(f"No such page defined: {page}")
            return

    def make_home_page(self):

        st.write("# Candle Pattern Scanner")

        # sidebar
        input_info = self.make_sidebar_home()

        start_date = input_info["start_date"]
        end_date = input_info["end_date"]
        mark_date = input_info["mark_date"]
        scan_all = input_info["scan_all"]
        scan_pattern = input_info["scan_pattern"]
        use_single_pattern = False

        # main body
        col1, col2 = st.beta_columns(2)
        col1.write("## Bullish Trend:")
        col2.write("## Bearish Trend:")

        if scan_pattern or scan_all:
            if scan_all:
                use_single_pattern = False

            if scan_pattern:
                use_single_pattern = True

            stocks = self.get_page_data(
                input_info=input_info,
                page="Home",
                use_single_pattern=use_single_pattern,
            )

            if not stocks:
                st.warning("No such pattern(s) was found!")
            else:

                graph_maker = GraphMaker(self.data_loader)

                with st.spinner("loading data..."):
                    for stock, momentum, pattern in stocks:
                        fig = graph_maker.make_canddle_graph(
                            stock, start_date, end_date, mark_date)

                        trend = "Bullish" if momentum > 0 else "Bearish"
                        (col1 if trend == "Bullish" else col2).write(
                            f"""
                            ### {stock.code}:{stock.code_name} - {pattern.pattern_name}
                            """, )

                        (col1
                         if trend == "Bullish" else col2).plotly_chart(fig)

            return

    def make_display_page(self):
        all_stocks = self.data_loader.tables["all_stocks"]

        with open("trading_view.html", "r") as f:
            widget = f.read()

        with open("trading_view_markets.html", "r") as f:
            market_widget = f.read()

        st.write("# Stock Price Chart")
        components.html(market_widget, width=1250, height=80)

        input_info = self.make_sidebar_display()

        if input_info["display"]:
            stock_pool = input_info["stock_pool"]

            if stock_pool == None:
                st.error("No Stocks are selected yet.")
            else:
                stock = all_stocks.loc[stock_pool, "code"]
                exchange, symbol = stock.split(".")
                exchange_code = "SSE" if exchange == "sh" else "SZSE"
                ticker = f"{exchange_code}:{symbol}"
                candle_widget = widget.replace("{{TICKER}}", ticker)
                components.html(candle_widget, height=610, width=1250)


class GraphMaker:
    def __init__(self, data_loader: DataLoader) -> None:
        self.data_loader = data_loader

    def get_graph_data(self, stock, start_date, end_date):
        with self.data_loader.create_db_session() as session:
            df_stock = pd.read_sql_query(
                stock.prices.statement,
                session.bind,
                index_col="price_id",
            )
            df_stock = df_stock[df_stock['date'].between(start_date, end_date)]

        return df_stock

    def make_canddle_graph(
        self,
        stock: Any,
        start_date: date,
        end_date: date,
        mark_date: date,
    ):
        # for stock, momentum, pattern in data:
        df_stock = self.get_graph_data(stock, start_date, end_date)
        # trend = "Bullish" if momentum > 0 else "Bearish"
        fig = go.Figure(data=[
            go.Candlestick(
                x=df_stock["date"],
                open=df_stock["open"],
                high=df_stock["high"],
                low=df_stock["low"],
                close=df_stock["close"],
                increasing_line_color="red",
                decreasing_line_color="green",
            )
        ])
        fig.update_layout(
            xaxis_rangeslider_visible=True,
            xaxis={"type": "category"},
        )
        fig.update_xaxes(nticks=10)
        fig.add_shape(
            type="rect",
            xref="x",
            yref="paper",
            x0=mark_date,
            y0=0,
            x1=end_date,
            y1=1,
            line=dict(
                color="rgba(0,0,0,0)",
                width=3,
            ),
            fillcolor="rgba(200,0,200,0.2)",
            layer="below",
        )

        return fig


if __name__ == "__main__":
    App().run()
