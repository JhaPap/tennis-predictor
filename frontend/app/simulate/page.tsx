"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import PlayerSelector from "@/components/predict/PlayerSelector";
import { simulateBracket } from "@/lib/api";
import { PlayerSummary, SimulateBracketResponse } from "@/lib/types";
import { Swords, Trophy } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";
import { cn } from "@/lib/utils";

const SURFACES = ["Hard", "Clay", "Grass"];
const SERIES_OPTIONS = ["ATP250", "ATP500", "Masters 1000", "Grand Slam"];

const SEED_LABELS = [
  "Seed 1", "Seed 2", "Seed 3", "Seed 4",
  "Seed 5", "Seed 6", "Seed 7", "Seed 8",
];

export default function SimulatePage() {
  const [players, setPlayers] = useState<(PlayerSummary | null)[]>(
    Array(8).fill(null)
  );
  const [surface, setSurface] = useState("Hard");
  const [series, setSeries] = useState("ATP250");
  const [bestOf, setBestOf] = useState(3);

  const mutation = useMutation({
    mutationFn: () =>
      simulateBracket({
        player_ids: players.map((p) => p!.id),
        surface,
        series,
        best_of: bestOf,
      }),
  });

  const filledCount = players.filter(Boolean).length;
  const canSimulate = filledCount === 8;

  function setPlayer(index: number, player: PlayerSummary | null) {
    setPlayers((prev) => {
      const next = [...prev];
      next[index] = player;
      return next;
    });
  }

  const result: SimulateBracketResponse | undefined = mutation.data;

  return (
    <div className="max-w-5xl mx-auto space-y-7">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Swords className="h-7 w-7 text-primary" />
          Bracket Simulator
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Select 8 players seeded 1–8, choose match conditions, and run a Monte Carlo
          simulation to estimate title probabilities.
        </p>
      </div>

      {/* Player selectors */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Player Seeds (1–8)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            {SEED_LABELS.map((label, i) => (
              <PlayerSelector
                key={i}
                label={label}
                value={players[i]}
                onChange={(p) => setPlayer(i, p)}
              />
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            {filledCount}/8 players selected
          </p>
        </CardContent>
      </Card>

      {/* Match conditions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Match Conditions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex flex-col gap-1.5 min-w-[140px]">
              <label className="text-sm font-medium text-muted-foreground">Surface</label>
              <Select value={surface} onValueChange={setSurface}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SURFACES.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5 min-w-[160px]">
              <label className="text-sm font-medium text-muted-foreground">Series</label>
              <Select value={series} onValueChange={setSeries}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SERIES_OPTIONS.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5 min-w-[120px]">
              <label className="text-sm font-medium text-muted-foreground">Best of</label>
              <Select value={String(bestOf)} onValueChange={(v) => setBestOf(Number(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="3">Best of 3</SelectItem>
                  <SelectItem value="5">Best of 5</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Button
        className="w-full h-12 text-base rounded-xl"
        disabled={!canSimulate || mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        <Swords className="mr-2 h-4 w-4" />
        {mutation.isPending ? "Simulating 10,000 brackets..." : "Simulate Tournament"}
      </Button>

      {mutation.isPending && (
        <Card>
          <CardContent className="pt-6 space-y-3">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
      )}

      {mutation.error && (
        <Card className="ring-1 ring-destructive/30">
          <CardContent className="pt-6">
            <p className="text-destructive text-sm">
              {(mutation.error as Error).message}
            </p>
          </CardContent>
        </Card>
      )}

      {result && !mutation.isPending && (
        <>
          {/* Bracket display */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Expected Bracket Progression</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-sm">
                {result.rounds.map((round) => (
                  <div key={round.round_name}>
                    <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">
                      {round.round_name}
                    </div>
                    <div className="space-y-3">
                      {round.matches.map((match, i) => (
                        <div
                          key={i}
                          className="rounded-lg border bg-card p-2.5 space-y-1.5"
                        >
                          {[match.player1, match.player2].map((player) => {
                            const isWinner = player.player_id === match.expected_winner.player_id;
                            return (
                              <div
                                key={player.player_id}
                                className={cn(
                                  "flex items-center justify-between rounded px-2 py-1 text-xs",
                                  isWinner
                                    ? "bg-green-500/15 text-green-700 font-semibold"
                                    : "text-muted-foreground"
                                )}
                              >
                                <span className="truncate">{player.name.split(" ")[0]}</span>
                                {isWinner && (
                                  <span className="ml-1 text-[10px] font-bold">
                                    {Math.round(match.win_prob * 100)}%
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Title probabilities chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Trophy className="h-4 w-4 text-yellow-400" />
                Title Probabilities (Monte Carlo · 10,000 simulations)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={result.title_probabilities.length * 44 + 40}>
                <BarChart
                  data={result.title_probabilities.map((p) => ({
                    name: p.name.split(" ")[0],
                    probability: Math.round(p.probability * 100),
                  }))}
                  layout="vertical"
                  margin={{ top: 4, right: 40, left: 60, bottom: 4 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} className="opacity-20" />
                  <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={55} />
                  <Tooltip formatter={(v: unknown) => [`${v}%`, "Title probability"]} />
                  <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                    {result.title_probabilities.map((_, i) => (
                      <Cell
                        key={i}
                        fill={i === 0 ? "#eab308" : i === 1 ? "#94a3b8" : i === 2 ? "#f97316" : "#3b6fd4"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
