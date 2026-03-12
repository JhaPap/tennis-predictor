"use client";

import { use } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getTournamentBracket } from "@/lib/api";
import { SERIES_BADGE, SURFACE_COLORS, cn } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";

export default function TournamentPage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = use(params);
  const searchParams = useSearchParams();
  const year = Number(searchParams.get("year") || 2024);

  const decodedName = decodeURIComponent(name);

  const { data: bracket, isLoading } = useQuery({
    queryKey: ["bracket", decodedName, year],
    queryFn: () => getTournamentBracket(decodedName, year),
  });

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!bracket) {
    return <div className="text-muted-foreground">Tournament not found.</div>;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-7">
      <div className="flex items-center gap-3">
        <Link href="/tournaments">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Tournaments
          </Button>
        </Link>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{bracket.name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <Badge
              className={cn(
                SERIES_BADGE[bracket.series] || "bg-gray-100 text-gray-800"
              )}
            >
              {bracket.series}
            </Badge>
            <span
              className={cn(
                "px-2 py-0.5 rounded text-white text-xs",
                SURFACE_COLORS[bracket.surface] || "bg-gray-400"
              )}
            >
              {bracket.surface}
            </span>
            <span className="text-muted-foreground text-sm">{bracket.year}</span>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {bracket.rounds.map((round) => (
          <Card key={round.round_name}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">
                {round.round_name} ({round.matches.length} matches)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {round.matches.map((m) => (
                  <div
                    key={m.id}
                    className="bg-muted/40 rounded-lg px-3 py-2 text-sm"
                  >
                    <div className="flex justify-between">
                      <span
                        className={cn(
                          m.winner_name === m.player1_name
                            ? "font-semibold"
                            : "text-muted-foreground"
                        )}
                      >
                        {m.player1_name}
                        {m.rank1 ? (
                          <span className="text-xs text-muted-foreground ml-1">
                            ({m.rank1})
                          </span>
                        ) : null}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span
                        className={cn(
                          m.winner_name === m.player2_name
                            ? "font-semibold"
                            : "text-muted-foreground"
                        )}
                      >
                        {m.player2_name}
                        {m.rank2 ? (
                          <span className="text-xs text-muted-foreground ml-1">
                            ({m.rank2})
                          </span>
                        ) : null}
                      </span>
                      {m.score && (
                        <span className="text-xs text-muted-foreground">
                          {m.score}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
