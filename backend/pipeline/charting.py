"""
Step 3.5: Match Charting Project — cumulative serve/return stats (anti-leakage).

Downloads Jeff Sackmann's Match Charting Project CSVs, normalises player names
to our "LastName F." format, matches to player_ids, and produces a parquet of
cumulative pre-match serve/return averages per player.

Output columns (charting_player_stats.parquet):
  player_id, date, ace_rate, df_rate, first_serve_pct,
  first_serve_win_pct, second_serve_win_pct, return_win_pct, charted_matches,
  bp_save_rate, bp_conversion_rate, net_win_rate, ue_rate, winner_rate
"""

import sys
import bisect
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHARTING_STATS_PATH, PROCESSED_DIR

# ── GitHub raw URLs ───────────────────────────────────────────────────────────
MATCHES_URL = (
    "https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject"
    "/master/charting-m-matches.csv"
)
STATS_URL = (
    "https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject"
    "/master/charting-m-stats-Overview.csv"
)
KP_SERVE_URL = (
    "https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject"
    "/master/charting-m-stats-KeyPointsServe.csv"
)
KP_RETURN_URL = (
    "https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject"
    "/master/charting-m-stats-KeyPointsReturn.csv"
)
NET_POINTS_URL = (
    "https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject"
    "/master/charting-m-stats-NetPoints.csv"
)
RALLY_URL = (
    "https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject"
    "/master/charting-m-stats-Rally.csv"
)

# ── Manual name corrections ───────────────────────────────────────────────────
# Maps charting "Firstname Lastname" → our DB "LastName F." format.
# Only needed when the simple last-word + first-initial heuristic fails.
MANUAL_CORRECTIONS: dict[str, str] = {
    # Compound surnames
    "Juan Martin Del Potro": "Del Potro J.",
    "Juan Martin del Potro": "Del Potro J.",
    "Alejandro Davidovich Fokina": "Davidovich Fokina A.",
    "Botic Van De Zandschulp": "Van De Zandschulp B.",
    "Roberto Bautista Agut": "Bautista Agut R.",
    "Alex De Minaur": "De Minaur A.",
    "Laslo Djere": "Djere L.",
    "Pedro Martinez": "Martinez P.",
    "Pedro Martinez Portero": "Martinez P.",
    "Feliciano Lopez": "Lopez F.",
    "Marc-Andrea Huesler": "Huesler M.",
    "Norbert Gombos": "Gombos N.",
    "Jan Lennard Struff": "Struff J.",
    "Lucas Pouille": "Pouille L.",
    "Albert Ramos": "Ramos-Vinolas A.",
    "Albert Ramos-Vinolas": "Ramos-Vinolas A.",
    "Pablo Cuevas": "Cuevas P.",
    "Pablo Carreno Busta": "Carreno Busta P.",
    "Pablo Carreno": "Carreno Busta P.",
    "Corentin Moutet": "Moutet C.",
    "Gregoire Barrere": "Barrere G.",
    "Jeremy Chardy": "Chardy J.",
    "Guido Andreozzi": "Andreozzi G.",
    "Guido Pella": "Pella G.",
    "Joao Sousa": "Sousa J.",
    "Nicolas Almagro": "Almagro N.",
    "Marcel Granollers": "Granollers M.",
    "David Ferrer": "Ferrer D.",
    "Fernando Verdasco": "Verdasco F.",
    "Nicolas Mahut": "Mahut N.",
    "Ernests Gulbis": "Gulbis E.",
}


def normalize_name(full_name: str) -> str:
    """Convert 'Firstname Lastname' → 'Lastname F.' (our DB format).

    Falls back to manual corrections for compound surnames.
    """
    if full_name in MANUAL_CORRECTIONS:
        return MANUAL_CORRECTIONS[full_name]

    parts = full_name.strip().split()
    if not parts:
        return full_name

    surname = parts[-1]
    initial = parts[0][0].upper() if parts[0] else "?"
    return f"{surname} {initial}."


def download_csv(url: str, label: str) -> pd.DataFrame:
    print(f"  Downloading {label}...")
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    from io import StringIO
    return pd.read_csv(StringIO(resp.text), low_memory=False)


