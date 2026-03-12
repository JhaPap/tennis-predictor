import {
  AuthResponse,
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
  User,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    // Pydantic 422 validation errors return detail as an array
    const detail = error.detail;
    if (Array.isArray(detail)) {
      throw new Error(detail[0]?.msg || "Validation error");
    }
    throw new Error(detail || "API error");
  }
  return res.json();
}

// Auth
export const register = (body: {
  email: string;
  username: string;
  password: string;
}) =>
  apiFetch<User>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const login = async (body: {
  email: string;
  password: string;
}): Promise<AuthResponse> => {
  const data = await apiFetch<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (typeof window !== "undefined") {
    localStorage.setItem("auth_token", data.access_token);
    document.cookie = `auth_token=${data.access_token}; path=/; max-age=${7 * 24 * 3600}; SameSite=Lax`;
  }
  return data;
};

export const verifyEmail = (token: string) =>
  apiFetch<{ message: string }>("/api/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });

export const resendVerification = (email: string) =>
  apiFetch<{ message: string }>("/api/auth/resend-verification", {
    method: "POST",
    body: JSON.stringify({ email }),
  });

export const getCurrentUser = () => apiFetch<User>("/api/auth/me");

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
