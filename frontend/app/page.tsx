"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getLeaderboard, getTrending, getPredictionHistory, getFeaturedMatches } from "@/lib/api";
import { formatElo, formatPct, SURFACE_COLORS } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Trophy,
  TrendingUp,
  Zap,
  Flame,
  ChevronRight,
  ArrowRight,
  ChevronDown,
  Swords,
} from "lucide-react";

export default function Home() {
  const { data: topPlayers = [], isLoading: loadingTop } = useQuery({
    queryKey: ["dashboard-top"],
    queryFn: () => getLeaderboard("overall", "elo", 5),
    staleTime: 60_000,
  });

  const { data: trending = [], isLoading: loadingTrending } = useQuery({
    queryKey: ["dashboard-trending"],
    queryFn: () => getTrending(5),
    staleTime: 60_000,
  });

  const { data: recentPredictions } = useQuery({
    queryKey: ["dashboard-predictions"],
    queryFn: () => getPredictionHistory(1, 3),
    staleTime: 30_000,
  });

  const { data: featuredMatches = [], isLoading: loadingFeatured } = useQuery({
    queryKey: ["dashboard-featured"],
    queryFn: () => getFeaturedMatches(5),
    staleTime: 60_000,
  });

  const predictions = recentPredictions?.items ?? [];

  return (
    <div className="relative mx-auto max-w-5xl">
      {/* Page-level background texture */}
      <div className="fixed inset-0 -z-20 bg-gradient-to-br from-primary/[0.06] via-transparent to-blue-500/[0.06]" />
      <div
        className="fixed inset-0 -z-20 opacity-[0.10]"
        style={{
          backgroundImage: "radial-gradient(circle, oklch(0.93 0.01 82 / 0.6) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />

      {/* Hero — fills most of the viewport */}
      <section className="relative flex flex-col items-center justify-center text-center min-h-[calc(100vh-10rem)] py-16 space-y-8">
        {/* Animated background accents */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          {/* Large slow-moving blobs */}
          <div
            className="absolute -top-24 -left-24 h-80 w-80 rounded-full bg-primary/20 blur-3xl"
            style={{ animation: "float-1 20s ease-in-out infinite" }}
          />
          <div
            className="absolute -bottom-16 -right-16 h-72 w-72 rounded-full bg-blue-500/20 blur-3xl"
            style={{ animation: "float-2 18s ease-in-out infinite" }}
          />
          <div
            className="absolute top-1/3 right-1/4 h-56 w-56 rounded-full bg-destructive/15 blur-3xl"
            style={{ animation: "float-3 22s ease-in-out infinite" }}
          />

          {/* Smaller vibrant orbs */}
          <div
            className="absolute top-[15%] left-[20%] h-28 w-28 rounded-full bg-primary/30 blur-2xl"
            style={{ animation: "float-4 15s ease-in-out infinite" }}
          />
          <div
            className="absolute top-[60%] right-[15%] h-20 w-20 rounded-full bg-cyan-400/25 blur-2xl"
            style={{ animation: "float-5 17s ease-in-out infinite" }}
          />
          <div
            className="absolute top-[40%] left-[55%] h-24 w-24 rounded-full bg-blue-400/20 blur-2xl"
            style={{ animation: "float-1 25s ease-in-out infinite reverse" }}
          />
          <div
            className="absolute top-[25%] right-[35%] h-16 w-16 rounded-full bg-primary/25 blur-xl"
            style={{ animation: "float-2 13s ease-in-out infinite reverse" }}
          />
          <div
            className="absolute bottom-[20%] left-[10%] h-32 w-32 rounded-full bg-cyan-300/15 blur-2xl"
            style={{ animation: "float-3 19s ease-in-out infinite reverse" }}
          />
        </div>

        <div className="space-y-5 max-w-2xl">
          <div className="inline-flex items-center gap-2 rounded-sm bg-primary/15 border border-primary/30 px-4 py-1.5 text-xs font-bold text-primary uppercase tracking-widest">
            <Zap className="h-3 w-3" />
            ML-Powered Predictions
          </div>
          <h1 className="text-5xl sm:text-6xl font-black tracking-tight leading-none uppercase">
            Who wins{" "}
            <span className="text-primary">the match?</span>
          </h1>
          <p className="text-muted-foreground text-base sm:text-lg leading-relaxed max-w-xl mx-auto">
            Choose any two ATP players, set the surface and round, and get an
            instant win probability — built on 25 years of professional
            tennis data and 37 predictive features.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <Link
            href="/predict"
            className="inline-flex items-center gap-2 rounded-sm bg-primary px-7 py-3 text-sm font-black uppercase tracking-wider text-primary-foreground shadow-lg shadow-primary/30 hover:shadow-primary/50 hover:scale-[1.03] transition-all"
          >
            <Zap className="h-4 w-4" />
            Make a Prediction
          </Link>
          <Link
            href="/about"
            className="inline-flex items-center gap-2 rounded-sm border border-border px-7 py-3 text-sm font-medium text-muted-foreground hover:border-primary/40 hover:text-foreground transition-all"
          >
            How it works
          </Link>
        </div>
        <a
          href="#dashboard"
          className="mt-8 text-muted-foreground/40 hover:text-primary transition-colors"
        >
          <ChevronDown className="h-5 w-5 animate-bounce" />
        </a>
      </section>

      {/* Dashboard — below the fold */}
      <div id="dashboard" className="space-y-8 pb-8">
        {/* Top Rated + On the Rise */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2 uppercase tracking-wider font-bold">
                <Trophy className="h-4 w-4 text-yellow-400" />
                Top Rated
              </CardTitle>
              <Link
                href="/players"
                className="text-xs font-medium text-primary hover:text-primary/80 inline-flex items-center gap-0.5 transition-colors"
              >
                All <ChevronRight className="h-3 w-3" />
              </Link>
            </CardHeader>
            <CardContent>
              {loadingTop ? (
                <div className="space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="h-9 rounded bg-muted animate-pulse" />
                  ))}
                </div>
              ) : (
                <ol className="space-y-0.5">
                  {topPlayers.map((p, i) => (
                    <li key={p.player_id}>
                      <Link
                        href={`/players/${p.player_id}`}
                        className="flex items-center justify-between rounded-sm px-2 py-2 hover:bg-accent transition-colors group"
                      >
                        <div className="flex items-center gap-2.5">
                          <span
                            className={`flex items-center justify-center h-5 w-5 rounded-sm text-[10px] font-bold ${
                              i === 0
                                ? "bg-yellow-500/25 text-yellow-300"
                                : i === 1
                                ? "bg-slate-400/20 text-slate-300"
                                : i === 2
                                ? "bg-orange-500/25 text-orange-300"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {p.rank}
                          </span>
                          <span className="text-sm font-medium group-hover:text-primary transition-colors">
                            {p.name}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                          <span className="text-xs text-muted-foreground">
                            {formatPct(p.win_rate)}
                          </span>
                          <Badge variant="secondary" className="font-mono text-[10px] px-1.5">
                            {formatElo(p.elo)}
                          </Badge>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ol>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2 uppercase tracking-wider font-bold">
                <TrendingUp className="h-4 w-4 text-orange-400" />
                On the Rise
              </CardTitle>
              <Link
                href="/leaderboard"
                className="text-xs font-medium text-orange-400 hover:text-orange-300 inline-flex items-center gap-0.5 transition-colors"
              >
                All <ChevronRight className="h-3 w-3" />
              </Link>
            </CardHeader>
            <CardContent>
              {loadingTrending ? (
                <div className="space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="h-9 rounded bg-muted animate-pulse" />
                  ))}
                </div>
              ) : (
                <ol className="space-y-0.5">
                  {trending.map((p) => (
                    <li key={p.player_id}>
                      <Link
                        href={`/players/${p.player_id}`}
                        className="flex items-center justify-between rounded-sm px-2 py-2 hover:bg-accent transition-colors group"
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="flex items-center justify-center h-5 w-5 rounded-sm bg-orange-500/20 text-orange-400 text-[10px] font-bold">
                            {p.rank}
                          </span>
                          <span className="text-sm font-medium group-hover:text-orange-400 transition-colors">
                            {p.name}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">
                            {formatPct(p.recent_win_rate)}
                          </span>
                          {p.streak > 0 && (
                            <Badge className="bg-gradient-to-r from-orange-500 to-red-500 text-white border-0 text-[10px] gap-0.5 px-1.5">
                              <Flame className="h-2.5 w-2.5" />
                              {p.streak}W
                            </Badge>
                          )}
                        </div>
                      </Link>
                    </li>
                  ))}
                </ol>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Featured Matchups */}
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2 uppercase tracking-wider font-bold">
              <Swords className="h-4 w-4 text-blue-400" />
              Recent Top Matchups
            </CardTitle>
            <Link
              href="/predict"
              className="text-xs font-medium text-blue-400 hover:text-blue-300 inline-flex items-center gap-0.5 transition-colors"
            >
              Predict <ChevronRight className="h-3 w-3" />
            </Link>
          </CardHeader>
          <CardContent>
            {loadingFeatured ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-9 rounded bg-muted animate-pulse" />
                ))}
              </div>
            ) : featuredMatches.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No recent matchups found.</p>
            ) : (
              <div className="divide-y divide-border">
                {featuredMatches.map((m, i) => (
                  <div key={i} className="flex items-center justify-between py-2.5 first:pt-0 last:pb-0">
                    <div className="min-w-0">
                      <span className="text-sm font-medium">
                        {m.player1_name.split(" ")[0]} vs {m.player2_name.split(" ")[0]}
                      </span>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span
                          className={`px-1.5 py-0.5 rounded text-white text-[10px] ${
                            SURFACE_COLORS[m.surface] || "bg-gray-400"
                          }`}
                        >
                          {m.surface}
                        </span>
                        <span className="text-[11px] text-muted-foreground">
                          {m.winner_name.split(" ")[0]} won
                        </span>
                      </div>
                    </div>
                    <Link
                      href={`/predict?p1=${m.player1_id}&p2=${m.player2_id}`}
                      className="shrink-0 ml-3 text-xs font-medium text-blue-400 hover:text-blue-300 inline-flex items-center gap-0.5 transition-colors"
                    >
                      Predict <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Predictions */}
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2 uppercase tracking-wider font-bold">
              <Zap className="h-4 w-4 text-cyan-400" />
              Recent Predictions
            </CardTitle>
            <Link
              href="/history"
              className="text-xs font-medium text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-0.5 transition-colors"
            >
              All <ChevronRight className="h-3 w-3" />
            </Link>
          </CardHeader>
          <CardContent>
            {predictions.length === 0 ? (
              <div className="text-center py-8 space-y-2">
                <p className="text-sm text-muted-foreground">No predictions yet.</p>
                <Link
                  href="/predict"
                  className="inline-flex items-center gap-1 text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  Make your first prediction <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {predictions.map((pred) => {
                  const p1Wins = pred.p1_win_prob > 0.5;
                  const winnerName = p1Wins ? pred.player1_name : pred.player2_name;
                  const pct = Math.round((p1Wins ? pred.p1_win_prob : 1 - pred.p1_win_prob) * 100);
                  return (
                    <div key={pred.id} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
                      <div>
                        <span className="text-sm font-medium">
                          {pred.player1_name.split(" ")[0]} vs {pred.player2_name.split(" ")[0]}
                        </span>
                        <span className="text-xs text-muted-foreground ml-2">
                          {pred.surface} · {winnerName.split(" ")[0]} favored
                        </span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {pred.was_correct !== null && (
                          <Badge
                            variant="secondary"
                            className={`text-[10px] px-1.5 ${
                              pred.was_correct
                                ? "bg-green-500/20 text-green-400 border-green-500/30"
                                : "bg-red-500/20 text-red-400 border-red-500/30"
                            }`}
                          >
                            {pred.was_correct ? "Correct" : "Wrong"}
                          </Badge>
                        )}
                        <span className="text-sm font-bold text-cyan-400 tabular-nums">
                          {pct}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
