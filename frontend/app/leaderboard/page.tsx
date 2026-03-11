"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getTrending } from "@/lib/api";
import { Flame } from "lucide-react";

export default function LeaderboardPage() {
  const { data: players = [], isLoading } = useQuery({
    queryKey: ["trending"],
    queryFn: () => getTrending(50),
    staleTime: 60_000,
  });

  return (
    <div className="max-w-5xl mx-auto space-y-7">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">On the Rise</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Players getting hot — ranked by win rate over their last 20 matches.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 20 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : (
        <div className="rounded-xl shadow-sm">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <TableHead>Player</TableHead>
                <TableHead className="text-right">Elo</TableHead>
                <TableHead className="text-right">Recent W/L</TableHead>
                <TableHead className="text-right">Recent Win %</TableHead>
                <TableHead className="text-right">Overall Win %</TableHead>
                <TableHead className="text-center">Streak</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {players.map((p) => (
                <TableRow key={p.player_id} className="hover:bg-muted/50">
                  <TableCell className="text-muted-foreground text-sm">
                    {p.rank}
                  </TableCell>
                  <TableCell>
                    <Link
                      href={`/players/${p.player_id}`}
                      className="font-medium hover:text-primary hover:underline"
                    >
                      {p.name}
                    </Link>
                    {p.current_rank && (
                      <span className="text-xs text-muted-foreground ml-2">
                        #{p.current_rank}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {Math.round(p.elo).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right text-sm text-muted-foreground">
                    {p.recent_wins}–{p.recent_matches - p.recent_wins}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {p.recent_win_rate.toFixed(1)}%
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    {p.overall_win_rate.toFixed(1)}%
                  </TableCell>
                  <TableCell className="text-center">
                    {p.streak > 0 ? (
                      <Badge className="bg-green-100 text-green-800 text-xs">
                        <Flame className="h-3 w-3 mr-0.5" />
                        W{p.streak}
                      </Badge>
                    ) : p.streak < 0 ? (
                      <Badge variant="outline" className="text-xs text-muted-foreground">
                        L{Math.abs(p.streak)}
                      </Badge>
                    ) : null}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
