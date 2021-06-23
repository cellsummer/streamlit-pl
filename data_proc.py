import pandas as pd
import os
import glob
import numpy as np


def read_csv_data():
    files = glob.glob(os.path.join(os.getcwd(), "data\\bet\\*.csv"))
    dfs = []
    for file in files:
        file_name = file.split("\\")[-1]
        season = file_name[3:5] + "-" + file_name[5:7]
        print(f"processing season: {season} ...")
        current_df = pd.read_csv(file, encoding="utf-8")
        current_df["season"] = season

        dfs.append(current_df)

    df = pd.concat(dfs, ignore_index=True)
    # df = df.astype({"Time": str})
    df.to_csv("data/bet_data.csv", index=False)
    return df


class SeasonSummary:
    def __init__(self, data, season):
        self.data = data[data["season"] == season]
        self.season = season
        self.num_of_matches = len(self.data.index)

    def __repr__(self):
        return f"SeasonSummary(data = {self.data}, season = {self.season})"

    def get_result_matrix(self):
        """get the result matrict for a single season"""
        teams = self.data["HomeTeam"].unique().tolist()
        teams.sort()
        results = []

        for team in teams:
            record = {"Teams": team}
            for opponent in teams:
                if team == opponent:
                    score = "-"
                else:
                    filt = self.data["HomeTeam"].eq(team) & self.data["AwayTeam"].eq(
                        opponent
                    )
                    home_score = int(self.data.loc[filt, "FTHG"].tolist()[0])
                    away_score = int(self.data.loc[filt, "FTAG"].tolist()[0])
                    score = f"{home_score}-{away_score}"
                record[opponent] = score
            results.append(record)

        return pd.DataFrame.from_records(results)

    def summary_goals(self):
        """get the summary of goals for a single season"""
        # num_of_matches = len(df.index)

        df_idx = ["home_goals", "away_goals", "total_goals"]
        # df_cols = ["ft_cnt, ft_avg, fh_cnt, fh_avg, sh_cnt, sh_avg"]

        ft_cnt = np.array(
            [
                self.data["FTHG"].sum(),
                self.data["FTAG"].sum(),
                self.data["FTHG"].sum() + self.data["FTAG"].sum(),
            ]
        )
        fh_cnt = np.array(
            [
                self.data["HTHG"].sum(),
                self.data["HTAG"].sum(),
                self.data["HTHG"].sum() + self.data["HTAG"].sum(),
            ]
        )
        sh_cnt = ft_cnt - fh_cnt
        ft_avg = ft_cnt / self.num_of_matches
        fh_avg = fh_cnt / self.num_of_matches
        sh_avg = sh_cnt / self.num_of_matches

        result = pd.DataFrame(
            data={
                "ft_cnt": ft_cnt,
                "ft_avg": ft_avg,
                "fh_cnt": fh_cnt,
                "fh_avg": fh_avg,
                "sh_cnt": sh_cnt,
                "sh_avg": sh_avg,
            },
            index=df_idx,
        )

        print(ft_cnt)

        return result

    def summary_ft_results(self):
        """get the summary of the full time results and their odds"""
        df_idx = ["home_win", "draw", "away_win"]
        match_cnt = np.array(
            [
                len(self.data[self.data["FTR"] == "H"].index),
                len(self.data[self.data["FTR"] == "D"].index),
                len(self.data[self.data["FTR"] == "A"].index),
            ]
        )

        match_pct = match_cnt / sum(match_cnt) * 100

        avg_odds_pin = np.array(
            [
                self.data["PSH"].mean(),
                self.data["PSD"].mean(),
                self.data["PSA"].mean(),
            ]
        )
        avg_odds_bet = np.array(
            [
                self.data["B365H"].mean(),
                self.data["B365D"].mean(),
                self.data["B365A"].mean(),
            ]
        )
        avg_winodds_pin = np.array(
            [
                self.data.loc[self.data["FTR"] == "H", "PSH"].mean(),
                self.data.loc[self.data["FTR"] == "D", "PSD"].mean(),
                self.data.loc[self.data["FTR"] == "A", "PSA"].mean(),
            ]
        )
        avg_winodds_bet = np.array(
            [
                self.data.loc[self.data["FTR"] == "D", "B365D"].mean(),
                self.data.loc[self.data["FTR"] == "H", "B365H"].mean(),
                self.data.loc[self.data["FTR"] == "A", "B365A"].mean(),
            ]
        )

        fair_odds = 100 / match_pct

        results = pd.DataFrame(
            data={
                "match_cnt": match_cnt,
                "match_pct": match_pct,
                "avg_odds_pin": avg_odds_pin,
                "avg_odds_bet": avg_odds_bet,
                "avg_winodds_pin": avg_winodds_pin,
                "avg_winodds_bet": avg_winodds_bet,
                "fair_odds": fair_odds,
            },
            index=df_idx,
        )
        return results

    def summary_goal_spread(self):
        """get the spread of goals in a match"""
        # num_of_matches = len(df.index)

        df_cols = ["match_cnt", "match_pct", "fair_odds"]
        results = {}
        for i in range(4):
            for j in range(4):
                match_cnt = len(
                    self.data[(self.data["FTHG"] == i) & (self.data["FTAG"] == j)].index
                )
                match_pct = match_cnt / self.num_of_matches * 100
                fair_odds = round(100 / match_pct, 2)
                score = f"{i}-{j}"
                results[score] = [match_cnt, match_pct, fair_odds]

        return_df = pd.DataFrame.from_dict(results, orient="index", columns=df_cols)
        # 4+ matches
        return_df.loc["4+", "match_cnt"] = (
            self.num_of_matches - return_df["match_cnt"].sum()
        )
        return_df.loc["4+", "match_pct"] = (
            return_df.loc["4+", "match_cnt"] / self.num_of_matches * 100
        )
        return_df.loc["4+", "fair_odds"] = round(
            100 / return_df.loc["4+", "match_pct"], 2
        )
        return_df.reset_index(inplace=True)
        return return_df

    def summary_goal_markets(self):
        """get the goal markets"""
        # num_of_matches = len(df.index)
        df_cols = ["match_cnt", "match_pct", "fair_odds"]
        results = {}
        for goal in np.arange(0.5, 5.5):

            match_cnt = len(
                self.data[(self.data["FTHG"] + self.data["FTAG"] < goal)].index
            )
            match_pct = match_cnt / self.num_of_matches * 100
            fair_odds = 100 / match_pct
            idx = f"Under {goal} goals"
            results[idx] = [match_cnt, match_pct, fair_odds]
            idx = f"Over {goal} goals"
            results[idx] = [
                self.num_of_matches - match_cnt,
                100 - match_pct,
                100 / (100 - match_pct),
            ]

        return_df = pd.DataFrame.from_dict(results, orient="index", columns=df_cols)
        return return_df

    def summary_stats(self):
        """get the stats of corners, shots, cards and fouls"""

        df_cols = [
            "corners_cnt",
            "corners_per_game",
            "corners_max",
            "corners_min",
            "shots_cnt",
            "shots_per_game",
            "shots_max",
            "shots_min",
            "shots_on_target_cnt",
            "shots_on_target_per_game",
            "shots_on_target_max",
            "shots_on_target_min",
            "yellow_cards_cnt",
            "yellow_cards_per_game",
            "yellow_cards_max",
            "yellow_cards_min",
            "red_cards_cnt",
            "red_cards_per_game",
            "red_cards_max",
            "red_cards_min",
            "fouls_cnt",
            "fouls_per_game",
            "fouls_max",
            "fouls_min",
        ]

        ### corners ####
        corners_cnt_h = self.data["HC"].sum()
        corners_cnt_a = self.data["AC"].sum()
        corners_cnt_t = (self.data["HC"] + self.data["AC"]).sum()
        corners_avg_h = round(self.data["HC"].mean(), 2)
        corners_avg_a = round(self.data["AC"].mean(), 2)
        corners_avg_t = round((self.data["HC"] + self.data["AC"]).mean(), 2)
        corners_max_h = self.data["HC"].max()
        corners_max_a = self.data["AC"].max()
        corners_max_t = (self.data["HC"] + self.data["AC"]).max()
        corners_min_h = self.data["HC"].min()
        corners_min_a = self.data["AC"].min()
        corners_min_t = (self.data["HC"] + self.data["AC"]).min()

        ### shots ####
        shots_cnt_h = self.data["HS"].sum()
        shots_cnt_a = self.data["AS"].sum()
        shots_cnt_t = (self.data["HS"] + self.data["AS"]).sum()
        shots_avg_h = round(self.data["HS"].mean(), 2)
        shots_avg_a = round(self.data["AS"].mean(), 2)
        shots_avg_t = round((self.data["HS"] + self.data["AS"]).mean(), 2)
        shots_max_h = self.data["HS"].max()
        shots_max_a = self.data["AS"].max()
        shots_max_t = (self.data["HS"] + self.data["AS"]).max()
        shots_min_h = self.data["HS"].min()
        shots_min_a = self.data["AS"].min()
        shots_min_t = (self.data["HS"] + self.data["AS"]).min()

        ##t shots on target ###
        shots_ot_cnt_h = self.data["HST"].sum()
        shots_ot_cnt_a = self.data["AST"].sum()
        shots_ot_cnt_t = (self.data["HST"] + self.data["AST"]).sum()
        shots_ot_avg_h = round(self.data["HST"].mean(), 2)
        shots_ot_avg_a = round(self.data["AST"].mean(), 2)
        shots_ot_avg_t = round((self.data["HST"] + self.data["AST"]).mean(), 2)
        shots_ot_max_h = self.data["HST"].max()
        shots_ot_max_a = self.data["AST"].max()
        shots_ot_max_t = (self.data["HST"] + self.data["AST"]).max()
        shots_ot_min_h = self.data["HST"].min()
        shots_ot_min_a = self.data["AST"].min()
        shots_ot_min_t = (self.data["HST"] + self.data["AST"]).min()

        ### yellow cards ###
        yellow_cards_cnt_h = self.data["HY"].sum()
        yellow_cards_cnt_a = self.data["AY"].sum()
        yellow_cards_cnt_t = (self.data["HY"] + self.data["AY"]).sum()
        yellow_cards_avg_h = round(self.data["HY"].mean(), 2)
        yellow_cards_avg_a = round(self.data["AY"].mean(), 2)
        yellow_cards_avg_t = round((self.data["HY"] + self.data["AY"]).mean(), 2)
        yellow_cards_max_h = self.data["HY"].max()
        yellow_cards_max_a = self.data["AY"].max()
        yellow_cards_max_t = (self.data["HY"] + self.data["AY"]).max()
        yellow_cards_min_h = self.data["HY"].min()
        yellow_cards_min_a = self.data["AY"].min()
        yellow_cards_min_t = (self.data["HY"] + self.data["AY"]).min()

        ### red cards ###
        red_cards_cnt_h = self.data["HR"].sum()
        red_cards_cnt_a = self.data["AR"].sum()
        red_cards_cnt_t = (self.data["HR"] + self.data["AR"]).sum()
        red_cards_avg_h = round(self.data["HR"].mean(), 2)
        red_cards_avg_a = round(self.data["AR"].mean(), 2)
        red_cards_avg_t = round((self.data["HR"] + self.data["AR"]).mean(), 2)
        red_cards_max_h = self.data["HR"].max()
        red_cards_max_a = self.data["AR"].max()
        red_cards_max_t = (self.data["HR"] + self.data["AR"]).max()
        red_cards_min_h = self.data["HR"].min()
        red_cards_min_a = self.data["AR"].min()
        red_cards_min_t = (self.data["HR"] + self.data["AR"]).min()

        ### fouls committed ###
        fouls_cnt_h = self.data["HF"].sum()
        fouls_cnt_a = self.data["AF"].sum()
        fouls_cnt_t = (self.data["HF"] + self.data["AF"]).sum()
        fouls_avg_h = round(self.data["HF"].mean(), 2)
        fouls_avg_a = round(self.data["AF"].mean(), 2)
        fouls_avg_t = round((self.data["HF"] + self.data["AF"]).mean(), 2)
        fouls_max_h = self.data["HF"].max()
        fouls_max_a = self.data["AF"].max()
        fouls_max_t = (self.data["HF"] + self.data["AF"]).max()
        fouls_min_h = self.data["HF"].min()
        fouls_min_a = self.data["AF"].min()
        fouls_min_t = (self.data["HF"] + self.data["AF"]).min()

        results = {}

        results["Home team"] = [
            corners_cnt_h,
            corners_avg_h,
            corners_max_h,
            corners_min_h,
            shots_cnt_h,
            shots_avg_h,
            shots_max_h,
            shots_min_h,
            shots_ot_cnt_h,
            shots_ot_avg_h,
            shots_ot_max_h,
            shots_ot_min_h,
            yellow_cards_cnt_h,
            yellow_cards_avg_h,
            yellow_cards_max_h,
            yellow_cards_min_h,
            red_cards_cnt_h,
            red_cards_avg_h,
            red_cards_max_h,
            red_cards_min_h,
            fouls_cnt_h,
            fouls_avg_h,
            fouls_max_h,
            fouls_min_h,
        ]

        results["Away team"] = [
            corners_cnt_a,
            corners_avg_a,
            corners_max_a,
            corners_min_a,
            shots_cnt_a,
            shots_avg_a,
            shots_max_a,
            shots_min_a,
            shots_ot_cnt_a,
            shots_ot_avg_a,
            shots_ot_max_a,
            shots_ot_min_a,
            yellow_cards_cnt_a,
            yellow_cards_avg_a,
            yellow_cards_max_a,
            yellow_cards_min_a,
            red_cards_cnt_a,
            red_cards_avg_a,
            red_cards_max_a,
            red_cards_min_a,
            fouls_cnt_a,
            fouls_avg_a,
            fouls_max_a,
            fouls_min_a,
        ]

        results["Total"] = [
            corners_cnt_t,
            corners_avg_t,
            corners_max_t,
            corners_min_t,
            shots_cnt_t,
            shots_avg_t,
            shots_max_t,
            shots_min_t,
            shots_ot_cnt_t,
            shots_ot_avg_t,
            shots_ot_max_t,
            shots_ot_min_t,
            yellow_cards_cnt_t,
            yellow_cards_avg_t,
            yellow_cards_max_t,
            yellow_cards_min_t,
            red_cards_cnt_t,
            red_cards_avg_t,
            red_cards_max_t,
            red_cards_min_t,
            fouls_cnt_t,
            fouls_avg_t,
            fouls_max_t,
            fouls_min_t,
        ]

        return_df = pd.DataFrame.from_dict(results, orient="index", columns=df_cols)
        return_df.reset_index(inplace=True)
        return return_df

    def calc_main_tables(self, table_type="overall"):
        """calculate the ranking table"""
        df = self.data

        cols = [
            "team",
            "played",
            "won",
            "draw",
            "lost",
            "goals_scored",
            "goals_conceded",
            "gd",
            "points",
            "goals_scored_pg",
            "goals_conceded_pg",
            "corners_for",
            "corners_against",
            "shots_made",
            "shots_allowed",
            "shots_to_score_a_goal",
            "shots_to_concede_a_goal",
            "yellow_cards",
            "red_cards_total",
            "fouls_commited",
            "fouls_suffered",
        ]

        results_home = {}
        results_away = {}
        results_overall = {}

        home_teams = df["HomeTeam"].unique().tolist()
        away_teams = df["AwayTeam"].unique().tolist()
        teams = list(set(home_teams + away_teams))

        # home table
        if table_type == "home" or table_type == "overall":
            for team in teams:
                team_df = df[df["HomeTeam"] == team]
                played = len(team_df.index)
                won = len(team_df[team_df["FTHG"] > team_df["FTAG"]].index)
                draw = len(team_df[team_df["FTHG"] == team_df["FTAG"]].index)
                lost = len(team_df[team_df["FTHG"] < team_df["FTAG"]].index)
                goals_scored = team_df["FTHG"].sum()
                goals_conceded = team_df["FTAG"].sum()
                gd = goals_scored - goals_conceded
                points = won * 3 + draw
                # additional stats per match
                goals_scored_pg = team_df["FTHG"].mean()
                goals_conceded_pg = team_df["FTAG"].mean()
                corners_for = team_df["HC"].mean()
                corners_against = team_df["AC"].mean()
                shots_made = team_df["HS"].mean()
                shots_allowed = team_df["AS"].mean()
                shots_to_score_a_goal = shots_made / goals_scored_pg
                shots_to_concede_a_goal = shots_allowed / goals_conceded_pg
                yellow_cards = team_df["HY"].mean()
                red_cards_total = team_df["HR"].sum()
                fouls_commited = team_df["HF"].mean()
                fouls_suffered = team_df["AF"].mean()
                results_home[team] = [
                    team,
                    played,
                    won,
                    draw,
                    lost,
                    goals_scored,
                    goals_conceded,
                    gd,
                    points,
                    goals_scored_pg,
                    goals_conceded_pg,
                    corners_for,
                    corners_against,
                    shots_made,
                    shots_allowed,
                    shots_to_score_a_goal,
                    shots_to_concede_a_goal,
                    yellow_cards,
                    red_cards_total,
                    fouls_commited,
                    fouls_suffered,
                ]

            df_home = pd.DataFrame.from_dict(results_home, orient="index", columns=cols)
            # rank teams by points, gd, goals_scored
            df_home["rank_points"] = (
                df_home["points"] * 1_000_000
                + df_home["gd"] * 1000
                + df_home["goals_scored"]
            )
            df_home["rank"] = (
                df_home["rank_points"].rank(method="dense", ascending=False).astype(int)
            )
            df_home.sort_values(by=["rank"], inplace=True)

        # away table
        if table_type == "away" or table_type == "overall":
            for team in teams:
                team_df = df[df["AwayTeam"] == team]
                played = len(team_df.index)
                won = len(team_df[team_df["FTHG"] < team_df["FTAG"]].index)
                draw = len(team_df[team_df["FTHG"] == team_df["FTAG"]].index)
                lost = len(team_df[team_df["FTHG"] > team_df["FTAG"]].index)
                goals_scored = team_df["FTAG"].sum()
                goals_conceded = team_df["FTHG"].sum()
                gd = goals_scored - goals_conceded
                points = won * 3 + draw
                # additional stats per match
                goals_scored_pg = team_df["FTAG"].mean()
                goals_conceded_pg = team_df["FTHG"].mean()
                corners_for = team_df["AC"].mean()
                corners_against = team_df["HC"].mean()
                shots_made = team_df["AS"].mean()
                shots_allowed = team_df["HS"].mean()
                shots_to_score_a_goal = shots_made / goals_scored_pg
                shots_to_concede_a_goal = shots_allowed / goals_conceded_pg
                yellow_cards = team_df["AY"].mean()
                red_cards_total = team_df["AR"].sum()
                fouls_commited = team_df["AF"].mean()
                fouls_suffered = team_df["HF"].mean()
                results_away[team] = [
                    team,
                    played,
                    won,
                    draw,
                    lost,
                    goals_scored,
                    goals_conceded,
                    gd,
                    points,
                    goals_scored_pg,
                    goals_conceded_pg,
                    corners_for,
                    corners_against,
                    shots_made,
                    shots_allowed,
                    shots_to_score_a_goal,
                    shots_to_concede_a_goal,
                    yellow_cards,
                    red_cards_total,
                    fouls_commited,
                    fouls_suffered,
                ]

            df_away = pd.DataFrame.from_dict(results_away, orient="index", columns=cols)
            # rank teams by points, gd, goals_scored
            df_away["rank_points"] = (
                df_away["points"] * 1_000_000
                + df_away["gd"] * 1000
                + df_away["goals_scored"]
            )
            df_away["rank"] = (
                df_away["rank_points"].rank(method="dense", ascending=False).astype(int)
            )
            df_away.sort_values(by=["rank"], inplace=True)

        # overall table
        if table_type == "overall":
            for team in teams:

                played = df_home.loc[team, "played"] + df_away.loc[team, "played"]
                won = df_home.loc[team, "won"] + df_away.loc[team, "won"]
                draw = df_home.loc[team, "draw"] + df_away.loc[team, "draw"]
                lost = df_home.loc[team, "lost"] + df_away.loc[team, "lost"]
                goals_scored = (
                    df_home.loc[team, "goals_scored"]
                    + df_away.loc[team, "goals_scored"]
                )
                goals_conceded = (
                    df_home.loc[team, "goals_conceded"]
                    + df_away.loc[team, "goals_conceded"]
                )
                gd = df_home.loc[team, "gd"] + df_away.loc[team, "gd"]
                points = won * 3 + draw
                # additional stats per match
                goals_scored_pg = (
                    df_home.loc[team, "goals_scored_pg"] * df_home.loc[team, "played"]
                    + df_away.loc[team, "goals_scored_pg"] * df_away.loc[team, "played"]
                ) / played
                goals_conceded_pg = (
                    df_home.loc[team, "goals_conceded_pg"] * df_home.loc[team, "played"]
                    + df_away.loc[team, "goals_conceded_pg"]
                    * df_away.loc[team, "played"]
                ) / played
                corners_for = (
                    df_home.loc[team, "corners_for"] * df_home.loc[team, "played"]
                    + df_away.loc[team, "corners_for"] * df_away.loc[team, "played"]
                ) / played
                corners_against = (
                    df_home.loc[team, "corners_against"] * df_home.loc[team, "played"]
                    + df_away.loc[team, "corners_against"] * df_away.loc[team, "played"]
                ) / played
                shots_made = (
                    df_home.loc[team, "shots_made"] * df_home.loc[team, "played"]
                    + df_away.loc[team, "shots_made"] * df_away.loc[team, "played"]
                ) / played
                shots_allowed = (
                    df_home.loc[team, "shots_allowed"] * df_home.loc[team, "played"]
                    + df_away.loc[team, "shots_allowed"] * df_away.loc[team, "played"]
                ) / played
                shots_to_score_a_goal = (
                    df_home.loc[team, "shots_to_score_a_goal"]
                    * df_home.loc[team, "played"]
                    + df_away.loc[team, "shots_to_score_a_goal"]
                    * df_away.loc[team, "played"]
                ) / played
                shots_to_concede_a_goal = (
                    df_home.loc[team, "shots_to_concede_a_goal"]
                    * df_home.loc[team, "played"]
                    + df_away.loc[team, "shots_to_concede_a_goal"]
                    * df_away.loc[team, "played"]
                ) / played
                yellow_cards = (
                    df_home.loc[team, "yellow_cards"] * df_home.loc[team, "played"]
                    + df_away.loc[team, "yellow_cards"] * df_away.loc[team, "played"]
                ) / played
                red_cards_total = (
                    df_home.loc[team, "red_cards_total"]
                    + df_away.loc[team, "red_cards_total"]
                )
                fouls_commited = (
                    df_home.loc[team, "fouls_commited"] * df_home.loc[team, "played"]
                    + df_away.loc[team, "fouls_commited"] * df_away.loc[team, "played"]
                ) / played
                fouls_suffered = (
                    df_home.loc[team, "fouls_suffered"] * df_home.loc[team, "played"]
                    + df_away.loc[team, "fouls_suffered"] * df_away.loc[team, "played"]
                ) / played
                results_overall[team] = [
                    team,
                    played,
                    won,
                    draw,
                    lost,
                    goals_scored,
                    goals_conceded,
                    gd,
                    points,
                    goals_scored_pg,
                    goals_conceded_pg,
                    corners_for,
                    corners_against,
                    shots_made,
                    shots_allowed,
                    shots_to_score_a_goal,
                    shots_to_concede_a_goal,
                    yellow_cards,
                    red_cards_total,
                    fouls_commited,
                    fouls_suffered,
                ]

            df_overall = pd.DataFrame.from_dict(
                results_overall, orient="index", columns=cols
            )
            # rank teams by points, gd, goals_scored
            df_overall["rank_points"] = (
                df_overall["points"] * 1_000_000
                + df_overall["gd"] * 1000
                + df_overall["goals_scored"]
            )
            df_overall["rank"] = (
                df_overall["rank_points"]
                .rank(method="dense", ascending=False)
                .astype(int)
            )
            df_overall.sort_values(by=["rank"], inplace=True)

        if table_type == "overall":
            return df_overall
        elif table_type == "home":
            return df_home
        elif table_type == "away":
            return df_away
        else:
            return 0

    def calc_team_stats(self, team):
        overall_main_tables = self.calc_main_tables("overall")
        home_main_tables = self.calc_main_tables("home")
        away_main_tables = self.calc_main_tables("away")
        dfs = {
            "Total": overall_main_tables,
            "Home": home_main_tables,
            "Away": away_main_tables,
        }
        cols = [
            "category",
            "mp",
            "win",
            "draw",
            "lost",
            "gs",
            "gc",
            "total_goals",
            "position",
            "points",
            "avg_points",
            "avg_gs",
            "avg_gc",
            "avg_goals",
            "corners_for",
            "corners_against",
            "corners_total",
            "shots_on_goal_f",
            "shots_on_goal_a",
            "fouls_commited",
            "fouls_suffered",
            "fouls_total",
        ]
        record = {}
        for row in ["Total", "Home", "Away"]:
            df = dfs[row]
            category = row
            mp = df.loc[team, "played"]
            win = df.loc[team, "won"]
            draw = df.loc[team, "draw"]
            lost = df.loc[team, "lost"]
            gs = df.loc[team, "goals_scored"]
            gc = df.loc[team, "goals_conceded"]
            total_goals = gs + gc
            position = df.loc[team, "rank"]
            points = df.loc[team, "points"]
            avg_points = points / mp
            avg_gs = df.loc[team, "goals_scored_pg"]
            avg_gc = df.loc[team, "goals_conceded_pg"]
            avg_goals = avg_gs + avg_gc
            corners_for = df.loc[team, "corners_for"]
            corners_against = df.loc[team, "corners_against"]
            corners_total = corners_for + corners_against
            shots_on_goal_f = df.loc[team, "shots_to_score_a_goal"]
            shots_on_goal_a = df.loc[team, "shots_to_concede_a_goal"]
            fouls_commited = df.loc[team, "fouls_commited"]
            fouls_suffered = df.loc[team, "fouls_suffered"]
            fouls_total = fouls_commited + fouls_suffered

            record[row] = [
                category,
                mp,
                win,
                draw,
                lost,
                gs,
                gc,
                total_goals,
                position,
                points,
                avg_points,
                avg_gs,
                avg_gc,
                avg_goals,
                corners_for,
                corners_against,
                corners_total,
                shots_on_goal_f,
                shots_on_goal_a,
                fouls_commited,
                fouls_suffered,
                fouls_total,
            ]

        results = pd.DataFrame.from_dict(record, orient="index", columns=cols)

        return results


def main():
    all_df = read_csv_data()
    # all_df = pd.read_csv("data/bet_data.csv", low_memory=False)
    # seasons = all_df.season.unique()
    # for season in seasons:
    #     summary = SeasonSummary(data=all_df, season=season)
    #     # print(get_result_matrix(df).head())
    #     print(f"printing season: {season}")
    #     print(summary.summary_stats())
    # print(summary.summary_goals())
    # print(summary.summary_goal_spread())
    # print(summary.summary_ft_results())
    # print(summary.summary_goal_markets())
    summary = SeasonSummary(data=all_df, season="19-20")
    print(summary.summary_goal_spread())


if __name__ == "__main__":
    main()
