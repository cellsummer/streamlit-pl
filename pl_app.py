import streamlit as st
from data_proc import SeasonSummary
import pandas as pd


st.set_page_config(
    page_title="Streamlit Premier League App",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.write("## Welcome to the Premier League App!")
# load data from csv file
all_df = pd.read_csv("bet_data.csv", low_memory=False)
# use the dropdown to navigate different pages.

main_menu = [
    "League Tables",
    "Results Matrix",
    # "Stats",
    "Head-to-Head",
    # "Goals & Scores",
    # "News",
]
season_menu = all_df["season"].unique().tolist()
home_menu = ["Liverpool", "Arsenal", "Chelsea", "Man United", "Man City", "Tottenham"]
away_menu = ["Liverpool", "Arsenal", "Chelsea", "Man United", "Man City", "Tottenham"]
st.sidebar.image("Barclays_PL.png")
st.sidebar.write("# Premier League Analytics and Dashboard")
st.sidebar.write(
    "ExploreExplore historical results for the Premier League season and see the analytics and betting odds for your favourite team. "
)
page = st.sidebar.selectbox("Page", main_menu)
season = st.sidebar.selectbox(
    "Select your season:", season_menu, index=len(season_menu) - 1
)

# choose the current season's data
data_summary = SeasonSummary(data=all_df, season=season)
result_matrix = data_summary.get_result_matrix()
result_matrix.index = result_matrix["Teams"]
result_matrix.drop(columns=["Teams"], inplace=True)

# Display data
if page == "League Tables":
    table_type = st.sidebar.selectbox("League Table:", ["overall", "home", "away"])
    display_cols = [
        "played",
        "won",
        "draw",
        "lost",
        "goals_scored",
        "goals_conceded",
        "gd",
        "points",
    ]
    league_table = data_summary.calc_main_tables(table_type)
    league_table = league_table[display_cols]
    st.dataframe(data=league_table, height=900)
if page == "Results Matrix":
    st.dataframe(data=result_matrix, height=900)
if page == "Head-to-Head":
    home_team = st.sidebar.selectbox("Select home team:", home_menu, index=0)
    away_team = st.sidebar.selectbox("Select away team:", away_menu, index=1)
    col1, col2 = st.beta_columns(2)
    stats_displays = [
        ["mp", "win", "draw", "lost", "gs", "gc"],
        ["position", "points", "avg_points"],
        ["avg_gs", "avg_gc", "avg_goals"],
        ["corners_for", "corners_against", "corners_total"],
        ["shots_on_goal_f", "shots_on_goal_a"],
        ["fouls_commited", "fouls_suffered", "fouls_total"],
    ]
    with col1:
        st.header(home_team)
        stats = data_summary.calc_team_stats(home_team)

        for stats_display in stats_displays:
            st.dataframe(stats[stats_display], width=450)

    with col2:
        st.header(away_team)
        stats = data_summary.calc_team_stats(away_team)

        for stats_display in stats_displays:
            st.dataframe(stats[stats_display], width=450)
