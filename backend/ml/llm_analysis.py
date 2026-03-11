"""
Hybrid ML+LLM layer: generates a concise match analysis narrative using Claude.

The XGBoost model owns the win probability. Claude's job is to explain it —
grounding the analysis in the actual feature values so it reads as data-driven
commentary rather than generic text.
"""

import os
from typing import Optional

_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _build_prompt(
    p1_name: str,
    p2_name: str,
    surface: str,
    series: str,
    round_name: str,
    best_of: int,
    tournament: Optional[str],
    p1_win_prob: float,
    p1_elo: float,
    p2_elo: float,
    p1_surface_elo: float,
    p2_surface_elo: float,
    p1_rank: Optional[int],
    p2_rank: Optional[int],
    h2h_p1_wins: int,
    h2h_p2_wins: int,
    h2h_surface_p1_wins: int,
    h2h_surface_total: int,
    p1_last20: float,
    p2_last20: float,
    p1_last5: float,
    p2_last5: float,
    serve_edge: float,
    return_edge: float,
    p1_first_serve_win_pct: float,
    p2_first_serve_win_pct: float,
    p1_return_win_pct: float,
    p2_return_win_pct: float,
) -> str:
    winner = p1_name if p1_win_prob >= 0.5 else p2_name
    underdog = p2_name if p1_win_prob >= 0.5 else p1_name
    winner_prob = max(p1_win_prob, 1 - p1_win_prob)

    event = tournament or series
    context = f"{event}, {round_name}, {surface}, Best of {best_of}"

    elo_leader = p1_name if p1_elo >= p2_elo else p2_name
    surf_elo_leader = p1_name if p1_surface_elo >= p2_surface_elo else p2_name

    rank_line = ""
    if p1_rank and p2_rank:
        rank_line = f"- ATP Rank: {p1_name} #{p1_rank} vs {p2_name} #{p2_rank}\n"

    h2h_total = h2h_p1_wins + h2h_p2_wins
    h2h_line = (
        f"- H2H: {p1_name} {h2h_p1_wins}–{h2h_p2_wins} {p2_name} (all-time)"
        if h2h_total > 0
        else "- H2H: No previous meetings"
    )
    if h2h_surface_total > 0:
        h2h_line += f", {h2h_surface_p1_wins}–{h2h_surface_total - h2h_surface_p1_wins} on {surface}"

    serve_direction = p1_name if serve_edge > 0 else p2_name
    return_direction = p1_name if return_edge > 0 else p2_name

    return f"""You are a concise tennis analyst. Write a 2–3 sentence match preview grounded in the data below.

Matchup: {p1_name} vs {p2_name}
Context: {context}
Model prediction: {winner} wins ({winner_prob:.0%} probability)

Key data:
- Overall Elo: {p1_name} {p1_elo:.0f} · {p2_name} {p2_elo:.0f} (leader: {elo_leader}, gap {abs(p1_elo - p2_elo):.0f})
- {surface} Elo: {p1_name} {p1_surface_elo:.0f} · {p2_name} {p2_surface_elo:.0f} (leader: {surf_elo_leader}, gap {abs(p1_surface_elo - p2_surface_elo):.0f})
{rank_line}{h2h_line}
- Recent form (last 20 / last 5): {p1_name} {p1_last20:.0%} / {p1_last5:.0%} · {p2_name} {p2_last20:.0%} / {p2_last5:.0%}
- 1st serve win %: {p1_name} {p1_first_serve_win_pct:.1%} · {p2_name} {p2_first_serve_win_pct:.1%}
- Return win %: {p1_name} {p1_return_win_pct:.1%} · {p2_name} {p2_return_win_pct:.1%}
- Serve edge ({serve_direction} favoured): {abs(serve_edge):.3f}
- Return edge ({return_direction} favoured): {abs(return_edge):.3f}

Instructions: Reference specific numbers. Identify the primary reason {winner} is favoured. Note one meaningful surface or serve/return matchup factor. End by describing what {underdog} would need to do to win. No bullet points. Do not restate the probability."""


def generate_match_analysis(
    p1_name: str,
    p2_name: str,
    surface: str,
    series: str,
    round_name: str,
    best_of: int,
    tournament: Optional[str],
    p1_win_prob: float,
    feature_dict: dict,
    p1_elo: float,
    p2_elo: float,
    p1_surface_elo: float,
    p2_surface_elo: float,
    p1_rank: Optional[int],
    p2_rank: Optional[int],
    h2h_surface_p1_wins: int,
    h2h_surface_total: int,
) -> Optional[str]:
    """Call Claude to generate a match analysis. Returns None on any failure."""
    client = _get_client()
    if client is None:
        return None

    try:
        prompt = _build_prompt(
            p1_name=p1_name,
            p2_name=p2_name,
            surface=surface,
            series=series,
            round_name=round_name,
            best_of=best_of,
            tournament=tournament,
            p1_win_prob=p1_win_prob,
            p1_elo=p1_elo,
            p2_elo=p2_elo,
            p1_surface_elo=p1_surface_elo,
            p2_surface_elo=p2_surface_elo,
            p1_rank=p1_rank,
            p2_rank=p2_rank,
            h2h_p1_wins=int(feature_dict.get("h2h_p1_wins", 0)),
            h2h_p2_wins=int(feature_dict.get("h2h_total", 0) - feature_dict.get("h2h_p1_wins", 0)),
            h2h_surface_p1_wins=h2h_surface_p1_wins,
            h2h_surface_total=h2h_surface_total,
            p1_last20=feature_dict.get("p1_winrate_last20", 0.5),
            p2_last20=feature_dict.get("p2_winrate_last20", 0.5),
            p1_last5=feature_dict.get("p1_winrate_last5", 0.5),
            p2_last5=feature_dict.get("p2_winrate_last5", 0.5),
            serve_edge=feature_dict.get("serve_edge", 0.0),
            return_edge=feature_dict.get("return_edge", 0.0),
            p1_first_serve_win_pct=feature_dict.get("p1_first_serve_win_pct", 0.683),
            p2_first_serve_win_pct=feature_dict.get("p2_first_serve_win_pct", 0.683),
            p1_return_win_pct=feature_dict.get("p1_return_win_pct", 0.337),
            p2_return_win_pct=feature_dict.get("p2_return_win_pct", 0.337),
        )

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=220,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    except Exception:
        return None
