import {
  CalibrationBucket,
  FeaturedMatch,
  H2HMatch,
  LeaderboardEntry,
  MatchSummary,
  PaginatedResponse,
  PlayerDetail,
  PlayerSummary,
  PredictResponse,
  PredictionLogEntry,
  SimulateBracketRequest,
  SimulateBracketResponse,
  TournamentBracket,
  TournamentSummary,
  TrendingEntry,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API error");
  }
  return res.json();
}

// Players
export const searchPlayers = (search: string, limit = 20) =>
  apiFetch<PlayerSummary[]>(`/api/players?search=${encodeURIComponent(search)}&limit=${limit}`);

export const getPlayer = (id: number) =>
  apiFetch<PlayerDetail>(`/api/players/${id}`);

// Predictions
export const predictMatch = (body: {
  player1_id: number;
  player2_id: number;
  surface: string;
  series: string;
  round: string;
  best_of: number;
  tournament?: string;
}) =>
  apiFetch<PredictResponse>("/api/predict", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const fetchMatchAnalysis = (body: {
  player1_id: number;
  player2_id: number;
  surface: string;
  series: string;
  round: string;
  best_of: number;
  tournament?: string;
}) =>
  apiFetch<{ analysis: string | null }>("/api/predict/analysis", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const getPredictionHistory = (page = 1, limit = 20) =>
  apiFetch<PaginatedResponse<PredictionLogEntry>>(
    `/api/predict/history?page=${page}&limit=${limit}`
  );

// Matches
export const getMatches = (params: {
  player_id?: number;
  surface?: string;
  year?: number;
  page?: number;
  limit?: number;
}) => {
  const q = new URLSearchParams();
  if (params.player_id) q.set("player_id", String(params.player_id));
  if (params.surface) q.set("surface", params.surface);
  if (params.year) q.set("year", String(params.year));
  if (params.page) q.set("page", String(params.page));
  if (params.limit) q.set("limit", String(params.limit));
  return apiFetch<PaginatedResponse<MatchSummary>>(`/api/matches?${q}`);
};

// Leaderboard
export const getLeaderboard = (surface = "overall", metric = "elo", limit = 50) =>
  apiFetch<LeaderboardEntry[]>(
    `/api/leaderboard?surface=${surface}&metric=${metric}&limit=${limit}`
  );

// Trending
export const getTrending = (limit = 50) =>
  apiFetch<TrendingEntry[]>(`/api/leaderboard/trending?limit=${limit}`);

// Tournaments
export const getTournaments = (year?: number, series?: string) => {
  const q = new URLSearchParams();
  if (year) q.set("year", String(year));
  if (series) q.set("series", series);
  return apiFetch<TournamentSummary[]>(`/api/tournaments?${q}`);
};

export const getTournamentBracket = (name: string, year: number) =>
  apiFetch<TournamentBracket>(
    `/api/tournaments/${encodeURIComponent(name)}/${year}/bracket`
  );

// H2H detail
export const getH2HMatches = (p1Id: number, p2Id: number) =>
  apiFetch<H2HMatch[]>(`/api/predict/h2h?p1_id=${p1Id}&p2_id=${p2Id}`);

// Calibration
export const getCalibration = () =>
  apiFetch<CalibrationBucket[]>("/api/predict/calibration");

// Featured Matches
export const getFeaturedMatches = (limit = 5) =>
  apiFetch<FeaturedMatch[]>(`/api/matches/featured?limit=${limit}`);

// Bracket Simulator
export const simulateBracket = (body: SimulateBracketRequest) =>
  apiFetch<SimulateBracketResponse>("/api/simulate/bracket", {
    method: "POST",
    body: JSON.stringify(body),
  });
