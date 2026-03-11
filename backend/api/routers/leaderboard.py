from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, case, func
from api.deps import get_db
from api.schemas import LeaderboardEntry, TrendingEntry
from db.models import Player, Match


def _compute_elo_change(db: Session, player: Player, elo_col: str) -> float:
    """Return Elo change over last 20 matches (recent trend)."""
    matches = (
        db.query(Match)
        .filter(or_(Match.player1_id == player.id, Match.player2_id == player.id))
        .order_by(Match.date.desc())
        .limit(20)
        .all()
    )
    if not matches:
        return 0.0
    oldest = matches[-1]
    if oldest.player1_id == player.id:
        elo_before = oldest.elo_p1_before
    else:
        elo_before = oldest.elo_p2_before
    if elo_before is None:
        return 0.0
    current_elo = getattr(player, elo_col, player.elo_overall)
    return round(current_elo - elo_before, 1)

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])

SURFACE_ELO_MAP = {
    "hard": "elo_hard",
    "clay": "elo_clay",
    "grass": "elo_grass",
    "overall": "elo_overall",
}


@router.get("", response_model=list[LeaderboardEntry])
def get_leaderboard(
    surface: str = Query(default="overall"),
    metric: str = Query(default="elo"),
    limit: int = Query(default=50, le=200),
    min_matches: int = Query(default=20),
    db: Session = Depends(get_db),
):
    surface_lower = surface.lower()
    elo_col = SURFACE_ELO_MAP.get(surface_lower, "elo_overall")

    # ATP ranking view: filter to currently ranked players, sort by rank
    if metric == "rank":
        players = (
            db.query(Player)
            .filter(Player.current_rank.isnot(None))
            .order_by(Player.current_rank.asc())
            .limit(limit)
            .all()
        )
        result = []
        for p in players:
            result.append(LeaderboardEntry(
                rank=p.current_rank,
                player_id=p.id,
                name=p.name,
                elo=round(p.elo_overall, 0),
                wins=p.wins,
                matches_played=p.matches_played,
                win_rate=round(p.win_rate_overall * 100, 1),
                win_rate_hard=round(p.win_rate_hard * 100, 1),
                win_rate_clay=round(p.win_rate_clay * 100, 1),
                win_rate_grass=round(p.win_rate_grass * 100, 1),
                elo_change=_compute_elo_change(db, p, "elo_overall"),
            ))
        return result

    # Elo / win-rate views: active players only (have a current rank)
    query = (
        db.query(Player)
        .filter(Player.matches_played >= min_matches)
        .filter(Player.current_rank.isnot(None))
    )

    if metric == "elo":
        order_col = getattr(Player, elo_col)
    elif metric == "win_rate":
        if surface_lower == "hard":
            order_col = Player.win_rate_hard
        elif surface_lower == "clay":
            order_col = Player.win_rate_clay
        elif surface_lower == "grass":
            order_col = Player.win_rate_grass
        else:
            order_col = Player.win_rate_overall
    elif metric == "wins":
        order_col = Player.wins
    else:
        order_col = Player.elo_overall

    players = query.order_by(order_col.desc()).limit(limit).all()

    result = []
    for rank, p in enumerate(players, start=1):
        elo_val = getattr(p, elo_col, p.elo_overall)
        if surface_lower == "hard":
            wr = p.win_rate_hard
        elif surface_lower == "clay":
            wr = p.win_rate_clay
        elif surface_lower == "grass":
            wr = p.win_rate_grass
        else:
            wr = p.win_rate_overall

        result.append(LeaderboardEntry(
            rank=rank,
            player_id=p.id,
            name=p.name,
            elo=round(elo_val, 0),
            wins=p.wins,
            matches_played=p.matches_played,
            win_rate=round(p.win_rate_overall * 100, 1),
            win_rate_hard=round(p.win_rate_hard * 100, 1),
            win_rate_clay=round(p.win_rate_clay * 100, 1),
            win_rate_grass=round(p.win_rate_grass * 100, 1),
            elo_change=_compute_elo_change(db, p, elo_col),
        ))

    return result


@router.get("/trending", response_model=list[TrendingEntry])
def get_trending(
    limit: int = Query(default=50, le=100),
    window: int = Query(default=20, le=50),
    min_recent: int = Query(default=10),
    db: Session = Depends(get_db),
):
    """Players on the rise — sorted by recent win rate over their last `window` matches."""
    players = db.query(Player).filter(Player.matches_played >= 20).all()

    trending = []
    for p in players:
        # Get last N matches for this player
        recent = (
            db.query(Match)
            .filter(or_(Match.player1_id == p.id, Match.player2_id == p.id))
            .order_by(Match.date.desc())
            .limit(window)
            .all()
        )

        if len(recent) < min_recent:
            continue

        recent_wins = sum(1 for m in recent if m.winner_id == p.id)
        recent_wr = recent_wins / len(recent) if recent else 0

        # Compute current streak
        streak = 0
        for m in recent:
            won = m.winner_id == p.id
            if streak == 0:
                streak = 1 if won else -1
            elif won and streak > 0:
                streak += 1
            elif not won and streak < 0:
                streak -= 1
            else:
                break

        trending.append({
            "player_id": p.id,
            "name": p.name,
            "elo": round(p.elo_overall, 0),
            "current_rank": p.current_rank,
            "recent_wins": recent_wins,
            "recent_matches": len(recent),
            "recent_win_rate": round(recent_wr * 100, 1),
            "overall_win_rate": round(p.win_rate_overall * 100, 1),
            "streak": streak,
        })

    # Sort by recent win rate descending, then by streak
    trending.sort(key=lambda x: (x["recent_win_rate"], x["streak"]), reverse=True)

    result = []
    for rank, entry in enumerate(trending[:limit], start=1):
        result.append(TrendingEntry(rank=rank, **entry))

    return result
