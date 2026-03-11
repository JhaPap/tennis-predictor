import numpy as np
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from api.deps import get_db
from api.schemas import PlayerSummary, PlayerDetail, RecentMatch, EloHistoryPoint, ServeStats
from db.models import Player, Match

router = APIRouter(prefix="/api/players", tags=["players"])

# ── Charting stats (lazy-loaded once) ────────────────────────────────────────
_charting: dict[int, ServeStats] | None = None
_charting_means: ServeStats | None = None

_CHARTING_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "charting_player_stats.parquet"

_CHARTING_DEFAULTS = {
    "ace_rate": 0.067,
    "df_rate": 0.040,
    "first_serve_pct": 0.611,
    "first_serve_win_pct": 0.683,
    "second_serve_win_pct": 0.480,
    "return_win_pct": 0.337,
}


def _load_charting() -> tuple[dict[int, ServeStats], ServeStats]:
    global _charting, _charting_means
    if _charting is not None:
        return _charting, _charting_means  # type: ignore[return-value]

    if not _CHARTING_PATH.exists():
        fallback = ServeStats(**_CHARTING_DEFAULTS, charted_matches=0, has_data=False)
        _charting = {}
        _charting_means = fallback
        return _charting, _charting_means

    df = pd.read_parquet(_CHARTING_PATH)
    stat_cols = ["ace_rate", "df_rate", "first_serve_pct",
                 "first_serve_win_pct", "second_serve_win_pct", "return_win_pct"]

    # League means from each player's latest snapshot
    latest = df.groupby("player_id").last().reset_index()
    means = {}
    for col in stat_cols:
        val = float(latest[col].mean(skipna=True))
        means[col] = val if not np.isnan(val) else _CHARTING_DEFAULTS[col]
    _charting_means = ServeStats(**means, charted_matches=0, has_data=False)

    # Per-player latest stats
    _charting = {}
    for pid, grp in df.groupby("player_id"):
        last = grp.sort_values("date").iloc[-1]
        row = {}
        for col in stat_cols:
            v = float(last[col]) if not pd.isna(last[col]) else means[col]
            row[col] = v
        _charting[int(pid)] = ServeStats(
            **row,
            charted_matches=int(last["charted_matches"]),
            has_data=True,
        )

    return _charting, _charting_means


def _get_serve_stats(player_id: int) -> ServeStats:
    stats, means = _load_charting()
    return stats.get(player_id, means)


def _get_recent_matches(db: Session, player_id: int, limit: int = 100) -> list[RecentMatch]:
    matches = (
        db.query(Match)
        .filter(
            or_(Match.player1_id == player_id, Match.player2_id == player_id)
        )
        .order_by(Match.date.desc())
        .limit(limit)
        .all()
    )
    result = []
    for m in matches:
        if m.player1_id == player_id:
            opp_id = m.player2_id
        else:
            opp_id = m.player1_id

        opp = db.query(Player).get(opp_id)
        opp_name = opp.name if opp else "Unknown"
        won = m.winner_id == player_id

        result.append(RecentMatch(
            id=m.id,
            date=m.date,
            tournament=m.tournament,
            surface=m.surface,
            opponent_name=opp_name,
            won=won,
            score=m.score,
        ))
    return result


def _get_elo_history(db: Session, player_id: int) -> list[EloHistoryPoint]:
    """
    Return monthly Elo snapshots from match history using pre-match Elo values.
    """
    matches = (
        db.query(Match)
        .filter(
            or_(Match.player1_id == player_id, Match.player2_id == player_id)
        )
        .order_by(Match.date)
        .all()
    )

    # Sample one point per month (last match of each month)
    monthly: dict[str, EloHistoryPoint] = {}
    for m in matches:
        month_key = m.date.strftime("%Y-%m")
        if m.player1_id == player_id:
            elo = m.elo_p1_before
        else:
            elo = m.elo_p2_before

        if elo is not None:
            monthly[month_key] = EloHistoryPoint(date=m.date, elo=round(elo, 0))

    return list(monthly.values())


@router.get("", response_model=list[PlayerSummary])
def search_players(
    search: str = Query(default="", min_length=0),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    # Only return active (currently ranked) players
    query = db.query(Player).filter(Player.current_rank.isnot(None))
    if search:
        query = query.filter(Player.name.ilike(f"%{search}%"))
    players = (
        query.order_by(Player.elo_overall.desc())
        .limit(limit)
        .all()
    )
    return [PlayerSummary.model_validate(p) for p in players]


@router.get("/{player_id}", response_model=PlayerDetail)
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.query(Player).get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    recent = _get_recent_matches(db, player_id)
    elo_history = _get_elo_history(db, player_id)

    return PlayerDetail(
        id=player.id,
        name=player.name,
        elo_overall=player.elo_overall,
        elo_hard=player.elo_hard,
        elo_clay=player.elo_clay,
        elo_grass=player.elo_grass,
        current_rank=player.current_rank,
        current_pts=player.current_pts,
        matches_played=player.matches_played,
        wins=player.wins,
        win_rate_overall=player.win_rate_overall,
        win_rate_hard=player.win_rate_hard,
        win_rate_clay=player.win_rate_clay,
        win_rate_grass=player.win_rate_grass,
        matches_hard=player.matches_hard,
        matches_clay=player.matches_clay,
        matches_grass=player.matches_grass,
        recent_matches=recent,
        elo_history=elo_history,
        serve_stats=_get_serve_stats(player_id),
    )
