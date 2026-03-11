"""
Step 3: Feature engineering with strict anti-leakage (no future data).
All rolling/cumulative stats use only matches BEFORE the current row.
Outputs: 47-feature matrix appended to the cleaned dataframe.
"""

import bisect
import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    MATCHES_CLEAN_PATH, PROCESSED_DIR, ROUND_ORDER, SERIES_TIER,
    FEATURE_COLUMNS, CHARTING_STATS_PATH,
)


_CHARTING_STAT_KEYS = [
    "ace_rate", "df_rate", "first_serve_pct",
    "first_serve_win_pct", "second_serve_win_pct", "return_win_pct",
    "bp_save_rate", "bp_conversion_rate", "net_win_rate",
    "ue_rate", "winner_rate",
]


def _load_charting_index(path: Path):
    """Load charting parquet and build {player_id: (sorted_dates, rows)} index.

    Returns (player_index, league_means) or (None, None) if file missing.
    """
    if not path.exists():
        return None, None

    df = pd.read_parquet(path)

    # Compute league means from latest snapshot per player
    # Guard against columns missing from the parquet (e.g. before re-running
    # pipeline.charting after adding new stat keys).
    latest = df.groupby("player_id").last().reset_index()
    means = {}
    for col in _CHARTING_STAT_KEYS:
        if col not in latest.columns:
            means[col] = np.nan  # filled by defaults loop below
        else:
            means[col] = float(latest[col].mean(skipna=True))

    # Fill any NaN means with sensible ATP averages
    defaults = {
        "ace_rate": 0.065,
        "df_rate": 0.048,
        "first_serve_pct": 0.615,
        "first_serve_win_pct": 0.745,
        "second_serve_win_pct": 0.535,
        "return_win_pct": 0.380,
        "bp_save_rate": 0.63,
        "bp_conversion_rate": 0.37,
        "net_win_rate": 0.52,
        "ue_rate": 0.15,
        "winner_rate": 0.20,
    }
    for k, v in defaults.items():
        if np.isnan(means.get(k, np.nan)):
            means[k] = v

    # Build per-player index: sorted list of (date, row_dict)
    # Only select columns that actually exist in the parquet.
    available_keys = [k for k in _CHARTING_STAT_KEYS if k in df.columns]
    player_index: dict[int, tuple[list, list]] = {}
    for pid, grp in df.groupby("player_id"):
        grp = grp.sort_values("date")
        dates = list(grp["date"])
        rows = grp[available_keys].to_dict("records")
        player_index[int(pid)] = (dates, rows)

    return player_index, means


