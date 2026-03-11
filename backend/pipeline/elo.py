"""
Step 2: Compute chronological Elo ratings (overall + per surface).
Records pre-match Elo snapshots on each row to prevent data leakage.
Outputs: data/processed/elo_ratings.parquet (current ratings per player)
"""

import numpy as np
import pandas as pd
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MATCHES_CLEAN_PATH, ELO_RATINGS_PATH, K_FACTORS, PROCESSED_DIR

STARTING_ELO = 1500.0
SURFACES = ["Hard", "Clay", "Grass", "Carpet"]


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def compute_elo_ratings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds columns to df (sorted chronologically):
      elo_p1_before, elo_p2_before
      elo_surface_p1_before, elo_surface_p2_before
    Also returns final Elo state for seeding the DB.
    """
    df = df.copy().sort_values("Date").reset_index(drop=True)

    # Overall Elo per player
    overall_elo: dict[int, float] = defaultdict(lambda: STARTING_ELO)
    # Surface Elo per player: surface → player_id → elo
    surface_elo: dict[str, dict[int, float]] = {
        s: defaultdict(lambda: STARTING_ELO) for s in SURFACES
    }

    elo_p1_before = np.zeros(len(df))
    elo_p2_before = np.zeros(len(df))
    elo_surface_p1_before = np.zeros(len(df))
    elo_surface_p2_before = np.zeros(len(df))

    for i, row in df.iterrows():
        p1 = row["player1_id"]
        p2 = row["player2_id"]
        surface = row["Surface"] if row["Surface"] in SURFACES else "Hard"
        series = row["Series"]
        k = K_FACTORS.get(series, 10)

        # Record BEFORE update
        elo_p1_before[i] = overall_elo[p1]
        elo_p2_before[i] = overall_elo[p2]
        elo_surface_p1_before[i] = surface_elo[surface][p1]
        elo_surface_p2_before[i] = surface_elo[surface][p2]

        # Actual outcome (1 = p1 won, 0 = p2 won)
        outcome = float(row["p1_won"])

        # Update overall Elo
        e1 = expected_score(overall_elo[p1], overall_elo[p2])
        e2 = 1.0 - e1
        overall_elo[p1] += k * (outcome - e1)
        overall_elo[p2] += k * ((1.0 - outcome) - e2)

        # Update surface Elo
        es1 = expected_score(surface_elo[surface][p1], surface_elo[surface][p2])
        es2 = 1.0 - es1
        surface_elo[surface][p1] += k * (outcome - es1)
        surface_elo[surface][p2] += k * ((1.0 - outcome) - es2)

    df["elo_p1_before"] = elo_p1_before
    df["elo_p2_before"] = elo_p2_before
    df["elo_surface_p1_before"] = elo_surface_p1_before
    df["elo_surface_p2_before"] = elo_surface_p2_before

    # Build final ratings snapshot for all players
    all_player_ids = set(df["player1_id"]) | set(df["player2_id"])
    records = []
    for pid in all_player_ids:
        records.append({
            "player_id": pid,
            "elo_overall": overall_elo[pid],
            "elo_hard": surface_elo["Hard"][pid],
            "elo_clay": surface_elo["Clay"][pid],
            "elo_grass": surface_elo["Grass"][pid],
        })
    elo_df = pd.DataFrame(records)

    return df, elo_df


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading cleaned matches...")
    df = pd.read_parquet(MATCHES_CLEAN_PATH)
    print(f"  {len(df):,} matches")

    print("Computing Elo ratings...")
    df_elo, elo_snapshot = compute_elo_ratings(df)

    df_elo.to_parquet(MATCHES_CLEAN_PATH, index=False)
    print(f"  Saved Elo columns back to {MATCHES_CLEAN_PATH}")

    elo_snapshot.to_parquet(ELO_RATINGS_PATH, index=False)
    print(f"  Saved current Elo snapshot → {ELO_RATINGS_PATH}")

    # Sanity check: top overall Elo players
    players_lookup = pd.read_parquet(PROCESSED_DIR / "players_lookup.parquet")
    merged = elo_snapshot.merge(players_lookup, left_on="player_id", right_on="id")
    top10 = merged.nlargest(10, "elo_overall")[["name", "elo_overall", "elo_hard", "elo_clay", "elo_grass"]]
    print("\nTop 10 players by Elo:")
    print(top10.to_string(index=False))


if __name__ == "__main__":
    main()
