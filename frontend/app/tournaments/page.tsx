"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getTournaments } from "@/lib/api";
import { SERIES_BADGE, SERIES_OPTIONS, SURFACE_COLORS, cn } from "@/lib/utils";
import { Search } from "lucide-react";

export default function TournamentsPage() {
  const [search, setSearch] = useState("");
  const [year, setYear] = useState<number | undefined>(2024);
  const [series, setSeries] = useState<string | undefined>(undefined);

  const { data: tournaments = [], isLoading } = useQuery({
    queryKey: ["tournaments", year, series],
    queryFn: () => getTournaments(year, series),
    staleTime: 60_000,
  });

  const filtered = tournaments.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-4xl mx-auto space-y-7">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Tournaments</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Browse tournament brackets and results.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search tournaments..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="border rounded-md px-3 py-2 text-sm bg-background"
          value={series || ""}
          onChange={(e) => setSeries(e.target.value || undefined)}
        >
          <option value="">All levels</option>
          {SERIES_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          className="border rounded-md px-3 py-2 text-sm bg-background"
          value={year || ""}
          onChange={(e) =>
            setYear(e.target.value ? Number(e.target.value) : undefined)
          }
        >
          <option value="">All years</option>
          {Array.from({ length: 26 }, (_, i) => 2025 - i).map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((t) => (
            <Link
              key={`${t.name}-${t.year}-${t.surface}-${t.series}`}
              href={`/tournaments/${encodeURIComponent(t.name)}?year=${t.year}`}
            >
              <Card className="transition-colors cursor-pointer">
                <CardContent className="py-3 px-4 flex items-center justify-between">
                  <div>
                    <div className="font-medium">{t.name}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {t.year} · {t.match_count} matches
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      className={cn(
                        "text-xs",
                        SERIES_BADGE[t.series] || "bg-gray-100 text-gray-800"
                      )}
                    >
                      {t.series}
                    </Badge>
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-white text-xs",
                        SURFACE_COLORS[t.surface] || "bg-gray-400"
                      )}
                    >
                      {t.surface}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
          {filtered.length === 0 && (
            <p className="text-muted-foreground text-sm text-center py-8">
              No tournaments found.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
