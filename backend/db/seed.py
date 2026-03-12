"""
Load processed parquet data → SQLite database.
Run after the full pipeline completes.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MATCHES_CLEAN_PATH, ELO_RATINGS_PATH, PROCESSED_DIR
from db.database import Base, engine, SessionLocal
from db.models import Match, Player, User


def safe_int(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return int(v)


def safe_float(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return float(v)


def seed_database():
    print("Creating tables...")
    # Drop only sports tables — never the users table
    sports_tables = [Match.__table__, Player.__table__]
    # Also drop prediction_log if it exists
    from db.models import PredictionLog
    sports_tables.append(PredictionLog.__table__)
    Base.metadata.drop_all(bind=engine, tables=sports_tables)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    # Load data
    print("Loading parquet files...")
    df = pd.read_parquet(MATCHES_CLEAN_PATH)
    elo_df = pd.read_parquet(ELO_RATINGS_PATH)
    players_lookup = pd.read_parquet(PROCESSED_DIR / "players_lookup.parquet")

    # Restrict to active (non-retired) players only
    active_players_path = PROCESSED_DIR / "active_players.parquet"
    if active_players_path.exists():
        active_df = pd.read_parquet(active_players_path)
        active_ids = set(active_df["id"].tolist())
        players_lookup = players_lookup[players_lookup["id"].isin(active_ids)]
        print(f"  Active players: {len(players_lookup):,} (retired players excluded)")
    else:
        print("  WARNING: active_players.parquet not found — seeding all players")

    # Merge elo into player lookup
    player_info = players_lookup.merge(elo_df, left_on="id", right_on="player_id", how="left")

    # Compute per-player aggregate stats from match data
    print("Computing player aggregate stats...")
    stats = {}
    for _, row in df.iterrows():
        p1 = int(row["player1_id"])
        p2 = int(row["player2_id"])
        surface = str(row["Surface"])
        p1_won = int(row["p1_won"])

        if p1 not in stats:
            stats[p1] = {"wins": 0, "matches": 0, "hard_w": 0, "hard_m": 0,
                         "clay_w": 0, "clay_m": 0, "grass_w": 0, "grass_m": 0,
                         "last_rank": None, "last_pts": None}
        if p2 not in stats:
            stats[p2] = {"wins": 0, "matches": 0, "hard_w": 0, "hard_m": 0,
                         "clay_w": 0, "clay_m": 0, "grass_w": 0, "grass_m": 0,
                         "last_rank": None, "last_pts": None}

        stats[p1]["wins"] += p1_won
        stats[p1]["matches"] += 1
        stats[p2]["wins"] += 1 - p1_won
        stats[p2]["matches"] += 1

        for pid, won in [(p1, p1_won), (p2, 1 - p1_won)]:
            if surface == "Hard":
                stats[pid]["hard_m"] += 1
                stats[pid]["hard_w"] += won
            elif surface == "Clay":
                stats[pid]["clay_m"] += 1
                stats[pid]["clay_w"] += won
            elif surface == "Grass":
                stats[pid]["grass_m"] += 1
                stats[pid]["grass_w"] += won

        # Track latest rank
        if pd.notna(row["Rank_1"]):
            stats[p1]["last_rank"] = int(row["Rank_1"])
        if pd.notna(row["Rank_2"]):
            stats[p2]["last_rank"] = int(row["Rank_2"])
        if pd.notna(row.get("Pts_1")):
            stats[p1]["last_pts"] = float(row["Pts_1"])
        if pd.notna(row.get("Pts_2")):
            stats[p2]["last_pts"] = float(row["Pts_2"])

    # Seed players
    print(f"Seeding {len(player_info):,} players...")
    players_batch = []
    for _, row in player_info.iterrows():
        pid = int(row["id"])
        s = stats.get(pid, {})
        m = s.get("matches", 0)
        w = s.get("wins", 0)

        def wr(wins, matches):
            return wins / matches if matches > 0 else 0.5

        p = Player(
            id=pid,
            name=row["name"],
            elo_overall=float(row.get("elo_overall", 1500)),
            elo_hard=float(row.get("elo_hard", 1500)),
            elo_clay=float(row.get("elo_clay", 1500)),
            elo_grass=float(row.get("elo_grass", 1500)),
            matches_played=m,
            wins=w,
            win_rate_overall=wr(w, m),
            matches_hard=s.get("hard_m", 0),
            matches_clay=s.get("clay_m", 0),
            matches_grass=s.get("grass_m", 0),
            win_rate_hard=wr(s.get("hard_w", 0), s.get("hard_m", 0)),
            win_rate_clay=wr(s.get("clay_w", 0), s.get("clay_m", 0)),
            win_rate_grass=wr(s.get("grass_w", 0), s.get("grass_m", 0)),
            current_rank=s.get("last_rank"),
            current_pts=s.get("last_pts"),
        )
        players_batch.append(p)

    session.bulk_save_objects(players_batch)
    session.commit()
    print(f"  Players seeded: {len(players_batch):,}")

    # Keep only matches that involve at least one active player
    # (preserves H2H history but drops purely retired-vs-retired matches)
    if "active_ids" in dir():
        df_matches = df[
            df["player1_id"].isin(active_ids) | df["player2_id"].isin(active_ids)
        ]
        print(f"  Matches involving active players: {len(df_matches):,} / {len(df):,}")
    else:
        df_matches = df

    # Seed matches in batches
    print(f"Seeding {len(df_matches):,} matches...")
    BATCH_SIZE = 5000
    df_matches = df_matches.reset_index(drop=True)
    for start in range(0, len(df_matches), BATCH_SIZE):
        batch = df_matches.iloc[start:start + BATCH_SIZE]
        match_objects = []
        for _, row in batch.iterrows():
            m = Match(
                tournament=str(row["Tournament"]),
                date=row["Date"].date(),
                series=str(row["Series"]),
                court=str(row.get("Court", "")),
                surface=str(row["Surface"]),
                round=str(row["Round"]),
                best_of=int(row["Best of"]) if pd.notna(row["Best of"]) else 3,
                player1_id=int(row["player1_id"]),
                player2_id=int(row["player2_id"]),
                winner_id=int(row["winner_id"]),
                rank1=safe_int(row.get("Rank_1")),
                rank2=safe_int(row.get("Rank_2")),
                pts1=safe_float(row.get("Pts_1")),
                pts2=safe_float(row.get("Pts_2")),
                odd1=safe_float(row.get("Odd_1")),
                odd2=safe_float(row.get("Odd_2")),
                score=str(row.get("Score", "")) if pd.notna(row.get("Score")) else None,
                elo_p1_before=safe_float(row.get("elo_p1_before")),
                elo_p2_before=safe_float(row.get("elo_p2_before")),
                elo_surface_p1_before=safe_float(row.get("elo_surface_p1_before")),
                elo_surface_p2_before=safe_float(row.get("elo_surface_p2_before")),
            )
            match_objects.append(m)
        session.bulk_save_objects(match_objects)
        session.commit()
        print(f"  Seeded {min(start + BATCH_SIZE, len(df_matches)):,}/{len(df_matches):,} matches")

    session.close()
    print("Database seeding complete.")


if __name__ == "__main__":
    seed_database()
