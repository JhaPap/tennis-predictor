"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, formatDate, SURFACE_COLORS } from "@/lib/utils";
import { H2HInfo } from "@/lib/types";
import { getH2HMatches } from "@/lib/api";
import { ChevronRight } from "lucide-react";

interface HeadToHeadCardProps {
  h2h: H2HInfo;
  p1Id: number;
  p2Id: number;
  p1Name: string;
  p2Name: string;
  surface: string;
}

export default function HeadToHeadCard({
  h2h,
  p1Id,
  p2Id,
  p1Name,
  p2Name,
  surface,
}: HeadToHeadCardProps) {
  const [open, setOpen] = useState(false);

  const { data: matches = [], isLoading } = useQuery({
    queryKey: ["h2h-matches", p1Id, p2Id],
    queryFn: () => getH2HMatches(p1Id, p2Id),
    enabled: open,
    staleTime: Infinity,
  });

  if (h2h.total === 0) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Head to Head</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No previous meetings.</p>
        </CardContent>
      </Card>
    );
  }

  const p1Pct = Math.round((h2h.p1_wins / h2h.total) * 100);
  const p2Pct = 100 - p1Pct;
  const p1Leads = h2h.p1_wins >= h2h.p2_wins;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Card className="h-full cursor-pointer hover:ring-1 hover:ring-primary/40 transition-all group">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center justify-between">
              <span>
                Head to Head
                <span className="text-muted-foreground font-normal ml-1.5">
                  {h2h.total} matches
                </span>
              </span>
              <span className="text-xs font-normal text-primary opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-0.5">
                View all <ChevronRight className="h-3 w-3" />
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-end">
              <div>
                <div className="text-xs text-muted-foreground">{p1Name.split(" ")[0]}</div>
                <div className={cn(
                  "text-2xl font-bold tabular-nums",
                  p1Leads ? "text-green-600" : "text-red-500"
                )}>
                  {h2h.p1_wins}
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground">{p2Name.split(" ")[0]}</div>
                <div className={cn(
                  "text-2xl font-bold tabular-nums",
                  !p1Leads ? "text-green-600" : "text-red-500"
                )}>
                  {h2h.p2_wins}
                </div>
              </div>
            </div>
            <div className="h-3 rounded-full overflow-hidden flex gap-0.5">
              <div
                className={cn(
                  "rounded-l-full transition-all",
                  p1Leads ? "bg-green-500" : "bg-red-400"
                )}
                style={{ width: `${p1Pct}%` }}
              />
              <div
                className={cn(
                  "rounded-r-full transition-all",
                  !p1Leads ? "bg-green-500" : "bg-red-400"
                )}
                style={{ width: `${p2Pct}%` }}
              />
            </div>
            {h2h.surface_total > 0 && (
              <div className="rounded-lg bg-muted/50 px-3 py-2">
                <p className="text-xs text-muted-foreground">
                  On {surface}:{" "}
                  <span className="font-semibold text-foreground">
                    {h2h.surface_p1_wins}–{h2h.surface_total - h2h.surface_p1_wins}
                  </span>
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </DialogTrigger>

      <DialogContent className="max-w-lg max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>
            {p1Name.split(" ")[0]} vs {p2Name.split(" ")[0]}
            <span className="text-muted-foreground font-normal text-sm ml-2">
              — {h2h.total} meetings
            </span>
          </DialogTitle>
        </DialogHeader>

        <div className="overflow-y-auto flex-1 -mx-6 px-6">
          {isLoading ? (
            <div className="space-y-2 py-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : (
            <div className="space-y-2 py-1">
              {matches.map((m) => {
                const p1Won = m.winner_name === p1Name;
                const winnerShort = m.winner_name.split(" ")[0];
                return (
                  <div
                    key={m.id}
                    className="rounded-lg border bg-card px-4 py-3 space-y-2"
                  >
                    {/* Top row: tournament + date */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-medium leading-tight truncate">
                          {m.tournament}
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {m.round} · {formatDate(m.date)}
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-white text-[10px] font-medium",
                            SURFACE_COLORS[m.surface] || "bg-gray-400"
                          )}
                        >
                          {m.surface}
                        </span>
                      </div>
                    </div>

                    {/* Score + winner */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "text-xs font-bold px-2 py-0.5 rounded",
                            p1Won
                              ? "bg-green-500/15 text-green-700"
                              : "bg-red-500/15 text-red-600"
                          )}
                        >
                          {winnerShort} won
                        </span>
                        {m.score && (
                          <span className="text-sm font-mono text-foreground">
                            {m.score}
                          </span>
                        )}
                      </div>
                      {/* Rankings at the time */}
                      {(m.rank1 || m.rank2) && (
                        <span className="text-[11px] text-muted-foreground">
                          #{m.rank1 ?? "–"} vs #{m.rank2 ?? "–"}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
