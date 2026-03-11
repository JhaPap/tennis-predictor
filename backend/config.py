from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"

CSV_PATH = BASE_DIR.parent / "atp_tennis.csv"
DB_PATH = DATA_DIR / "tennis.db"

MATCHES_CLEAN_PATH = PROCESSED_DIR / "matches_clean.parquet"
ELO_RATINGS_PATH = PROCESSED_DIR / "elo_ratings.parquet"
CHARTING_STATS_PATH = PROCESSED_DIR / "charting_player_stats.parquet"
MODEL_PATH = MODELS_DIR / "xgboost_model.pkl"
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"

SERIES_MAP = {
    "International": "ATP250",
    "International Gold": "ATP500",
    "Masters": "Masters 1000",
    "Masters Cup": "Masters Cup",
    "Grand Slam": "Grand Slam",
    "ATP250": "ATP250",
    "ATP500": "ATP500",
    "Masters 1000": "Masters 1000",
}

K_FACTORS = {
    "Grand Slam": 32,
    "Masters 1000": 24,
    "Masters Cup": 20,
    "ATP500": 16,
    "ATP250": 10,
}

SERIES_TIER = {
    "ATP250": 1,
    "ATP500": 2,
    "Masters 1000": 3,
    "Masters Cup": 3,
    "Grand Slam": 4,
}

ROUND_ORDER = {
    "1st Round": 1,
    "2nd Round": 2,
    "3rd Round": 3,
    "4th Round": 4,
    "Round Robin": 4,
    "Quarterfinals": 5,
    "Semifinals": 6,
    "The Final": 7,
}

FEATURE_COLUMNS = [
    "elo_diff",
    "surface_elo_diff",
    "rank_diff",
    "log_rank_ratio",
    "pts_diff",
    "p1_winrate_overall",
    "p2_winrate_overall",
    "p1_winrate_surface",
    "p2_winrate_surface",
    "p1_winrate_last20",
    "p2_winrate_last20",
    "p1_winrate_last5",
    "p2_winrate_last5",
    "winrate_diff_overall",
    "winrate_diff_surface",
    "h2h_p1_wins",
    "h2h_total",
    "h2h_surface_p1_wins",
    "h2h_winrate_p1",
    "days_since_last_match_p1",
    "days_since_last_match_p2",
    "is_grand_slam",
    "is_best_of_5",
    "surface_hard",
    "surface_clay",
    "is_indoor",
    "round_encoded",
    "series_tier",
    "p1_matches_played_ytd",
    "p2_matches_played_ytd",
    "p1_surface_matches_played",
    "p2_surface_matches_played",
    "p1_tournament_winrate",
    "p2_tournament_winrate",
    "p1_tournament_matches",
    "p2_tournament_matches",
    "tournament_winrate_diff",
    # Serve & return stats (from Match Charting Project)
    "p1_ace_rate",
    "p2_ace_rate",
    "p1_df_rate",
    "p2_df_rate",
    "p1_first_serve_pct",
    "p2_first_serve_pct",
    "p1_first_serve_win_pct",
    "p2_first_serve_win_pct",
    "p1_return_win_pct",
    "p2_return_win_pct",
    # Serve/return matchup differentials
    "serve_edge",
    "return_edge",
    # Break-point clutch stats (Match Charting Project - KeyPoints files)
    "p1_bp_save_rate",
    "p2_bp_save_rate",
    "p1_bp_conversion_rate",
    "p2_bp_conversion_rate",
    # Net play (Match Charting Project - NetPoints file)
    "p1_net_win_rate",
    "p2_net_win_rate",
    # Shot quality (Match Charting Project - Rally file)
    "p1_ue_rate",
    "p2_ue_rate",
    "p1_winner_rate",
    "p2_winner_rate",
    # Break-point edge: server's save rate vs opponent's conversion rate
    "bp_edge",
]

import os as _os
_extra = _os.environ.get("CORS_ORIGINS", "")
CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"] + [
    o.strip() for o in _extra.split(",") if o.strip()
]
