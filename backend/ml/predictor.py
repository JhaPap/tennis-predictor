"""
Inference wrapper: loads the trained model and builds feature vectors
for hypothetical matchups (no future data, uses current player state from DB).
"""

import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    MODEL_PATH, MODEL_METADATA_PATH, FEATURE_COLUMNS,
    ROUND_ORDER, SERIES_TIER, CHARTING_STATS_PATH,
)

_model = None
_metadata = None
_charting_stats: Optional[dict] = None   # {player_id: latest_stats_dict}
_charting_means: Optional[dict] = None   # league-mean fallback values

_CHARTING_STAT_KEYS = [
    "ace_rate", "df_rate", "first_serve_pct",
    "first_serve_win_pct", "second_serve_win_pct", "return_win_pct",
    "bp_save_rate", "bp_conversion_rate", "net_win_rate",
    "ue_rate", "winner_rate",
]
_CHARTING_DEFAULTS = {
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


def load_model():
    global _model, _metadata
    if _model is None:
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
        with open(MODEL_METADATA_PATH) as f:
            _metadata = json.load(f)
    return _model, _metadata


def _load_charting():
    """Lazy-load charting stats; returns (player_latest_dict, means_dict)."""
    global _charting_stats, _charting_means

    if _charting_stats is not None:
        return _charting_stats, _charting_means

    if not CHARTING_STATS_PATH.exists():
        _charting_stats = {}
        _charting_means = dict(_CHARTING_DEFAULTS)
        return _charting_stats, _charting_means

    df = pd.read_parquet(CHARTING_STATS_PATH)

    # Compute league means from the latest snapshot per player
    # Guard against columns that don't exist yet in the parquet (e.g. before
    # pipeline.charting is re-run after adding new stat keys).
    latest_all = df.groupby("player_id").last().reset_index()
    means = {}
    for col in _CHARTING_STAT_KEYS:
        if col not in latest_all.columns:
            means[col] = _CHARTING_DEFAULTS.get(col, np.nan)
        else:
            val = float(latest_all[col].mean(skipna=True))
            means[col] = val if not np.isnan(val) else _CHARTING_DEFAULTS.get(col, np.nan)
    _charting_means = means

    # For each player, take the most recent snapshot (used for future predictions)
    _charting_stats = {}
    for pid, grp in df.groupby("player_id"):
        last_row = grp.sort_values("date").iloc[-1]
        row_dict = {}
        for k in _CHARTING_STAT_KEYS:
            if k not in last_row.index:
                row_dict[k] = means[k]
            else:
                v = float(last_row.get(k, np.nan))
                row_dict[k] = means[k] if np.isnan(v) else v
        _charting_stats[int(pid)] = row_dict

    return _charting_stats, _charting_means


def compute_serve_stats(player_id: int) -> dict:
    """Return charting serve/return stats for a player, or league means."""
    stats, means = _load_charting()
    return stats.get(player_id, dict(means))


def get_surface_elo(player, surface: str) -> float:
    surface_map = {
        "Hard": player.elo_hard,
        "Clay": player.elo_clay,
        "Grass": player.elo_grass,
    }
    return surface_map.get(surface, player.elo_overall)


def get_surface_winrate(player, surface: str) -> float:
    surface_map = {
        "Hard": player.win_rate_hard,
        "Clay": player.win_rate_clay,
        "Grass": player.win_rate_grass,
    }
    return surface_map.get(surface, player.win_rate_overall)


def get_surface_matches(player, surface: str) -> int:
    surface_map = {
        "Hard": player.matches_hard,
        "Clay": player.matches_clay,
        "Grass": player.matches_grass,
    }
    return surface_map.get(surface, 0)


def compute_h2h(db, p1_id: int, p2_id: int, surface: Optional[str] = None):
    from db.models import Match
    from sqlalchemy import or_, and_

    query = db.query(Match).filter(
        or_(
            and_(Match.player1_id == p1_id, Match.player2_id == p2_id),
            and_(Match.player1_id == p2_id, Match.player2_id == p1_id),
        )
    )
    matches = query.all()

    p1_wins = 0
    total = len(matches)
    p1_surface_wins = 0
    surface_total = 0

    for m in matches:
        won = m.winner_id == p1_id
        if won:
            p1_wins += 1
        if surface and m.surface == surface:
            surface_total += 1
            if won:
                p1_surface_wins += 1

    return {
        "p1_wins": p1_wins,
        "p2_wins": total - p1_wins,
        "total": total,
        "surface_p1_wins": p1_surface_wins,
        "surface_total": surface_total,
    }


def compute_player_form(db, player_id: int):
    """Query the Match table for a player's recent form stats.

    Returns a dict with last20_winrate, last5_winrate, ytd_matches,
    days_since_last_match (log-scaled).
    """
    from db.models import Match
    from sqlalchemy import or_, desc

    # Get last 20 matches ordered by date desc
    recent_matches = (
        db.query(Match)
        .filter(or_(Match.player1_id == player_id, Match.player2_id == player_id))
        .order_by(desc(Match.date))
        .limit(20)
        .all()
    )

    last20_wins = 0
    last5_wins = 0
    last20_count = len(recent_matches)
    last5_count = min(5, last20_count)

    for idx, m in enumerate(recent_matches):
        won = m.winner_id == player_id
        if won:
            last20_wins += 1
            if idx < 5:
                last5_wins += 1

    last20_winrate = last20_wins / last20_count if last20_count > 0 else 0.5
    last5_winrate = last5_wins / last5_count if last5_count > 0 else 0.5

    # YTD matches
    current_year = datetime.now().year
    ytd_count = (
        db.query(Match)
        .filter(
            or_(Match.player1_id == player_id, Match.player2_id == player_id),
            Match.date >= date(current_year, 1, 1),
        )
        .count()
    )

    # Days since last match
    if recent_matches:
        last_date = recent_matches[0].date
        if isinstance(last_date, datetime):
            last_date = last_date.date()
        days_since = (date.today() - last_date).days
        days_since = max(days_since, 0)
    else:
        days_since = 30  # default

    return {
        "last20_winrate": last20_winrate,
        "last5_winrate": last5_winrate,
        "ytd_matches": ytd_count,
        "days_since_last_match": np.log1p(days_since),
    }


def compute_tournament_stats(db, player_id: int, tournament: Optional[str], surface: str):
    """Query Match table for player's record at a specific tournament.

    Returns {"winrate": float, "matches": int}. Falls back to surface winrate
    sentinel when tournament is None/empty or player has no history there.
    """
    if not tournament:
        return {"winrate": None, "matches": 0}

    from db.models import Match
    from sqlalchemy import or_

    matches = (
        db.query(Match)
        .filter(
            or_(Match.player1_id == player_id, Match.player2_id == player_id),
            Match.tournament == tournament,
        )
        .all()
    )

    total = len(matches)
    if total == 0:
        return {"winrate": None, "matches": 0}

    wins = sum(1 for m in matches if m.winner_id == player_id)
    return {"winrate": wins / total, "matches": total}


def build_feature_vector(db, p1, p2, h2h_data: dict, surface: str, series: str,
                         round_name: str, best_of: int,
                         tournament: Optional[str] = None) -> np.ndarray:
    """
    Build the same 37-feature vector used at training time,
    using real DB queries for rolling stats.
    """
    e1 = p1.elo_overall
    e2 = p2.elo_overall
    es1 = get_surface_elo(p1, surface)
    es2 = get_surface_elo(p2, surface)

    r1 = p1.current_rank or 500
    r2 = p2.current_rank or 500
    r1 = max(r1, 1)
    r2 = max(r2, 1)

    pts1 = p1.current_pts or 0.0
    pts2 = p2.current_pts or 0.0

    # Real DB queries for rolling stats (fixes training/inference mismatch)
    p1_form = compute_player_form(db, p1.id)
    p2_form = compute_player_form(db, p2.id)

    p1_wr_overall = p1.win_rate_overall
    p2_wr_overall = p2.win_rate_overall
    p1_wr_surface = get_surface_winrate(p1, surface)
    p2_wr_surface = get_surface_winrate(p2, surface)

    # H2H winrate
    h2h_total = h2h_data["total"]
    h2h_p1_wins = h2h_data["p1_wins"]
    h2h_winrate_p1 = (h2h_p1_wins / h2h_total) if h2h_total > 0 else 0.5

    features = {
        "elo_diff": e1 - e2,
        "surface_elo_diff": es1 - es2,
        "rank_diff": r2 - r1,
        "log_rank_ratio": float(np.log(r2 / r1)) if r1 > 0 and r2 > 0 else 0.0,
        "pts_diff": pts1 - pts2,
        "p1_winrate_overall": p1_wr_overall,
        "p2_winrate_overall": p2_wr_overall,
        "p1_winrate_surface": p1_wr_surface,
        "p2_winrate_surface": p2_wr_surface,
        "p1_winrate_last20": p1_form["last20_winrate"],
        "p2_winrate_last20": p2_form["last20_winrate"],
        "p1_winrate_last5": p1_form["last5_winrate"],
        "p2_winrate_last5": p2_form["last5_winrate"],
        "winrate_diff_overall": p1_wr_overall - p2_wr_overall,
        "winrate_diff_surface": p1_wr_surface - p2_wr_surface,
        "h2h_p1_wins": float(h2h_p1_wins),
        "h2h_total": float(h2h_total),
        "h2h_surface_p1_wins": float(h2h_data["surface_p1_wins"]),
        "h2h_winrate_p1": h2h_winrate_p1,
        "days_since_last_match_p1": p1_form["days_since_last_match"],
        "days_since_last_match_p2": p2_form["days_since_last_match"],
        "is_grand_slam": 1.0 if series == "Grand Slam" else 0.0,
        "is_best_of_5": 1.0 if best_of == 5 else 0.0,
        "surface_hard": 1.0 if surface == "Hard" else 0.0,
        "surface_clay": 1.0 if surface == "Clay" else 0.0,
        "is_indoor": 0.0,
        "round_encoded": float(ROUND_ORDER.get(round_name, 1)),
        "series_tier": float(SERIES_TIER.get(series, 1)),
        "p1_matches_played_ytd": float(p1_form["ytd_matches"]),
        "p2_matches_played_ytd": float(p2_form["ytd_matches"]),
        "p1_surface_matches_played": float(get_surface_matches(p1, surface)),
        "p2_surface_matches_played": float(get_surface_matches(p2, surface)),
    }

    # --- Tournament-specific features ---
    p1_tourn = compute_tournament_stats(db, p1.id, tournament, surface)
    p2_tourn = compute_tournament_stats(db, p2.id, tournament, surface)
    p1_tourn_wr = p1_tourn["winrate"] if p1_tourn["winrate"] is not None else p1_wr_surface
    p2_tourn_wr = p2_tourn["winrate"] if p2_tourn["winrate"] is not None else p2_wr_surface
    features["p1_tournament_winrate"] = p1_tourn_wr
    features["p2_tournament_winrate"] = p2_tourn_wr
    features["p1_tournament_matches"] = float(p1_tourn["matches"])
    features["p2_tournament_matches"] = float(p2_tourn["matches"])
    features["tournament_winrate_diff"] = p1_tourn_wr - p2_tourn_wr

    # --- Serve & return features (Match Charting Project) ---
    p1_chart = compute_serve_stats(p1.id)
    p2_chart = compute_serve_stats(p2.id)
    features["p1_ace_rate"]            = p1_chart["ace_rate"]
    features["p2_ace_rate"]            = p2_chart["ace_rate"]
    features["p1_df_rate"]             = p1_chart["df_rate"]
    features["p2_df_rate"]             = p2_chart["df_rate"]
    features["p1_first_serve_pct"]     = p1_chart["first_serve_pct"]
    features["p2_first_serve_pct"]     = p2_chart["first_serve_pct"]
    features["p1_first_serve_win_pct"] = p1_chart["first_serve_win_pct"]
    features["p2_first_serve_win_pct"] = p2_chart["first_serve_win_pct"]
    features["p1_return_win_pct"]      = p1_chart["return_win_pct"]
    features["p2_return_win_pct"]      = p2_chart["return_win_pct"]
    features["serve_edge"]  = features["p1_first_serve_win_pct"] - features["p2_return_win_pct"]
    features["return_edge"] = features["p1_return_win_pct"] - features["p2_first_serve_win_pct"]

    # --- Break-point clutch features ---
    features["p1_bp_save_rate"]       = p1_chart.get("bp_save_rate", 0.63)
    features["p2_bp_save_rate"]       = p2_chart.get("bp_save_rate", 0.63)
    features["p1_bp_conversion_rate"] = p1_chart.get("bp_conversion_rate", 0.37)
    features["p2_bp_conversion_rate"] = p2_chart.get("bp_conversion_rate", 0.37)
    # --- Net play features ---
    features["p1_net_win_rate"]       = p1_chart.get("net_win_rate", 0.52)
    features["p2_net_win_rate"]       = p2_chart.get("net_win_rate", 0.52)
    # --- Shot quality features ---
    features["p1_ue_rate"]            = p1_chart.get("ue_rate", 0.15)
    features["p2_ue_rate"]            = p2_chart.get("ue_rate", 0.15)
    features["p1_winner_rate"]        = p1_chart.get("winner_rate", 0.20)
    features["p2_winner_rate"]        = p2_chart.get("winner_rate", 0.20)
    # Break-point edge: p1's ability to save vs p2's ability to convert
    features["bp_edge"] = features["p1_bp_save_rate"] - features["p2_bp_conversion_rate"]

    return np.array([features[col] for col in FEATURE_COLUMNS], dtype=np.float64)


def compute_confidence(p1, p2, h2h_data: dict, win_prob: float) -> str:
    score = 0
    if p1.matches_played > 100:
        score += 1
    if p2.matches_played > 100:
        score += 1
    if h2h_data["total"] > 5:
        score += 1
    if abs(p1.elo_overall - p2.elo_overall) > 100:
        score += 1
    if p1.matches_played > 30 and p2.matches_played > 30:
        score += 1

    if score >= 4:
        data_level = "high"
    elif score >= 2:
        data_level = "medium"
    else:
        data_level = "low"

    # Cap confidence based on prediction margin — a near-coin-flip
    # should never report high confidence regardless of data quality.
    margin = abs(win_prob - 0.5)
    if margin < 0.05:
        return "low"
    if margin < 0.12:
        return "low" if data_level == "low" else "medium"
    return data_level


def _df_for_model(feature_vector: np.ndarray, metadata: dict) -> pd.DataFrame:
    """Build a DataFrame with exactly the columns the model was trained on.

    Uses metadata["feature_columns"] as the source of truth so that adding
    new entries to FEATURE_COLUMNS doesn't break an already-trained model.
    """
    model_cols = metadata.get("feature_columns", FEATURE_COLUMNS)
    feat_dict = dict(zip(FEATURE_COLUMNS, feature_vector))
    vals = [feat_dict.get(c, 0.0) for c in model_cols]
    return pd.DataFrame([vals], columns=model_cols)


def format_key_factors(feature_vector: np.ndarray, p1_name: str, p2_name: str) -> list[dict]:
    """Return top 5 most influential features in human-readable form."""
    factors = []
    feat_dict = dict(zip(FEATURE_COLUMNS, feature_vector))

    elo_diff = feat_dict.get("elo_diff", 0)
    if abs(elo_diff) > 0:
        factors.append({
            "feature": "Elo Rating Advantage",
            "p1_value": round(float(feat_dict.get("elo_diff", 0) + 1500), 0),
            "p2_value": round(1500.0, 0),
            "advantage": p1_name if elo_diff > 0 else p2_name,
            "margin": round(abs(elo_diff), 0),
        })

    surf_elo_diff = feat_dict.get("surface_elo_diff", 0)
    if abs(surf_elo_diff) > 10:
        factors.append({
            "feature": "Surface Elo Advantage",
            "p1_value": round(float(surf_elo_diff + 1500), 0),
            "p2_value": round(1500.0, 0),
            "advantage": p1_name if surf_elo_diff > 0 else p2_name,
            "margin": round(abs(surf_elo_diff), 0),
        })

    p1_wr = feat_dict.get("p1_winrate_surface", 0.5)
    p2_wr = feat_dict.get("p2_winrate_surface", 0.5)
    factors.append({
        "feature": "Surface Win Rate",
        "p1_value": f"{p1_wr*100:.1f}%",
        "p2_value": f"{p2_wr*100:.1f}%",
        "advantage": p1_name if p1_wr > p2_wr else p2_name,
        "margin": round(abs(p1_wr - p2_wr) * 100, 1),
    })

    rank_diff = feat_dict.get("rank_diff", 0)
    if abs(rank_diff) > 0:
        factors.append({
            "feature": "ATP Ranking",
            "p1_value": int(feat_dict.get("rank_diff", 0) * -1 + 250),
            "p2_value": 250,
            "advantage": p1_name if rank_diff > 0 else p2_name,
            "margin": int(abs(rank_diff)),
        })

    p1_tourn_matches = feat_dict.get("p1_tournament_matches", 0)
    p2_tourn_matches = feat_dict.get("p2_tournament_matches", 0)
    if p1_tourn_matches >= 3 or p2_tourn_matches >= 3:
        p1_twr = feat_dict.get("p1_tournament_winrate", 0.5)
        p2_twr = feat_dict.get("p2_tournament_winrate", 0.5)
        factors.append({
            "feature": "Tournament Win Rate",
            "p1_value": f"{p1_twr*100:.1f}%",
            "p2_value": f"{p2_twr*100:.1f}%",
            "advantage": p1_name if p1_twr > p2_twr else p2_name,
            "margin": round(abs(p1_twr - p2_twr) * 100, 1),
        })

    h2h_wins = feat_dict.get("h2h_p1_wins", 0)
    h2h_total = feat_dict.get("h2h_total", 0)
    if h2h_total > 0:
        factors.append({
            "feature": "Head to Head",
            "p1_value": f"{int(h2h_wins)}-{int(h2h_total - h2h_wins)}",
            "p2_value": f"{int(h2h_total - h2h_wins)}-{int(h2h_wins)}",
            "advantage": p1_name if h2h_wins > h2h_total / 2 else p2_name if h2h_wins < h2h_total / 2 else "Even",
            "margin": int(abs(h2h_wins - (h2h_total - h2h_wins))),
        })

    return factors[:5]


def get_match_analysis(db, player1_id: int, player2_id: int, surface: str,
                       series: str, round_name: str, best_of: int,
                       tournament: Optional[str] = None) -> Optional[str]:
    """Build a feature vector and call the LLM to generate a match analysis."""
    from db.models import Player
    from ml.llm_analysis import generate_match_analysis

    model, metadata = load_model()

    p1 = db.query(Player).get(player1_id)
    p2 = db.query(Player).get(player2_id)
    if not p1 or not p2:
        raise ValueError("Player not found")

    h2h = compute_h2h(db, player1_id, player2_id, surface)
    feature_vector = build_feature_vector(db, p1, p2, h2h, surface, series, round_name, best_of, tournament)

    X = _df_for_model(feature_vector, metadata)
    p1_win_prob = float(model.predict_proba(X)[0][1])
    feature_dict = dict(zip(FEATURE_COLUMNS, feature_vector))

    return generate_match_analysis(
        p1_name=p1.name,
        p2_name=p2.name,
        surface=surface,
        series=series,
        round_name=round_name,
        best_of=best_of,
        tournament=tournament,
        p1_win_prob=p1_win_prob,
        feature_dict=feature_dict,
        p1_elo=p1.elo_overall,
        p2_elo=p2.elo_overall,
        p1_surface_elo=get_surface_elo(p1, surface),
        p2_surface_elo=get_surface_elo(p2, surface),
        p1_rank=p1.current_rank,
        p2_rank=p2.current_rank,
        h2h_surface_p1_wins=h2h["surface_p1_wins"],
        h2h_surface_total=h2h["surface_total"],
    )


def predict_match(db, player1_id: int, player2_id: int, surface: str,
                  series: str, round_name: str, best_of: int,
                  tournament: Optional[str] = None) -> dict:
    from db.models import Player, PredictionLog

    model, metadata = load_model()

    p1 = db.query(Player).get(player1_id)
    p2 = db.query(Player).get(player2_id)

    if not p1 or not p2:
        raise ValueError("Player not found")

    h2h = compute_h2h(db, player1_id, player2_id, surface)

    feature_vector = build_feature_vector(db, p1, p2, h2h, surface, series, round_name, best_of, tournament)

    X = _df_for_model(feature_vector, metadata)
    p1_win_prob = float(model.predict_proba(X)[0][1])

    key_factors = format_key_factors(feature_vector, p1.name, p2.name)
    confidence = compute_confidence(p1, p2, h2h, p1_win_prob)

    # Log prediction
    log_entry = PredictionLog(
        player1_id=player1_id,
        player2_id=player2_id,
        player1_name=p1.name,
        player2_name=p2.name,
        surface=surface,
        series=series,
        best_of=best_of,
        round=round_name,
        p1_win_prob=p1_win_prob,
    )
    db.add(log_entry)
    db.commit()

    return {
        "player1": {
            "id": p1.id,
            "name": p1.name,
            "win_probability": p1_win_prob,
            "elo": round(p1.elo_overall, 0),
            "surface_elo": round(get_surface_elo(p1, surface), 0),
            "rank": p1.current_rank,
            "win_rate_overall": round(p1.win_rate_overall * 100, 1),
            "win_rate_surface": round(get_surface_winrate(p1, surface) * 100, 1),
        },
        "player2": {
            "id": p2.id,
            "name": p2.name,
            "win_probability": 1.0 - p1_win_prob,
            "elo": round(p2.elo_overall, 0),
            "surface_elo": round(get_surface_elo(p2, surface), 0),
            "rank": p2.current_rank,
            "win_rate_overall": round(p2.win_rate_overall * 100, 1),
            "win_rate_surface": round(get_surface_winrate(p2, surface) * 100, 1),
        },
        "head_to_head": h2h,
        "key_factors": key_factors,
        "confidence": confidence,
        "analysis": None,
        "surface": surface,
        "series": series,
        "round": round_name,
        "best_of": best_of,
        "tournament": tournament,
    }
