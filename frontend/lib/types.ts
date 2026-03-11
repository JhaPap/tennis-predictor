export interface PlayerSummary {
  id: number;
  name: string;
  elo_overall: number;
  current_rank: number | null;
  matches_played: number;
  win_rate_overall: number;
}

export interface RecentMatch {
  id: number;
  date: string;
  tournament: string;
  surface: string;
  opponent_name: string;
  won: boolean;
  score: string | null;
}

export interface EloHistoryPoint {
  date: string;
  elo: number;
}

export interface ServeStats {
  ace_rate: number;
  df_rate: number;
  first_serve_pct: number;
  first_serve_win_pct: number;
  second_serve_win_pct: number;
  return_win_pct: number;
  charted_matches: number;
  has_data: boolean;
}

export interface PlayerDetail {
  id: number;
  name: string;
  elo_overall: number;
  elo_hard: number;
  elo_clay: number;
  elo_grass: number;
  current_rank: number | null;
  current_pts: number | null;
  matches_played: number;
  wins: number;
  win_rate_overall: number;
  win_rate_hard: number;
  win_rate_clay: number;
  win_rate_grass: number;
  matches_hard: number;
  matches_clay: number;
  matches_grass: number;
  recent_matches: RecentMatch[];
  elo_history: EloHistoryPoint[];
  serve_stats: ServeStats | null;
}

export interface PlayerPredictInfo {
  id: number;
  name: string;
  win_probability: number;
  elo: number;
  surface_elo: number;
  rank: number | null;
  win_rate_overall: number;
  win_rate_surface: number;
}

export interface H2HInfo {
  p1_wins: number;
  p2_wins: number;
  total: number;
  surface_p1_wins: number;
  surface_total: number;
}

export interface KeyFactor {
  feature: string;
  p1_value: string | number;
  p2_value: string | number;
  advantage: string;
  margin: string | number;
}

export interface PredictResponse {
  player1: PlayerPredictInfo;
  player2: PlayerPredictInfo;
  head_to_head: H2HInfo;
  key_factors: KeyFactor[];
  confidence: "high" | "medium" | "low";
  analysis: string | null;
  surface: string;
  series: string;
  round: string;
  best_of: number;
  tournament?: string;
}

export interface LeaderboardEntry {
  rank: number;
  player_id: number;
  name: string;
  elo: number;
  wins: number;
  matches_played: number;
  win_rate: number;
  win_rate_hard: number;
  win_rate_clay: number;
  win_rate_grass: number;
  elo_change: number;
}

export interface TrendingEntry {
  rank: number;
  player_id: number;
  name: string;
  elo: number;
  current_rank: number | null;
  recent_wins: number;
  recent_matches: number;
  recent_win_rate: number;
  overall_win_rate: number;
  streak: number;
}

export interface MatchSummary {
  id: number;
  tournament: string;
  date: string;
  surface: string;
  series: string;
  round: string;
  player1_name: string;
  player2_name: string;
  winner_name: string;
  score: string | null;
  rank1: number | null;
  rank2: number | null;
}

export interface TournamentSummary {
  name: string;
  year: number;
  series: string;
  surface: string;
  match_count: number;
}

export interface BracketMatch {
  id: number;
  player1_name: string;
  player2_name: string;
  winner_name: string;
  score: string | null;
  rank1: number | null;
  rank2: number | null;
}

export interface BracketRound {
  round_name: string;
  matches: BracketMatch[];
}

export interface TournamentBracket {
  name: string;
  year: number;
  series: string;
  surface: string;
  rounds: BracketRound[];
}

export interface PredictionLogEntry {
  id: number;
  created_at: string;
  player1_name: string;
  player2_name: string;
  surface: string;
  series: string;
  best_of: number;
  round: string | null;
  p1_win_prob: number;
  was_correct: boolean | null;
}

export interface H2HMatch {
  id: number;
  date: string;
  tournament: string;
  surface: string;
  series: string;
  round: string;
  winner_name: string;
  score: string | null;
  rank1: number | null;
  rank2: number | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface CalibrationBucket {
  bucket_label: string;
  predicted_avg: number;
  actual_rate: number;
  count: number;
}

export interface FeaturedMatch {
  player1_id: number;
  player1_name: string;
  player2_id: number;
  player2_name: string;
  surface: string;
  date: string;
  winner_name: string;
  score: string | null;
}

export interface SimulatedPlayer {
  player_id: number;
  name: string;
}

export interface SimulatedMatch {
  player1: SimulatedPlayer;
  player2: SimulatedPlayer;
  expected_winner: SimulatedPlayer;
  win_prob: number;
}

export interface SimulatedRound {
  round_name: string;
  matches: SimulatedMatch[];
}

export interface TitleProbability {
  player_id: number;
  name: string;
  probability: number;
}

export interface SimulateBracketRequest {
  player_ids: number[];
  surface: string;
  series: string;
  best_of: number;
}

export interface SimulateBracketResponse {
  rounds: SimulatedRound[];
  title_probabilities: TitleProbability[];
}
