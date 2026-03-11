from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, aliased
from sqlalchemy import or_
from api.deps import get_db
from api.schemas import MatchSummary, FeaturedMatch
from db.models import Match, Player

router = APIRouter(prefix="/api/matches", tags=["matches"])


def _enrich_match(db: Session, m: Match) -> MatchSummary:
    p1 = db.query(Player).get(m.player1_id)
    p2 = db.query(Player).get(m.player2_id)
    winner = db.query(Player).get(m.winner_id)
    return MatchSummary(
        id=m.id,
        tournament=m.tournament,
        date=m.date,
        surface=m.surface,
        series=m.series,
        round=m.round,
        player1_name=p1.name if p1 else "Unknown",
        player2_name=p2.name if p2 else "Unknown",
        winner_name=winner.name if winner else "Unknown",
        score=m.score,
        rank1=m.rank1,
        rank2=m.rank2,
    )


@router.get("")
def list_matches(
    player_id: int = Query(default=None),
    surface: str = Query(default=None),
    year: int = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Match)

    if player_id:
        query = query.filter(
            or_(Match.player1_id == player_id, Match.player2_id == player_id)
        )
    if surface:
        query = query.filter(Match.surface == surface)
    if year:
        from sqlalchemy import extract
        query = query.filter(extract("year", Match.date) == year)

    query = query.order_by(Match.date.desc())
    total = query.count()
    matches = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": [_enrich_match(db, m) for m in matches],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/featured", response_model=list[FeaturedMatch])
def get_featured_matches(
    limit: int = Query(default=5, le=20),
    db: Session = Depends(get_db),
):
    """Most recent matches where both players have a current ATP rank."""
    P1 = aliased(Player)
    P2 = aliased(Player)
    Winner = aliased(Player)

    rows = (
        db.query(Match, P1, P2, Winner)
        .join(P1, Match.player1_id == P1.id)
        .join(P2, Match.player2_id == P2.id)
        .join(Winner, Match.winner_id == Winner.id)
        .filter(P1.current_rank.isnot(None))
        .filter(P2.current_rank.isnot(None))
        .order_by(Match.date.desc())
        .limit(limit)
        .all()
    )

    result = []
    for m, p1, p2, winner in rows:
        result.append(FeaturedMatch(
            player1_id=p1.id,
            player1_name=p1.name,
            player2_id=p2.id,
            player2_name=p2.name,
            surface=m.surface,
            date=m.date,
            winner_name=winner.name,
            score=m.score,
        ))
    return result


@router.get("/{match_id}", response_model=MatchSummary)
def get_match(match_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    m = db.query(Match).get(match_id)
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    return _enrich_match(db, m)
