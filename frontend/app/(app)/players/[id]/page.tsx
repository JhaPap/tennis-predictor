"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import SurfaceBreakdown from "@/components/players/SurfaceBreakdown";
import EloChart from "@/components/players/EloChart";
import RecentForm from "@/components/players/RecentForm";
import ServeReturnCard from "@/components/players/ServeReturnCard";
import FormHeatmap from "@/components/players/FormHeatmap";
import { getPlayer } from "@/lib/api";
import { formatElo, formatPct } from "@/lib/utils";
import { ArrowLeft, Zap } from "lucide-react";

export default function PlayerPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: player, isLoading } = useQuery({
    queryKey: ["player", id],
    queryFn: () => getPlayer(Number(id)),
  });

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!player) {
    return <div className="text-muted-foreground">Player not found.</div>;
  }

  return (
    <div className="max-w-3xl mx-auto space-y-7">
      <div className="flex items-center gap-3">
        <Link href="/players">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Players
          </Button>
        </Link>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{player.name}</h1>
          <div className="flex items-center gap-2 mt-1">
            {player.current_rank && (
              <Badge variant="outline">Rank #{player.current_rank}</Badge>
            )}
            <span className="text-sm text-muted-foreground">
              {player.matches_played} matches · {player.wins} wins ·{" "}
              {formatPct(player.win_rate_overall * 100)} win rate
            </span>
          </div>
        </div>
        <Link href={`/predict?p1=${player.id}`}>
          <Button size="sm" variant="outline">
            <Zap className="h-3.5 w-3.5 mr-1" />
            Predict
          </Button>
        </Link>
      </div>

      {/* Elo summary */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Overall Elo", value: formatElo(player.elo_overall) },
          { label: "Hard Elo", value: formatElo(player.elo_hard) },
          { label: "Clay Elo", value: formatElo(player.elo_clay) },
          { label: "Grass Elo", value: formatElo(player.elo_grass) },
        ].map(({ label, value }) => (
          <Card key={label}>
            <CardContent className="py-3 text-center">
              <div className="text-lg font-bold">{value}</div>
              <div className="text-xs text-muted-foreground">{label}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <SurfaceBreakdown player={player} />
      {player.serve_stats && <ServeReturnCard stats={player.serve_stats} />}
      <EloChart history={player.elo_history} />
      <RecentForm matches={player.recent_matches} />
      <FormHeatmap matches={player.recent_matches} />
    </div>
  );
}
