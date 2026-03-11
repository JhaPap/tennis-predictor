import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
from api.schemas import (
    SimulateBracketRequest,
    SimulateBracketResponse,
    SimulatedMatch,
    SimulatedPlayer,
    SimulatedRound,
    TitleProbability,
)
from db.models import Player

router = APIRouter(prefix="/api/simulate", tags=["simulate"])

SURFACE_ELO_ATTR = {
    "Hard": "elo_hard",
    "Clay": "elo_clay",
    "Grass": "elo_grass",
}


def _surface_win_prob(p1_elo: float, p2_elo: float) -> float:
    """Standard Elo win probability for p1 over p2."""
    return 1.0 / (1.0 + 10 ** ((p2_elo - p1_elo) / 400.0))


@router.post("/bracket", response_model=SimulateBracketResponse)
def simulate_bracket(req: SimulateBracketRequest, db: Session = Depends(get_db)):
    if len(req.player_ids) != 8:
        raise HTTPException(status_code=400, detail="Exactly 8 player IDs required.")

    # Fetch players
    players: dict[int, Player] = {}
    for pid in req.player_ids:
        p = db.query(Player).get(pid)
        if not p:
            raise HTTPException(status_code=404, detail=f"Player {pid} not found.")
        players[pid] = p

    elo_attr = SURFACE_ELO_ATTR.get(req.surface, "elo_overall")

    def get_elo(pid: int) -> float:
        p = players[pid]
        return getattr(p, elo_attr, p.elo_overall) or p.elo_overall

    # Pre-compute pairwise win probabilities
    ids = req.player_ids  # seeding order: [S1, S2, ..., S8]
    # Standard draw: 1 and 2 seeds are on opposite halves of the bracket
    # Top half: 1v8, 4v5  →  SF winner faces bottom-half SF winner in the Final
    # Bottom half: 3v6, 2v7
    # Path: 1 beats 8 → beats 4/5 → meets 2 only in the Final
    qf_pairs = [(ids[0], ids[7]), (ids[3], ids[4]), (ids[2], ids[5]), (ids[1], ids[6])]

    def win_prob(p1_id: int, p2_id: int) -> float:
        return _surface_win_prob(get_elo(p1_id), get_elo(p2_id))

    # Monte Carlo simulation (10,000 iterations)
    ITERATIONS = 10_000
    title_wins: dict[int, int] = {pid: 0 for pid in ids}

    for _ in range(ITERATIONS):
        # QF
        qf_winners = []
        for a, b in qf_pairs:
            qf_winners.append(a if random.random() < win_prob(a, b) else b)

        # SF: W(QF1) vs W(QF2), W(QF3) vs W(QF4)
        sf_winners = []
        for i in range(0, 4, 2):
            a, b = qf_winners[i], qf_winners[i + 1]
            sf_winners.append(a if random.random() < win_prob(a, b) else b)

        # Final
        a, b = sf_winners[0], sf_winners[1]
        champion = a if random.random() < win_prob(a, b) else b
        title_wins[champion] += 1

    # Build deterministic rounds using expected winners (highest prob)
    def expected_match(p1_id: int, p2_id: int) -> SimulatedMatch:
        prob = win_prob(p1_id, p2_id)
        if prob >= 0.5:
            winner_id, w_prob = p1_id, prob
        else:
            winner_id, w_prob = p2_id, 1 - prob
        return SimulatedMatch(
            player1=SimulatedPlayer(player_id=p1_id, name=players[p1_id].name),
            player2=SimulatedPlayer(player_id=p2_id, name=players[p2_id].name),
            expected_winner=SimulatedPlayer(player_id=winner_id, name=players[winner_id].name),
            win_prob=round(w_prob, 3),
        )

    # QF round
    qf_matches = [expected_match(a, b) for a, b in qf_pairs]
    qf_expected_winners = [m.expected_winner.player_id for m in qf_matches]

    # SF round (using expected QF winners)
    sf_match1 = expected_match(qf_expected_winners[0], qf_expected_winners[1])
    sf_match2 = expected_match(qf_expected_winners[2], qf_expected_winners[3])
    sf_matches = [sf_match1, sf_match2]
    sf_expected_winners = [sf_match1.expected_winner.player_id, sf_match2.expected_winner.player_id]

    # Final
    final_match = expected_match(sf_expected_winners[0], sf_expected_winners[1])

    rounds = [
        SimulatedRound(round_name="Quarterfinals", matches=qf_matches),
        SimulatedRound(round_name="Semifinals", matches=sf_matches),
        SimulatedRound(round_name="Final", matches=[final_match]),
    ]

    title_probs = [
        TitleProbability(
            player_id=pid,
            name=players[pid].name,
            probability=round(title_wins[pid] / ITERATIONS, 3),
        )
        for pid in ids
    ]
    title_probs.sort(key=lambda x: x.probability, reverse=True)

    return SimulateBracketResponse(rounds=rounds, title_probabilities=title_probs)
