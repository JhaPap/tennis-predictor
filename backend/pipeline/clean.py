"""
Step 1: CSV ingestion, normalization, and cleaning.
Active-player filter: players with last match >= ACTIVE_CUTOFF are current.
All historical matches are kept for Elo computation, but `both_active` flag
marks rows where both players are active — used in train.py.
Outputs: data/processed/matches_clean.parquet, active_players.parquet
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CSV_PATH, MATCHES_CLEAN_PATH, SERIES_MAP, PROCESSED_DIR

# Players whose last match is before this date are treated as retired
ACTIVE_CUTOFF = pd.Timestamp("2023-01-01")


def parse_score(score_str: str) -> dict:
    """Parse '6-4 7-5' into set/game counts for each player."""
    result = {"p1_sets": 0, "p2_sets": 0, "total_games": 0}
    if not isinstance(score_str, str) or not score_str.strip():
        return result
    try:
        sets = score_str.strip().split()
        for s in sets:
            if "-" not in s:
                continue
            parts = s.split("-")
            if len(parts) != 2:
                continue
            # Strip tiebreak notation like (7)
            g1 = int("".join(c for c in parts[0] if c.isdigit())[:2] or "0")
            g2_raw = parts[1].split("(")[0]
            g2 = int("".join(c for c in g2_raw if c.isdigit())[:2] or "0")
            result["total_games"] += g1 + g2
            if g1 > g2:
                result["p1_sets"] += 1
            elif g2 > g1:
                result["p2_sets"] += 1
    except Exception:
        pass
    return result


def load_and_clean(csv_path=CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # Parse and sort by date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "Player_1", "Player_2", "Winner"])
    df = df.sort_values("Date").reset_index(drop=True)

    # Normalize series names (pre-2009 naming)
    df["Series"] = df["Series"].map(lambda s: SERIES_MAP.get(s, s))

    # Replace -1 sentinels with NaN
    for col in ["Rank_1", "Rank_2", "Pts_1", "Pts_2", "Odd_1", "Odd_2"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].replace(-1, np.nan)
            df[col] = df[col].replace(-1.0, np.nan)

    # Binary target: 1 if Player_1 won
    df["p1_won"] = (df["Winner"] == df["Player_1"]).astype(int)

    # Derived flags
    df["is_grand_slam"] = (df["Series"] == "Grand Slam").astype(int)
    df["is_best_of_5"] = (df["Best of"] == 5).astype(int)
    df["is_indoor"] = (df["Court"].str.strip().str.lower() == "indoor").astype(int)

    # Normalize surface
    df["Surface"] = df["Surface"].str.strip().str.title()

    # Parse score
    score_parsed = df["Score"].apply(parse_score)
    df["p1_sets"] = score_parsed.apply(lambda x: x["p1_sets"])
    df["p2_sets"] = score_parsed.apply(lambda x: x["p2_sets"])
    df["total_games"] = score_parsed.apply(lambda x: x["total_games"])

    # Build canonical player ID lookup (consistent across pipeline runs)
    all_players = pd.Series(
        pd.concat([df["Player_1"], df["Player_2"]]).unique()
    ).sort_values().reset_index(drop=True)
    player_id_map = {name: idx + 1 for idx, name in enumerate(all_players)}

    df["player1_id"] = df["Player_1"].map(player_id_map)
    df["player2_id"] = df["Player_2"].map(player_id_map)
    df["winner_id"] = df["Winner"].map(player_id_map)

    # Save player lookup
    player_df = pd.DataFrame(
        [{"id": v, "name": k} for k, v in player_id_map.items()]
    ).sort_values("id")
    player_df.to_parquet(PROCESSED_DIR / "players_lookup.parquet", index=False)

    # --- Active player filter ---
    # Compute each player's last match date across both Player_1 and Player_2 columns
    last_as_p1 = df.groupby("Player_1")["Date"].max().rename("last_date")
    last_as_p2 = df.groupby("Player_2")["Date"].max().rename("last_date")
    last_match = pd.concat([last_as_p1, last_as_p2]).groupby(level=0).max()

    active_names = set(last_match[last_match >= ACTIVE_CUTOFF].index)
    active_ids = {player_id_map[n] for n in active_names if n in player_id_map}

    # Save active player list for use by seeder / API
    active_df = pd.DataFrame([
        {"id": player_id_map[n], "name": n, "last_match_date": last_match[n]}
        for n in active_names if n in player_id_map
    ]).sort_values("id")
    active_df.to_parquet(PROCESSED_DIR / "active_players.parquet", index=False)

    # Flag rows where BOTH players are active (used to restrict training data)
    df["both_active"] = (
        df["player1_id"].isin(active_ids) & df["player2_id"].isin(active_ids)
    )

    return df


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading and cleaning CSV...")
    df = load_and_clean()
    active_count = len(pd.read_parquet(PROCESSED_DIR / "active_players.parquet"))
    both_active_count = df["both_active"].sum()
    print(f"  Total rows:          {len(df):,}")
    print(f"  Date range:          {df['Date'].min().date()} → {df['Date'].max().date()}")
    print(f"  Total unique players:{len(pd.concat([df['Player_1'], df['Player_2']]).unique()):,}")
    print(f"  Active players:      {active_count} (last match >= {ACTIVE_CUTOFF.date()})")
    print(f"  Both-active matches: {both_active_count:,} (used for model training)")
    print(f"  Surfaces: {df['Surface'].value_counts().to_dict()}")
    print(f"  Series: {df['Series'].value_counts().to_dict()}")
    nulls = df[["Rank_1", "Rank_2", "Pts_1", "Pts_2", "Odd_1", "Odd_2"]].isnull().sum()
    print(f"  Null counts:\n{nulls}")

    df.to_parquet(MATCHES_CLEAN_PATH, index=False)
    print(f"Saved → {MATCHES_CLEAN_PATH}")


if __name__ == "__main__":
    main()
