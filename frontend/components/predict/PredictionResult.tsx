"use client";

import { useState } from "react";
import { PredictResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatPct, formatElo, cn } from "@/lib/utils";
import { Crown, Sparkles, Loader2, AlertTriangle } from "lucide-react";
import HeadToHeadCard from "./HeadToHeadCard";
import { fetchMatchAnalysis } from "@/lib/api";

const CONFIDENCE_COLORS = {
  high: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-red-100 text-red-800",
};

interface PredictionResultProps {
  result: PredictResponse;
  requestParams: {
    player1_id: number;
    player2_id: number;
    surface: string;
    series: string;
    round: string;
    best_of: number;
    tournament?: string;
  };
}

export default function PredictionResult({ result, requestParams }: PredictionResultProps) {
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  async function handleGenerateAnalysis() {
    setLoadingAnalysis(true);
    try {
      const res = await fetchMatchAnalysis(requestParams);
      setAnalysis(res.analysis);
    } catch {
      // silently fail
    } finally {
      setLoadingAnalysis(false);
    }
  }

  const { player1, player2, head_to_head, key_factors, confidence } = result;
  const p1Pct = player1.win_probability * 100;
  const p2Pct = player2.win_probability * 100;
  const p1Wins = p1Pct >= p2Pct;

  // Upset alert: underdog (higher rank number) has ≥40% win probability
  const p1IsUnderdog =
    player1.rank !== null && player2.rank !== null && player1.rank > player2.rank;
  const p2IsUnderdog =
    player1.rank !== null && player2.rank !== null && player2.rank > player1.rank;
  const isUpsetAlert =
    (p1IsUnderdog && p1Pct >= 40) || (p2IsUnderdog && p2Pct >= 40);

  return (
    <div className="space-y-5">
      {/* Main probability display */}
      <Card>
        <CardContent className="pt-6 space-y-5">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Win Probability
            </span>
            <div className="flex items-center gap-2">
              {isUpsetAlert && (
                <Badge className="bg-orange-100 text-orange-700 border-orange-200 flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  Upset Alert
                </Badge>
              )}
              <Badge className={CONFIDENCE_COLORS[confidence]}>
                {confidence} confidence
              </Badge>
            </div>
          </div>

          {/* Winner callout */}
          <div className="flex items-center justify-center gap-2 py-2">
            <Crown className="h-5 w-5 text-green-500" />
            <span className="text-lg font-bold text-green-600">
              {p1Wins ? player1.name : player2.name}
            </span>
            <span className="text-sm text-muted-foreground">predicted to win</span>
          </div>

          {/* Player percentages */}
          <div className="flex justify-between items-end">
            <div className="text-left">
              <div className={cn(
                "text-sm font-semibold",
                p1Wins ? "text-green-600" : "text-red-500"
              )}>
                {player1.name}
              </div>
              <div className={cn(
                "text-3xl font-bold tabular-nums",
                p1Wins ? "text-green-600" : "text-red-500"
              )}>
                {formatPct(p1Pct)}
              </div>
            </div>
            <div className="text-right">
              <div className={cn(
                "text-sm font-semibold",
                !p1Wins ? "text-green-600" : "text-red-500"
              )}>
                {player2.name}
              </div>
              <div className={cn(
                "text-3xl font-bold tabular-nums",
                !p1Wins ? "text-green-600" : "text-red-500"
              )}>
                {formatPct(p2Pct)}
              </div>
            </div>
          </div>

          {/* Probability bar */}
          <div className="h-5 rounded-full overflow-hidden flex gap-0.5">
            <div
              className={cn(
                "rounded-l-full transition-all duration-500",
                p1Wins ? "bg-green-500" : "bg-red-400"
              )}
              style={{ width: `${p1Pct}%` }}
            />
            <div
              className={cn(
                "rounded-r-full transition-all duration-500",
                !p1Wins ? "bg-green-500" : "bg-red-400"
              )}
              style={{ width: `${p2Pct}%` }}
            />
          </div>
        </CardContent>
      </Card>

      {/* AI Analysis */}
      {analysis ? (
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader className="pb-2 pt-4">
            <CardTitle className="text-sm flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Match Analysis
              <Badge variant="outline" className="ml-auto text-[10px] font-normal text-muted-foreground">
                AI · Claude
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-sm text-muted-foreground leading-relaxed">{analysis}</p>
          </CardContent>
        </Card>
      ) : (
        <Button
          variant="outline"
          className="w-full"
          onClick={handleGenerateAnalysis}
          disabled={loadingAnalysis}
        >
          {loadingAnalysis ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating analysis...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Generate AI Analysis
            </>
          )}
        </Button>
      )}

      {/* Stats + H2H side by side */}
      <div className="grid gap-5 md:grid-cols-2">
        {/* Stats comparison */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Stats Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Column headers */}
            <div className="flex items-center gap-3 mb-4 pb-3 border-b">
              <span className="w-20 text-xs font-semibold truncate">
                {player1.name.split(" ")[0]}
              </span>
              <span className="flex-1 text-center text-xs text-muted-foreground">
                Stat
              </span>
              <span className="w-20 text-xs font-semibold text-right truncate">
                {player2.name.split(" ")[0]}
              </span>
            </div>
            <div className="space-y-3">
              {[
                {
                  label: "Elo Rating",
                  v1: formatElo(player1.elo),
                  v2: formatElo(player2.elo),
                  raw1: player1.elo,
                  raw2: player2.elo,
                },
                {
                  label: `${result.surface} Elo`,
                  v1: formatElo(player1.surface_elo),
                  v2: formatElo(player2.surface_elo),
                  raw1: player1.surface_elo,
                  raw2: player2.surface_elo,
                },
                {
                  label: "ATP Rank",
                  v1: player1.rank ? `#${player1.rank}` : "–",
                  v2: player2.rank ? `#${player2.rank}` : "–",
                  raw1: player1.rank ? -player1.rank : -Infinity,
                  raw2: player2.rank ? -player2.rank : -Infinity,
                },
                {
                  label: "Overall Win %",
                  v1: formatPct(player1.win_rate_overall),
                  v2: formatPct(player2.win_rate_overall),
                  raw1: player1.win_rate_overall,
                  raw2: player2.win_rate_overall,
                },
                {
                  label: `${result.surface} Win %`,
                  v1: formatPct(player1.win_rate_surface),
                  v2: formatPct(player2.win_rate_surface),
                  raw1: player1.win_rate_surface,
                  raw2: player2.win_rate_surface,
                },
              ].map(({ label, v1, v2, raw1, raw2 }) => {
                const p1Better = raw1 > raw2;
                const even = raw1 === raw2;
                return (
                  <div key={label}>
                    <div className="flex items-center gap-3">
                      <span
                        className={cn(
                          "w-20 text-sm font-semibold tabular-nums",
                          even
                            ? "text-muted-foreground"
                            : p1Better
                            ? "text-green-600"
                            : "text-red-500"
                        )}
                      >
                        {v1}
                      </span>
                      <span className="flex-1 text-center text-xs text-muted-foreground">
                        {label}
                      </span>
                      <span
                        className={cn(
                          "w-20 text-sm font-semibold tabular-nums text-right",
                          even
                            ? "text-muted-foreground"
                            : !p1Better
                            ? "text-green-600"
                            : "text-red-500"
                        )}
                      >
                        {v2}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* H2H */}
        <HeadToHeadCard
          h2h={head_to_head}
          p1Id={player1.id}
          p2Id={player2.id}
          p1Name={player1.name}
          p2Name={player2.name}
          surface={result.surface}
        />
      </div>

      {/* Key factors */}
      {key_factors.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Key Factors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-2">
              {key_factors.map((factor, i) => {
                const isEven = factor.advantage === "Even";
                const favorsP1 =
                  !isEven && factor.advantage === player1.name;
                return (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2 text-sm"
                  >
                    <span className="text-muted-foreground">
                      {factor.feature}
                    </span>
                    {isEven ? (
                      <span className="text-xs text-muted-foreground font-medium">
                        Even
                      </span>
                    ) : (
                      <span
                        className={cn(
                          "text-xs font-semibold",
                          favorsP1 === p1Wins ? "text-green-600" : "text-red-500"
                        )}
                      >
                        {factor.advantage.split(" ")[0]} +{factor.margin}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