def _build_kp_cumulative(
    df_raw: pd.DataFrame,
    match_dates: dict,
    name_to_id: dict,
    num_col: str,
    denom_col: str,
    out_col: str,
    row_filter: str | None = None,
) -> pd.DataFrame:
    """Build cumulative key-point stat snapshots from a KeyPoints or NetPoints CSV.

    Parameters
    ----------
    df_raw      : Raw CSV dataframe (KeyPointsServe, KeyPointsReturn, or NetPoints).
    match_dates : match_id → datetime mapping.
    name_to_id  : normalized player name → player_id mapping.
    num_col     : Numerator column name (e.g. "pts_won").
    denom_col   : Denominator column name (e.g. "pts" or "net_pts").
    out_col     : Output rate column name (e.g. "bp_save_rate").
    row_filter  : If set, keep only rows where the "row" column equals this value.
                  Use "BP" for break-point serve, "BPO" for break-point return,
                  "NetPoints" for net totals.  None keeps all rows.

    Returns
    -------
    DataFrame with columns: player_id, date, out_col
    """
    df = df_raw.copy()

    # Attach match date
    df["date"] = df["match_id"].map(match_dates)
    df = df.dropna(subset=["date"])

    # Filter to the requested row type to avoid double-counting sub-totals
    if row_filter is not None and "row" in df.columns:
        df = df[df["row"] == row_filter].copy()

    # Normalise player names → DB format, map to player_id
    if "player" not in df.columns:
        print(f"    Warning: 'player' column not found in {out_col} source data; skipping.")
        return pd.DataFrame(columns=["player_id", "date", out_col])

    df["db_name"] = df["player"].apply(normalize_name)
    df["player_id"] = df["db_name"].map(name_to_id)
    df = df.dropna(subset=["player_id"])
    df["player_id"] = df["player_id"].astype(int)

    # Cast numeric columns
    for col in [num_col, denom_col]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            print(f"    Warning: column '{col}' not found; treating as 0.")
            df[col] = 0.0

    # Group by (player_id, date) — sum across all row values within each match
    df_agg = (
        df.groupby(["player_id", "date"])[[num_col, denom_col]]
        .sum()
        .reset_index()
        .sort_values(["player_id", "date"])
        .reset_index(drop=True)
    )

    # Chronological accumulation per player
    records = []
    acc: dict[int, dict[str, float]] = {}

    for _, row in df_agg.iterrows():
        pid = int(row["player_id"])
        d = row["date"]

        if pid not in acc:
            acc[pid] = {"num": 0.0, "denom": 0.0}

        acc[pid]["num"]   += float(row[num_col])
        acc[pid]["denom"] += float(row[denom_col])

        cum_num   = acc[pid]["num"]
        cum_denom = acc[pid]["denom"]

        records.append({
            "player_id": pid,
            "date": d,
            out_col: cum_num / cum_denom if cum_denom > 0 else np.nan,
        })

    snap = pd.DataFrame(records)
    print(f"    {out_col}: {len(snap):,} snapshots for {snap['player_id'].nunique():,} players")
    return snap


