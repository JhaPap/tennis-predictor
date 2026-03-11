"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import {
  TooltipRoot,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { getLeaderboard, searchPlayers } from "@/lib/api";
import { formatPct } from "@/lib/utils";
import { Search, TrendingUp, TrendingDown, HelpCircle } from "lucide-react";

function EloTrend({ change }: { change: number }) {
  if (Math.abs(change) < 5) return <span className="text-muted-foreground">—</span>;
  if (change > 0)
    return (
      <span className="flex items-center justify-end gap-0.5 text-green-600 font-semibold text-sm">
        <TrendingUp className="h-3 w-3" />+{Math.round(change)}
      </span>
    );
  return (
    <span className="flex items-center justify-end gap-0.5 text-red-500 font-semibold text-sm">
      <TrendingDown className="h-3 w-3" />{Math.round(change)}
    </span>
  );
}

const SURFACES = ["overall", "hard", "clay", "grass"] as const;

export default function PlayersPage() {
  const [view, setView] = useState<"atp" | "elo">("atp");
  const [surface, setSurface] = useState<string>("overall");
  const [search, setSearch] = useState("");

  const { data: atpPlayers = [], isLoading: isLoadingAtp } = useQuery({
    queryKey: ["players-atp"],
    queryFn: () => getLeaderboard("overall", "rank", 100),
    staleTime: 60_000,
    enabled: view === "atp",
  });

  const { data: eloPlayers = [], isLoading: isLoadingElo } = useQuery({
    queryKey: ["players-elo", surface],
    queryFn: () => getLeaderboard(surface, "elo", 100),
    staleTime: 60_000,
    enabled: view === "elo",
  });

  const { data: searchResults = [], isLoading: isSearching } = useQuery({
    queryKey: ["players-search", search],
    queryFn: () => searchPlayers(search, 50),
    enabled: search.length > 0,
    staleTime: 30_000,
  });

  const isSearchMode = search.length > 0;
  const players = view === "atp" ? atpPlayers : eloPlayers;
  const isLoading = view === "atp" ? isLoadingAtp : isLoadingElo;

  return (
    <div className="max-w-5xl mx-auto space-y-7">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Players</h1>
        <p className="text-muted-foreground text-sm mt-1">
          {view === "atp"
            ? "Current ATP top 100 by live ranking."
            : "Top 100 active players ranked by Elo rating."}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search active players..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {!isSearchMode && (
          <>
            <Tabs value={view} onValueChange={(v) => setView(v as "atp" | "elo")}>
              <TabsList>
                <TabsTrigger value="atp">ATP Ranking</TabsTrigger>
                <TabsTrigger value="elo">Elo Rating</TabsTrigger>
              </TabsList>
            </Tabs>

            {view === "elo" && (
              <Tabs value={surface} onValueChange={setSurface}>
                <TabsList>
                  {SURFACES.map((s) => (
                    <TabsTrigger key={s} value={s} className="capitalize">
                      {s}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </Tabs>
            )}
          </>
        )}
      </div>

      {isSearchMode ? (
        isSearching ? (
          <div className="space-y-2">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : (
          <div className="rounded-xl shadow-sm">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Player</TableHead>
                  <TableHead className="text-right">ATP Rank</TableHead>
                  <TableHead className="text-right">Elo</TableHead>
                  <TableHead className="text-right">Matches</TableHead>
                  <TableHead className="text-right">Win %</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {searchResults.map((p) => (
                  <TableRow key={p.id} className="hover:bg-muted/50">
                    <TableCell>
                      <Link
                        href={`/players/${p.id}`}
                        className="font-medium hover:text-primary hover:underline"
                      >
                        {p.name}
                      </Link>
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {p.current_rank ? `#${p.current_rank}` : "–"}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {Math.round(p.elo_overall).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {p.matches_played}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatPct(p.win_rate_overall * 100)}
                    </TableCell>
                  </TableRow>
                ))}
                {searchResults.length === 0 && (
                  <TableRow>
                    <TableCell
                      colSpan={5}
                      className="text-center text-muted-foreground py-8"
                    >
                      No active players found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        )
      ) : isLoading ? (
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
                {view === "atp" ? (
                  <>
                    <TableHead className="text-right">Elo</TableHead>
                    <TableHead className="text-right">
                      <TooltipRoot>
                        <TooltipTrigger className="inline-flex items-center gap-1 cursor-default">
                          Trend
                          <HelpCircle className="h-3 w-3 text-muted-foreground/60" />
                        </TooltipTrigger>
                        <TooltipContent>
                          Elo change over the player's last 20 matches — a recent form indicator, not a live ranking shift.
                        </TooltipContent>
                      </TooltipRoot>
                    </TableHead>
                    <TableHead className="text-right">W/L</TableHead>
                    <TableHead className="text-right">Win %</TableHead>
                    <TableHead className="text-right">Hard %</TableHead>
                    <TableHead className="text-right">Clay %</TableHead>
                    <TableHead className="text-right">Grass %</TableHead>
                  </>
                ) : (
                  <>
                    <TableHead className="text-right">ATP Rank</TableHead>
                    <TableHead className="text-right">Elo</TableHead>
                    <TableHead className="text-right">
                      <TooltipRoot>
                        <TooltipTrigger className="inline-flex items-center gap-1 cursor-default">
                          Trend
                          <HelpCircle className="h-3 w-3 text-muted-foreground/60" />
                        </TooltipTrigger>
                        <TooltipContent>
                          Elo change over the player's last 20 matches — a recent form indicator, not a live ranking shift.
                        </TooltipContent>
                      </TooltipRoot>
                    </TableHead>
                    <TableHead className="text-right">W/L</TableHead>
                    <TableHead className="text-right">Win %</TableHead>
                    <TableHead className="text-right">Hard %</TableHead>
                    <TableHead className="text-right">Clay %</TableHead>
                    <TableHead className="text-right">Grass %</TableHead>
                  </>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {players.map((p) => (
                <TableRow key={p.player_id} className="hover:bg-muted/50">
                  <TableCell className="text-muted-foreground text-sm font-mono">
                    {p.rank}
                  </TableCell>
                  <TableCell>
                    <Link
                      href={`/players/${p.player_id}`}
                      className="font-medium hover:text-primary hover:underline"
                    >
                      {p.name}
                    </Link>
                  </TableCell>
                  {view === "atp" ? (
                    <>
                      <TableCell className="text-right font-mono">
                        {Math.round(p.elo).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <EloTrend change={p.elo_change} />
                      </TableCell>
                      <TableCell className="text-right text-sm text-muted-foreground">
                        {p.wins}–{p.matches_played - p.wins}
                      </TableCell>
                      <TableCell className="text-right">{formatPct(p.win_rate)}</TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatPct(p.win_rate_hard)}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatPct(p.win_rate_clay)}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatPct(p.win_rate_grass)}
                      </TableCell>
                    </>
                  ) : (
                    <>
                      <TableCell className="text-right text-muted-foreground text-sm">
                        {p.rank ? `#${p.rank}` : "–"}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {Math.round(p.elo).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <EloTrend change={p.elo_change} />
                      </TableCell>
                      <TableCell className="text-right text-sm text-muted-foreground">
                        {p.wins}–{p.matches_played - p.wins}
                      </TableCell>
                      <TableCell className="text-right">{formatPct(p.win_rate)}</TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatPct(p.win_rate_hard)}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatPct(p.win_rate_clay)}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatPct(p.win_rate_grass)}
                      </TableCell>
                    </>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
