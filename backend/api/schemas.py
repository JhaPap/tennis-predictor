from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# --- Auth ---

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    is_email_verified: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Prediction ---

class PredictRequest(BaseModel):
    player1_id: int
    player2_id: int
    surface: str = "Hard"
    series: str = "ATP250"
    round: str = "1st Round"
    best_of: int = 3
    tournament: Optional[str] = None


class PlayerPredictInfo(BaseModel):
    id: int
    name: str
    win_probability: float
    elo: float
    surface_elo: float
    rank: Optional[int]
    win_rate_overall: float
    win_rate_surface: float


class H2HInfo(BaseModel):
    p1_wins: int
    p2_wins: int
    total: int
    surface_p1_wins: int
    surface_total: int


class KeyFactor(BaseModel):
    feature: str
    p1_value: object
    p2_value: object
    advantage: str
    margin: object


class PredictResponse(BaseModel):
    player1: PlayerPredictInfo
    player2: PlayerPredictInfo
    head_to_head: H2HInfo
    key_factors: list[KeyFactor]
    confidence: str
    analysis: Optional[str] = None
    surface: str
    series: str
    round: str
    best_of: int
    tournament: Optional[str] = None


class PredictionLogEntry(BaseModel):
    id: int
    created_at: datetime
    player1_name: str
    player2_name: str
    surface: str
    series: str
    best_of: int
    round: Optional[str]
    p1_win_prob: float
    was_correct: Optional[bool]

    class Config:
        from_attributes = True


# --- Players ---

class ServeStats(BaseModel):
    ace_rate: float
    df_rate: float
    first_serve_pct: float
    first_serve_win_pct: float
    second_serve_win_pct: float
    return_win_pct: float
    charted_matches: int
    has_data: bool


class PlayerSummary(BaseModel):
    id: int
    name: str
    elo_overall: float
    current_rank: Optional[int]
    matches_played: int
    win_rate_overall: float

    class Config:
        from_attributes = True


class EloHistoryPoint(BaseModel):
    date: date
    elo: float


class RecentMatch(BaseModel):
    id: int
    date: date
    tournament: str
    surface: str
    opponent_name: str
    won: bool
    score: Optional[str]


class PlayerDetail(BaseModel):
    id: int
    name: str
    elo_overall: float
    elo_hard: float
    elo_clay: float
    elo_grass: float
    current_rank: Optional[int]
    current_pts: Optional[float]
    matches_played: int
    wins: int
    win_rate_overall: float
    win_rate_hard: float
    win_rate_clay: float
    win_rate_grass: float
    matches_hard: int
    matches_clay: int
    matches_grass: int
    recent_matches: list[RecentMatch]
    elo_history: list[EloHistoryPoint]
    serve_stats: Optional[ServeStats] = None

    class Config:
        from_attributes = True


# --- H2H detail ---

class H2HMatch(BaseModel):
    id: int
    date: date
    tournament: str
    surface: str
    series: str
    round: str
    winner_name: str
    score: Optional[str]
    rank1: Optional[int]
    rank2: Optional[int]


# --- Matches ---

class MatchSummary(BaseModel):
    id: int
    tournament: str
    date: date
    surface: str
    series: str
    round: str
    player1_name: str
    player2_name: str
    winner_name: str
    score: Optional[str]
    rank1: Optional[int]
    rank2: Optional[int]

    class Config:
        from_attributes = True


# --- Leaderboard ---

class LeaderboardEntry(BaseModel):
    rank: int
    player_id: int
    name: str
    elo: float
    wins: int
    matches_played: int
    win_rate: float
    win_rate_hard: float
    win_rate_clay: float
    win_rate_grass: float
    elo_change: float = 0.0


class TrendingEntry(BaseModel):
    rank: int
    player_id: int
    name: str
    elo: float
    current_rank: Optional[int]
    recent_wins: int
    recent_matches: int
    recent_win_rate: float
    overall_win_rate: float
    streak: int  # positive = win streak, negative = loss streak


# --- Tournaments ---

class TournamentSummary(BaseModel):
    name: str
    year: int
    series: str
    surface: str
    match_count: int


class BracketMatch(BaseModel):
    id: int
    player1_name: str
    player2_name: str
    winner_name: str
    score: Optional[str]
    rank1: Optional[int]
    rank2: Optional[int]


class BracketRound(BaseModel):
    round_name: str
    matches: list[BracketMatch]


class TournamentBracket(BaseModel):
    name: str
    year: int
    series: str
    surface: str
    rounds: list[BracketRound]


# --- Calibration ---

class CalibrationBucket(BaseModel):
    bucket_label: str
    predicted_avg: float
    actual_rate: float
    count: int


# --- Featured Matches ---

class FeaturedMatch(BaseModel):
    player1_id: int
    player1_name: str
    player2_id: int
    player2_name: str
    surface: str
    date: date
    winner_name: str
    score: Optional[str]


# --- Bracket Simulator ---

class SimulateBracketRequest(BaseModel):
    player_ids: list[int]  # exactly 8
    surface: str = "Hard"
    series: str = "ATP250"
    best_of: int = 3


class SimulatedPlayer(BaseModel):
    player_id: int
    name: str


class SimulatedMatch(BaseModel):
    player1: SimulatedPlayer
    player2: SimulatedPlayer
    expected_winner: SimulatedPlayer
    win_prob: float  # probability that expected_winner wins


class SimulatedRound(BaseModel):
    round_name: str
    matches: list[SimulatedMatch]


class TitleProbability(BaseModel):
    player_id: int
    name: str
    probability: float


class SimulateBracketResponse(BaseModel):
    rounds: list[SimulatedRound]
    title_probabilities: list[TitleProbability]


# --- Pagination ---

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    limit: int
    pages: int