def _build_rally_cumulative(
    df_raw: pd.DataFrame,
    match_dates: dict,
    name_to_id: dict,
) -> pd.DataFrame:
    """Build cumulative ue_rate and winner_rate snapshots from the Rally CSV.

    The Rally file uses 'server' and 'returner' columns instead of 'player'.
    Each row has stats for both players in a rally-length bucket.

    Expected columns: match_id, server, returner, pts,
                      p1w (server winners), p1u (server unforced),
                      p2w (returner winners), p2u (returner unforced)

    Returns
    -------
    DataFrame with columns: player_id, date, ue_rate, winner_rate
    """
    df = df_raw.copy()

    # Attach match date
    df["date"] = df["match_id"].map(match_dates)
    df = df.dropna(subset=["date"])

    # Filter to "Total" rows only — rally file has per-rally-length buckets AND
    # a summary "Total" row per match; using only Total avoids double-counting.
    if "row" in df.columns:
        df = df[df["row"] == "Total"].copy()

    # Actual MCP column names (pl1_* = server, pl2_* = returner)
    winner_server_col     = next((c for c in ["pl1_winners", "p1w", "p1_w", "sv_winners"] if c in df.columns), None)
    unforced_server_col   = next((c for c in ["pl1_unforced", "p1u", "p1_u", "sv_unforced"] if c in df.columns), None)
    winner_returner_col   = next((c for c in ["pl2_winners", "p2w", "p2_w", "rt_winners"] if c in df.columns), None)
    unforced_returner_col = next((c for c in ["pl2_unforced", "p2u", "p2_u", "rt_unforced"] if c in df.columns), None)
    pts_col               = next((c for c in ["pts", "total_pts", "points"] if c in df.columns), None)

    missing = [name for name, col in [
        ("server", "server"), ("returner", "returner"),
        ("pts", pts_col), ("winners_server", winner_server_col),
        ("unforced_server", unforced_server_col), ("winners_returner", winner_returner_col),
        ("unforced_returner", unforced_returner_col),
    ] if col is None]

    if missing:
        print(f"    Warning: Rally columns not found: {missing}. Skipping rally stats.")
        print(f"    Available columns: {list(df.columns)}")
        return pd.DataFrame(columns=["player_id", "date", "ue_rate", "winner_rate"])

    # Cast numeric columns
    for col in [pts_col, winner_server_col, unforced_server_col,
                winner_returner_col, unforced_returner_col]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ── Build per-player aggregates from server role ───────────────────────────
    df_s = df[["match_id", "date", "server", pts_col,
               winner_server_col, unforced_server_col]].copy()
    df_s.columns = ["match_id", "date", "player_name", "pts", "winners", "unforced"]
    df_s["db_name"] = df_s["player_name"].apply(normalize_name)
    df_s["player_id"] = df_s["db_name"].map(name_to_id)
    df_s = df_s.dropna(subset=["player_id"])
    df_s["player_id"] = df_s["player_id"].astype(int)

    # ── Build per-player aggregates from returner role ────────────────────────
    df_r = df[["match_id", "date", "returner", pts_col,
               winner_returner_col, unforced_returner_col]].copy()
    df_r.columns = ["match_id", "date", "player_name", "pts", "winners", "unforced"]
    df_r["db_name"] = df_r["player_name"].apply(normalize_name)
    df_r["player_id"] = df_r["db_name"].map(name_to_id)
    df_r = df_r.dropna(subset=["player_id"])
    df_r["player_id"] = df_r["player_id"].astype(int)

    # Combine both roles
    df_combined = pd.concat([df_s, df_r], ignore_index=True)

    # Group by (player_id, date) — sum across all rally-length buckets and roles
    df_agg = (
        df_combined.groupby(["player_id", "date"])[["pts", "winners", "unforced"]]
        .sum()
        .reset_index()
        .sort_values(["player_id", "date"])
        .reset_index(drop=True)
    )

    # Chronological accumulation per player
    records = []
    acc: dict[int, dict[str, float]] = {}

    for _, row in df_agg.iterrows():
        pid = int(row["player_id"])
        d = row["date"]

        if pid not in acc:
            acc[pid] = {"pts": 0.0, "winners": 0.0, "unforced": 0.0}

        acc[pid]["pts"]      += float(row["pts"])
        acc[pid]["winners"]  += float(row["winners"])
        acc[pid]["unforced"] += float(row["unforced"])

        cum_pts      = acc[pid]["pts"]
        cum_winners  = acc[pid]["winners"]
        cum_unforced = acc[pid]["unforced"]

        records.append({
            "player_id": pid,
            "date": d,
            "ue_rate":     cum_unforced / cum_pts if cum_pts > 0 else np.nan,
            "winner_rate": cum_winners  / cum_pts if cum_pts > 0 else np.nan,
        })

    snap = pd.DataFrame(records)
    print(f"    ue_rate/winner_rate: {len(snap):,} snapshots for {snap['player_id'].nunique():,} players")
    return snap


