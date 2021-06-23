import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
import json
from datetime import date
from stock_data import StockList, StockPrices, StockMomentums, CandlePatterns
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# back-end config
engine = create_engine(
    "sqlite:///app.db",
    echo=False,
    future=False,
)
Session = sessionmaker(bind=engine)

# front-end config
st.set_page_config(
    page_title="Streamlit Stock App",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

today = date(2021, 5, 20)
earliest_date = date(2020, 1, 1)

with open("trading_view.html", "r") as f:
    widget = f.read()

with open("trading_view_markets.html", "r") as f:
    market_widget = f.read()


with Session() as session:
    all_stocks = pd.read_sql_query(
        session.query(StockList).statement, session.bind, index_col="stock_id"
    )
    candle_patterns = pd.read_sql_query(
        session.query(CandlePatterns).statement, session.bind, index_col="pattern_id"
    )
    top_patterns = candle_patterns[candle_patterns["is_top"]]

# Side bar layout
navigation_menu = ["Home", "View Stocks"]

page = st.sidebar.selectbox("Page", options=navigation_menu)

if page == "Home":

    st.write("# Candle Pattern Scanner")

    with st.sidebar.form("date_range"):
        pattern_selector = st.selectbox(
            "Select Pattern:",
            options=list(candle_patterns.index),
            format_func=lambda x: str(candle_patterns.loc[x, "pattern_name"]),
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

    def graph_data(
        start_date,
        end_date,
        mark_date,
        patterns,
    ) -> None:

        col1, col2 = st.beta_columns(2)
        stocks = (
            session.query(StockList, StockMomentums.value, CandlePatterns)
            .select_from(StockList)
            .join(StockPrices)
            .join(StockMomentums)
            .join(CandlePatterns)
            .filter(
                CandlePatterns.pattern_id.in_(patterns),
                StockPrices.date == mark_date,
            )
            .all()
        )

        if not stocks:
            st.warning("No such pattern(s) was found!")
            return

        col1.write("## Bullish Trend:")
        col2.write("## Bearish Trend:")

        for stock, momentum, pattern in stocks:
            df_stock = pd.read_sql_query(
                stock.prices.statement,
                session.bind,
                index_col="price_id",
            )
            df_stock = df_stock[df_stock["date"].between(start_date, end_date)]

            trend = "Bullish" if momentum > 0 else "Bearish"

            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=df_stock["date"],
                        open=df_stock["open"],
                        high=df_stock["high"],
                        low=df_stock["low"],
                        close=df_stock["close"],
                        increasing_line_color="red",
                        decreasing_line_color="green",
                    )
                ]
            )
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
            # fig.update_layout(template="plotly_dark")
            # fig.show()

            (col1 if trend == "Bullish" else col2).write(
                f"""
                ### {stock.code}:{stock.code_name} - {pattern.pattern_name}
                """,
            )

            (col1 if trend == "Bullish" else col2).plotly_chart(fig)

        return

    if submit_btn:
        with st.spinner("Loading data..."):
            with Session() as session:
                graph_data(
                    # df_stocks,
                    start_date_slider,
                    end_date_slider,
                    date_input,
                    [pattern_selector],
                )

    if scan_btn:
        with st.spinner("Loading data..."):
            with Session() as session:
                graph_data(
                    start_date_slider,
                    end_date_slider,
                    date_input,
                    top_patterns.index,
                )

elif page == "View Stocks":

    st.write("# Stock Price Chart")
    components.html(market_widget, width=1250, height=80)

    with st.sidebar.form("stock_display"):
        stock_pool = st.selectbox(
            "Choose stock ticker to display:",
            options=list(all_stocks.index),
            format_func=(
                lambda x: f'{all_stocks.loc[x, "code"]}:{all_stocks.loc[x, "code_name"]}'
            ),
        )
        display_btn = st.form_submit_button("Display stocks")

    if display_btn:
        if stock_pool == None:
            st.error("No Stocks are selected yet.")
        else:
            stock = all_stocks.loc[stock_pool, "code"]
            exchange, symbol = stock.split(".")
            exchange_code = "SSE" if exchange == "sh" else "SZSE"
            ticker = f"{exchange_code}:{symbol}"
            candle_widget = widget.replace("{{TICKER}}", ticker)
            components.html(candle_widget, height=610, width=1250)
