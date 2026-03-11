from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from api.deps import get_db
from api.schemas import TournamentSummary, TournamentBracket, BracketRound, BracketMatch
from db.models import Match, Player
from config import ROUND_ORDER

router = APIRouter(prefix="/api/tournaments", tags=["tournaments"])


@router.get("", response_model=list[TournamentSummary])
def list_tournaments(
    year: int = Query(default=None),
    series: str = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(
        Match.tournament,
        func.extract("year", Match.date).label("year"),
        Match.series,
        Match.surface,
        func.count(Match.id).label("match_count"),
    ).group_by(
        Match.tournament,
        func.extract("year", Match.date),
        Match.series,
        Match.surface,
    )

    if year:
        query = query.filter(extract("year", Match.date) == year)
    if series:
        query = query.filter(Match.series == series)

    rows = query.order_by(
        func.extract("year", Match.date).desc(),
        Match.series,
        Match.tournament,
    ).limit(500).all()

    return [
        TournamentSummary(
            name=row.tournament,
            year=int(row.year),
            series=row.series,
            surface=row.surface,
            match_count=row.match_count,
        )
        for row in rows
    ]


@router.get("/{tournament_name}/{year}/bracket", response_model=TournamentBracket)
def get_bracket(
    tournament_name: str,
    year: int,
    db: Session = Depends(get_db),
):
    matches = (
        db.query(Match)
        .filter(
            Match.tournament == tournament_name,
            extract("year", Match.date) == year,
        )
        .order_by(Match.date)
        .all()
    )

    if not matches:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Group by round in logical order
    round_order = {v: k for k, v in ROUND_ORDER.items()}
    rounds_dict: dict[str, list[BracketMatch]] = {}

    for m in matches:
        p1 = db.query(Player).get(m.player1_id)
        p2 = db.query(Player).get(m.player2_id)
        winner = db.query(Player).get(m.winner_id)

        bm = BracketMatch(
            id=m.id,
            player1_name=p1.name if p1 else "Unknown",
            player2_name=p2.name if p2 else "Unknown",
            winner_name=winner.name if winner else "Unknown",
            score=m.score,
            rank1=m.rank1,
            rank2=m.rank2,
        )
        round_name = m.round or "Unknown"
        if round_name not in rounds_dict:
            rounds_dict[round_name] = []
        rounds_dict[round_name].append(bm)

    # Sort rounds by ROUND_ORDER value
    def round_sort_key(round_name):
        return ROUND_ORDER.get(round_name, 99)

    sorted_rounds = sorted(rounds_dict.items(), key=lambda x: round_sort_key(x[0]))

    bracket_rounds = [
        BracketRound(round_name=rname, matches=rmatches)
        for rname, rmatches in sorted_rounds
    ]

    series = matches[0].series
    surface = matches[0].surface

    return TournamentBracket(
        name=tournament_name,
        year=year,
        series=series,
        surface=surface,
        rounds=bracket_rounds,
    )