def _get_charting_stats(player_id: int, before_date, player_index, means: dict) -> dict:
    """Return the most recent charting snapshot before `before_date`.

    Falls back to league means if no data available.
    """
    if player_index is None or player_id not in player_index:
        return dict(means)

    dates, rows = player_index[player_id]
    # bisect_left finds insertion point for before_date; idx-1 is the latest
    # snapshot strictly before before_date
    idx = bisect.bisect_left(dates, before_date)
    if idx == 0:
        return dict(means)

    row = rows[idx - 1]
    # Replace any NaN values with league means
    result = {}
    for k in _CHARTING_STAT_KEYS:
        v = row.get(k, np.nan)
        result[k] = means[k] if (v is None or np.isnan(v)) else v
    return result


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("Date").reset_index(drop=True)
    n = len(df)

    # Load charting stats (optional — gracefully absent during early pipeline runs)
    charting_index, charting_means = _load_charting_index(CHARTING_STATS_PATH)

    # Pre-allocate feature arrays
    features = {col: np.zeros(n, dtype=np.float64) for col in FEATURE_COLUMNS}

    # Running state (updated after each match, before processing next)
    player_wins: dict[int, int] = {}
    player_matches: dict[int, int] = {}
    surface_wins: dict[tuple, int] = {}
    surface_matches: dict[tuple, int] = {}
    last20_results: dict[int, list] = {}
    last5_results: dict[int, list] = {}
    last_match_date: dict[int, pd.Timestamp] = {}
    ytd_matches: dict[tuple, int] = {}      # (player_id, year) → count
    h2h_wins: dict[tuple, int] = {}         # (p1, p2) → p1 wins vs p2
    h2h_total: dict[tuple, int] = {}        # (p1, p2) sorted → total
    h2h_surface_wins: dict[tuple, int] = {} # (p1, p2, surface) → p1 wins
    tournament_wins: dict[tuple, int] = {}    # (player_id, tournament_name) → wins
    tournament_matches: dict[tuple, int] = {} # (player_id, tournament_name) → total

    def get_winrate(pid, wins_dict, matches_dict):
        m = matches_dict.get(pid, 0)
        if m == 0:
            return 0.5
        return wins_dict.get(pid, 0) / m

    def get_surface_winrate(pid, surface, s_wins, s_matches):
        key = (pid, surface)
        m = s_matches.get(key, 0)
        if m == 0:
            return 0.5
        return s_wins.get(key, 0) / m

    def get_tournament_winrate(pid, tournament, surface):
        """Tournament-specific winrate, falling back to surface winrate when no history."""
        key = (pid, tournament)
        m = tournament_matches.get(key, 0)
        if m == 0:
            return get_surface_winrate(pid, surface, surface_wins, surface_matches)
        return tournament_wins.get(key, 0) / m

    def get_last_n_winrate(pid, results_dict):
        results = results_dict.get(pid, [])
        if not results:
            return 0.5
        return sum(results) / len(results)

    def get_h2h(p1, p2):
        key = (min(p1, p2), max(p1, p2))
        total = h2h_total.get(key, 0)
        p1_wins = h2h_wins.get((p1, p2), 0)
        return p1_wins, total

    def get_h2h_surface(p1, p2, surface):
        return h2h_surface_wins.get((p1, p2, surface), 0)

    def get_days_since_last_match(pid, current_date):
        last_date = last_match_date.get(pid)
        if last_date is None:
            return np.log1p(30)  # default ~30 days if no history
        days = (current_date - last_date).days
        days = max(days, 0)
        return np.log1p(days)

    for i, row in df.iterrows():
        p1 = int(row["player1_id"])
        p2 = int(row["player2_id"])
        surface = str(row["Surface"])
        series = str(row["Series"])
        year = row["Date"].year
        current_date = row["Date"]

        # --- ELO features ---
        e1 = row["elo_p1_before"]
        e2 = row["elo_p2_before"]
        es1 = row["elo_surface_p1_before"]
        es2 = row["elo_surface_p2_before"]
        features["elo_diff"][i] = e1 - e2
        features["surface_elo_diff"][i] = es1 - es2

        # --- Ranking features ---
        r1 = row["Rank_1"]
        r2 = row["Rank_2"]
        if pd.notna(r1) and pd.notna(r2) and r1 > 0 and r2 > 0:
            features["rank_diff"][i] = r2 - r1
            features["log_rank_ratio"][i] = np.log(r2 / r1)
        else:
            features["rank_diff"][i] = 0.0
            features["log_rank_ratio"][i] = 0.0

        pts1 = row.get("Pts_1", np.nan)
        pts2 = row.get("Pts_2", np.nan)
        if pd.notna(pts1) and pd.notna(pts2):
            features["pts_diff"][i] = float(pts1) - float(pts2)
        else:
            features["pts_diff"][i] = 0.0

        # --- Win rate features (using state BEFORE this match) ---
        p1_wr_overall = get_winrate(p1, player_wins, player_matches)
        p2_wr_overall = get_winrate(p2, player_wins, player_matches)
        p1_wr_surface = get_surface_winrate(p1, surface, surface_wins, surface_matches)
        p2_wr_surface = get_surface_winrate(p2, surface, surface_wins, surface_matches)

        features["p1_winrate_overall"][i] = p1_wr_overall
        features["p2_winrate_overall"][i] = p2_wr_overall
        features["p1_winrate_surface"][i] = p1_wr_surface
        features["p2_winrate_surface"][i] = p2_wr_surface
        features["p1_winrate_last20"][i] = get_last_n_winrate(p1, last20_results)
        features["p2_winrate_last20"][i] = get_last_n_winrate(p2, last20_results)
        features["p1_winrate_last5"][i] = get_last_n_winrate(p1, last5_results)
        features["p2_winrate_last5"][i] = get_last_n_winrate(p2, last5_results)

        # --- Diff features ---
        features["winrate_diff_overall"][i] = p1_wr_overall - p2_wr_overall
        features["winrate_diff_surface"][i] = p1_wr_surface - p2_wr_surface

        # --- H2H features ---
        h2h_p1_wins, h2h_t = get_h2h(p1, p2)
        features["h2h_p1_wins"][i] = h2h_p1_wins
        features["h2h_total"][i] = h2h_t
        features["h2h_surface_p1_wins"][i] = get_h2h_surface(p1, p2, surface)
        features["h2h_winrate_p1"][i] = (h2h_p1_wins / h2h_t) if h2h_t > 0 else 0.5

        # --- Days since last match ---
        features["days_since_last_match_p1"][i] = get_days_since_last_match(p1, current_date)
        features["days_since_last_match_p2"][i] = get_days_since_last_match(p2, current_date)

        # --- Match context features ---
        features["is_grand_slam"][i] = float(row["is_grand_slam"])
        features["is_best_of_5"][i] = float(row["is_best_of_5"])
        features["surface_hard"][i] = 1.0 if surface == "Hard" else 0.0
        features["surface_clay"][i] = 1.0 if surface == "Clay" else 0.0
        features["is_indoor"][i] = float(row["is_indoor"])
        features["round_encoded"][i] = float(ROUND_ORDER.get(str(row["Round"]), 1))
        features["series_tier"][i] = float(SERIES_TIER.get(series, 1))

        # --- Volume features ---
        features["p1_matches_played_ytd"][i] = float(ytd_matches.get((p1, year), 0))
        features["p2_matches_played_ytd"][i] = float(ytd_matches.get((p2, year), 0))
        features["p1_surface_matches_played"][i] = float(surface_matches.get((p1, surface), 0))
        features["p2_surface_matches_played"][i] = float(surface_matches.get((p2, surface), 0))

        # --- Tournament-specific features ---
        tournament = str(row["Tournament"])
        p1_tourn_wr = get_tournament_winrate(p1, tournament, surface)
        p2_tourn_wr = get_tournament_winrate(p2, tournament, surface)
        features["p1_tournament_winrate"][i] = p1_tourn_wr
        features["p2_tournament_winrate"][i] = p2_tourn_wr
        features["p1_tournament_matches"][i] = float(tournament_matches.get((p1, tournament), 0))
        features["p2_tournament_matches"][i] = float(tournament_matches.get((p2, tournament), 0))
        features["tournament_winrate_diff"][i] = p1_tourn_wr - p2_tourn_wr

        # --- Serve & return features (Match Charting Project) ---
        p1_chart = _get_charting_stats(p1, current_date, charting_index, charting_means or {})
        p2_chart = _get_charting_stats(p2, current_date, charting_index, charting_means or {})
        features["p1_ace_rate"][i]              = p1_chart.get("ace_rate", 0.065)
        features["p2_ace_rate"][i]              = p2_chart.get("ace_rate", 0.065)
        features["p1_df_rate"][i]               = p1_chart.get("df_rate", 0.048)
        features["p2_df_rate"][i]               = p2_chart.get("df_rate", 0.048)
        features["p1_first_serve_pct"][i]       = p1_chart.get("first_serve_pct", 0.615)
        features["p2_first_serve_pct"][i]       = p2_chart.get("first_serve_pct", 0.615)
        features["p1_first_serve_win_pct"][i]   = p1_chart.get("first_serve_win_pct", 0.683)
        features["p2_first_serve_win_pct"][i]   = p2_chart.get("first_serve_win_pct", 0.683)
        features["p1_return_win_pct"][i]        = p1_chart.get("return_win_pct", 0.337)
        features["p2_return_win_pct"][i]        = p2_chart.get("return_win_pct", 0.337)
        # Serve/return matchup differentials
        features["serve_edge"][i]  = features["p1_first_serve_win_pct"][i] - features["p2_return_win_pct"][i]
        features["return_edge"][i] = features["p1_return_win_pct"][i] - features["p2_first_serve_win_pct"][i]

        # --- Break-point clutch features ---
        features["p1_bp_save_rate"][i]       = p1_chart.get("bp_save_rate", 0.63)
        features["p2_bp_save_rate"][i]       = p2_chart.get("bp_save_rate", 0.63)
        features["p1_bp_conversion_rate"][i] = p1_chart.get("bp_conversion_rate", 0.37)
        features["p2_bp_conversion_rate"][i] = p2_chart.get("bp_conversion_rate", 0.37)
        # --- Net play features ---
        features["p1_net_win_rate"][i]       = p1_chart.get("net_win_rate", 0.52)
        features["p2_net_win_rate"][i]       = p2_chart.get("net_win_rate", 0.52)
        # --- Shot quality features ---
        features["p1_ue_rate"][i]            = p1_chart.get("ue_rate", 0.15)
        features["p2_ue_rate"][i]            = p2_chart.get("ue_rate", 0.15)
        features["p1_winner_rate"][i]        = p1_chart.get("winner_rate", 0.20)
        features["p2_winner_rate"][i]        = p2_chart.get("winner_rate", 0.20)
        # Break-point edge: p1's ability to save vs p2's ability to convert
        features["bp_edge"][i] = features["p1_bp_save_rate"][i] - features["p2_bp_conversion_rate"][i]

        # --- Update state AFTER recording features (anti-leakage) ---
        p1_won = int(row["p1_won"])
        p2_won = 1 - p1_won

        # Overall stats
        player_wins[p1] = player_wins.get(p1, 0) + p1_won
        player_wins[p2] = player_wins.get(p2, 0) + p2_won
        player_matches[p1] = player_matches.get(p1, 0) + 1
        player_matches[p2] = player_matches.get(p2, 0) + 1

        # Surface stats
        surface_wins[(p1, surface)] = surface_wins.get((p1, surface), 0) + p1_won
        surface_wins[(p2, surface)] = surface_wins.get((p2, surface), 0) + p2_won
        surface_matches[(p1, surface)] = surface_matches.get((p1, surface), 0) + 1
        surface_matches[(p2, surface)] = surface_matches.get((p2, surface), 0) + 1

        # Last 20
        if p1 not in last20_results:
            last20_results[p1] = []
        if p2 not in last20_results:
            last20_results[p2] = []
        last20_results[p1].append(p1_won)
        last20_results[p2].append(p2_won)
        if len(last20_results[p1]) > 20:
            last20_results[p1].pop(0)
        if len(last20_results[p2]) > 20:
            last20_results[p2].pop(0)

        # Last 5
        if p1 not in last5_results:
            last5_results[p1] = []
        if p2 not in last5_results:
            last5_results[p2] = []
        last5_results[p1].append(p1_won)
        last5_results[p2].append(p2_won)
        if len(last5_results[p1]) > 5:
            last5_results[p1].pop(0)
        if len(last5_results[p2]) > 5:
            last5_results[p2].pop(0)

        # Last match date
        last_match_date[p1] = current_date
        last_match_date[p2] = current_date

        # YTD matches
        ytd_matches[(p1, year)] = ytd_matches.get((p1, year), 0) + 1
        ytd_matches[(p2, year)] = ytd_matches.get((p2, year), 0) + 1

        # H2H
        h2h_key = (min(p1, p2), max(p1, p2))
        h2h_total[h2h_key] = h2h_total.get(h2h_key, 0) + 1
        if p1_won:
            h2h_wins[(p1, p2)] = h2h_wins.get((p1, p2), 0) + 1
        else:
            h2h_wins[(p2, p1)] = h2h_wins.get((p2, p1), 0) + 1
        surface_key = (p1, p2, surface) if p1_won else (p2, p1, surface)
        h2h_surface_wins[surface_key] = h2h_surface_wins.get(surface_key, 0) + 1

        # Tournament stats
        tournament_wins[(p1, tournament)] = tournament_wins.get((p1, tournament), 0) + p1_won
        tournament_wins[(p2, tournament)] = tournament_wins.get((p2, tournament), 0) + p2_won
        tournament_matches[(p1, tournament)] = tournament_matches.get((p1, tournament), 0) + 1
        tournament_matches[(p2, tournament)] = tournament_matches.get((p2, tournament), 0) + 1

    # Attach feature columns to df
    for col, arr in features.items():
        df[col] = arr

    return df


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading Elo-enriched matches...")
    df = pd.read_parquet(MATCHES_CLEAN_PATH)
    print(f"  {len(df):,} matches")

    print("Building feature matrix...")
    df_feat = build_feature_matrix(df)

    # Verify no NaN in feature columns
    null_counts = df_feat[FEATURE_COLUMNS].isnull().sum()
    if null_counts.any():
        print("WARNING: NaN values in features:")
        print(null_counts[null_counts > 0])
    else:
        print(f"  All {len(FEATURE_COLUMNS)} feature columns complete (no NaN)")

    print(f"  Feature stats:\n{df_feat[FEATURE_COLUMNS].describe().T[['mean','std','min','max']].to_string()}")

    df_feat.to_parquet(MATCHES_CLEAN_PATH, index=False)
    print(f"Saved → {MATCHES_CLEAN_PATH}")


if __name__ == "__main__":
    main()