def build_charting_stats() -> pd.DataFrame:
    """Download, process, and return cumulative charting stats per player."""

    # ── 1. Download raw data ─────────────────────────────────────────────────
    matches_raw    = download_csv(MATCHES_URL,    "charting-m-matches.csv")
    stats_raw      = download_csv(STATS_URL,      "charting-m-stats-Overview.csv")
    kp_serve_raw   = download_csv(KP_SERVE_URL,   "charting-m-stats-KeyPointsServe.csv")
    kp_return_raw  = download_csv(KP_RETURN_URL,  "charting-m-stats-KeyPointsReturn.csv")
    net_points_raw = download_csv(NET_POINTS_URL, "charting-m-stats-NetPoints.csv")
    rally_raw      = download_csv(RALLY_URL,      "charting-m-stats-Rally.csv")

    print(f"  Matches: {len(matches_raw):,} rows | Overview Stats: {len(stats_raw):,} rows")
    print(f"  KP Serve: {len(kp_serve_raw):,} rows | KP Return: {len(kp_return_raw):,} rows")
    print(f"  Net Points: {len(net_points_raw):,} rows | Rally: {len(rally_raw):,} rows")

    # ── 2. Parse match dates ─────────────────────────────────────────────────
    matches_raw["date"] = pd.to_datetime(
        matches_raw["Date"].astype(str).str.strip(), format="%Y%m%d", errors="coerce"
    )
    matches_raw = matches_raw.dropna(subset=["date"])

    match_dates = matches_raw.set_index("match_id")["date"].to_dict()

    # ── 3. Filter overview stats to Total rows only ──────────────────────────
    stats = stats_raw[stats_raw["set"] == "Total"].copy()
    print(f"  Overview Total-set rows: {len(stats):,}")

    # ── 4. Attach match date ─────────────────────────────────────────────────
    stats["date"] = stats["match_id"].map(match_dates)
    stats = stats.dropna(subset=["date"])

    # ── 5. Load player lookup and build name→id mapping ─────────────────────
    players_df = pd.read_parquet(PROCESSED_DIR / "players_lookup.parquet")
    name_to_id: dict[str, int] = dict(zip(players_df["name"], players_df["id"]))

    # ── 6. Normalise charting player names → DB format ───────────────────────
    stats["db_name"] = stats["player"].apply(normalize_name)
    stats["player_id"] = stats["db_name"].map(name_to_id)

    n_matched = stats["player_id"].notna().sum()
    n_total = len(stats)
    n_unmatched = n_total - n_matched
    print(f"  Name matching: {n_matched:,}/{n_total:,} rows matched "
          f"({n_unmatched:,} unmatched — no player_id in our DB)")

    stats = stats.dropna(subset=["player_id"])
    stats["player_id"] = stats["player_id"].astype(int)

    # ── 7. Cast numeric columns ──────────────────────────────────────────────
    num_cols = [
        "serve_pts", "aces", "dfs", "first_in", "first_won",
        "second_in", "second_won", "return_pts", "return_pts_won",
    ]
    for col in num_cols:
        if col in stats.columns:
            stats[col] = pd.to_numeric(stats[col], errors="coerce").fillna(0)
        else:
            stats[col] = 0.0

    # ── 8. Sort chronologically, compute cumulative overview stats ───────────
    stats = stats.sort_values(["player_id", "date"]).reset_index(drop=True)

    records = []

    # Running accumulators per player
    acc: dict[int, dict[str, float]] = {}

    for _, row in stats.iterrows():
        pid = int(row["player_id"])
        d = row["date"]

        if pid not in acc:
            acc[pid] = {
                "serve_pts": 0.0,
                "aces": 0.0,
                "dfs": 0.0,
                "first_in": 0.0,
                "first_won": 0.0,
                "second_in": 0.0,
                "second_won": 0.0,
                "return_pts": 0.0,
                "return_pts_won": 0.0,
                "matches": 0,
            }

        a = acc[pid]

        # Update accumulators (BEFORE recording snapshot so snapshot is
        # post-match — snapshot is used for NEXT match's feature lookup
        # via date < current_match_date, giving anti-leakage)
        a["serve_pts"]       += float(row["serve_pts"])
        a["aces"]            += float(row["aces"])
        a["dfs"]             += float(row["dfs"])
        a["first_in"]        += float(row["first_in"])
        a["first_won"]       += float(row["first_won"])
        a["second_in"]       += float(row["second_in"])
        a["second_won"]      += float(row["second_won"])
        a["return_pts"]      += float(row["return_pts"])
        a["return_pts_won"]  += float(row["return_pts_won"])
        a["matches"]         += 1

        sp = a["serve_pts"]
        fi = a["first_in"]
        si = a["second_in"]
        rp = a["return_pts"]

        records.append({
            "player_id": pid,
            "date": d,
            "ace_rate":             a["aces"] / sp          if sp > 0 else np.nan,
            "df_rate":              a["dfs"] / sp            if sp > 0 else np.nan,
            "first_serve_pct":      fi / sp                  if sp > 0 else np.nan,
            "first_serve_win_pct":  a["first_won"] / fi      if fi > 0 else np.nan,
            "second_serve_win_pct": a["second_won"] / si     if si > 0 else np.nan,
            "return_win_pct":       a["return_pts_won"] / rp if rp > 0 else np.nan,
            "charted_matches": a["matches"],
        })

    base_result = pd.DataFrame(records)
    print(f"  Generated {len(base_result):,} cumulative overview snapshots for "
          f"{base_result['player_id'].nunique():,} players")

    # ── 9. Build new cumulative snapshots from additional datasets ───────────
    print("  Building key-points and rally cumulative snapshots...")

    kp_serve_snap  = _build_kp_cumulative(
        kp_serve_raw,  match_dates, name_to_id, "pts_won", "pts", "bp_save_rate",
        row_filter="BP",          # row=="BP" = break points faced on serve
    )
    kp_return_snap = _build_kp_cumulative(
        kp_return_raw, match_dates, name_to_id, "pts_won", "pts", "bp_conversion_rate",
        row_filter="BPO",         # row=="BPO" = break-point opportunities on return
    )
    net_snap = _build_kp_cumulative(
        net_points_raw, match_dates, name_to_id, "pts_won", "net_pts", "net_win_rate",
        row_filter="NetPoints",   # row=="NetPoints" = match total (excludes sub-categories)
    )
    rally_snap = _build_rally_cumulative(rally_raw, match_dates, name_to_id)

    # ── 10. Merge new snapshots into base_result via merge_asof ─────────────
    # merge_asof requires both DataFrames sorted by the merge key (date).
    base_result = base_result.sort_values("date").reset_index(drop=True)

    for snap, label in [
        (kp_serve_snap,  "bp_save_rate"),
        (kp_return_snap, "bp_conversion_rate"),
        (net_snap,       "net_win_rate"),
        (rally_snap,     "ue_rate / winner_rate"),
    ]:
        if snap.empty:
            print(f"    Skipping merge for {label} — empty snapshot DataFrame.")
            continue

        snap_sorted = snap.sort_values("date").reset_index(drop=True)

        base_result = pd.merge_asof(
            base_result,
            snap_sorted,
            by="player_id",
            on="date",
            direction="backward",
        )
        print(f"    Merged {label} into base_result.")

    print(f"  Final enriched parquet: {len(base_result):,} rows, "
          f"columns: {list(base_result.columns)}")

    return base_result


def get_league_means(df: pd.DataFrame) -> dict[str, float]:
    """Compute league-mean fallback values from the latest snapshot per player."""
    latest = df.groupby("player_id").last().reset_index()
    stat_cols = [
        "ace_rate", "df_rate", "first_serve_pct",
        "first_serve_win_pct", "second_serve_win_pct", "return_win_pct",
        "bp_save_rate", "bp_conversion_rate", "net_win_rate",
        "ue_rate", "winner_rate",
    ]
    means = {}
    for col in stat_cols:
        if col in latest.columns:
            means[col] = float(latest[col].mean(skipna=True))
        else:
            means[col] = np.nan
    return means


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    print("Building charting stats...")
    df = build_charting_stats()

    means = get_league_means(df)
    print("\nLeague-mean fallback values:")
    for k, v in means.items():
        print(f"  {k}: {v:.4f}")

    df.to_parquet(CHARTING_STATS_PATH, index=False)
    print(f"\nSaved → {CHARTING_STATS_PATH}")
    print(f"  {len(df):,} rows | {df['player_id'].nunique():,} players")


if __name__ == "__main__":
    main()
