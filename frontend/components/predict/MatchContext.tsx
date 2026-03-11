"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown, X } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn, SERIES_OPTIONS, ROUND_OPTIONS, SERIES_BADGE, SURFACE_COLORS } from "@/lib/utils";
import { getTournaments } from "@/lib/api";
import { TournamentSummary } from "@/lib/types";

interface MatchContextProps {
  surface: string;
  series: string;
  round: string;
  tournament: string;
  onSurfaceChange: (v: string) => void;
  onSeriesChange: (v: string, bestOf: number) => void;
  onRoundChange: (v: string) => void;
  onTournamentSelect: (tournament: string, surface: string, series: string, bestOf: number) => void;
  onTournamentClear: () => void;
}

export default function MatchContext({
  surface,
  series,
  round,
  tournament,
  onSurfaceChange,
  onSeriesChange,
  onRoundChange,
  onTournamentSelect,
  onTournamentClear,
}: MatchContextProps) {
  const isGrandSlam = series === "Grand Slam";
  const locked = !!tournament;
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const { data: allTournaments = [] } = useQuery({
    queryKey: ["tournaments-all"],
    queryFn: () => getTournaments(),
    staleTime: 5 * 60_000,
  });

  // Deduplicate tournaments by name → pick the most recent entry for surface/series
  const uniqueTournaments = useMemo(() => {
    const map = new Map<string, TournamentSummary>();
    for (const t of allTournaments) {
      const existing = map.get(t.name);
      if (!existing || t.year > existing.year) {
        map.set(t.name, t);
      }
    }
    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [allTournaments]);

  const filtered = useMemo(() => {
    if (!search) return uniqueTournaments.slice(0, 50);
    const q = search.toLowerCase();
    return uniqueTournaments.filter((t) => t.name.toLowerCase().includes(q)).slice(0, 50);
  }, [uniqueTournaments, search]);

  function handleTournamentSelect(t: TournamentSummary) {
    const bestOf = t.series === "Grand Slam" ? 5 : 3;
    onTournamentSelect(t.name, t.surface, t.series, bestOf);
    setOpen(false);
    setSearch("");
  }

  function handleSeriesChange(v: string) {
    const bestOf = v === "Grand Slam" ? 5 : 3;
    onSeriesChange(v, bestOf);
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="text-sm font-medium text-muted-foreground block mb-1.5">
          Tournament
        </label>
        <div className="flex gap-2">
          <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                role="combobox"
                aria-expanded={open}
                className="w-full justify-between h-10"
              >
                {tournament ? (
                  <span className="truncate">{tournament}</span>
                ) : (
                  <span className="text-muted-foreground">Select tournament...</span>
                )}
                <ChevronsUpDown className="h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-0">
              <Command>
                <CommandInput
                  placeholder="Search tournaments..."
                  value={search}
                  onValueChange={setSearch}
                />
                <CommandList>
                  <CommandEmpty>No tournaments found.</CommandEmpty>
                  <CommandGroup>
                    {filtered.map((t) => (
                      <CommandItem
                        key={t.name}
                        value={t.name}
                        onSelect={() => handleTournamentSelect(t)}
                      >
                        <Check
                          className={cn(
                            "mr-2 h-4 w-4",
                            tournament === t.name ? "opacity-100" : "opacity-0"
                          )}
                        />
                        <span className="flex-1 truncate">{t.name}</span>
                        <span className="flex items-center gap-1.5 ml-2">
                          <span
                            className={cn(
                              "px-1.5 py-0.5 rounded text-white text-[10px]",
                              SURFACE_COLORS[t.surface] || "bg-gray-400"
                            )}
                          >
                            {t.surface}
                          </span>
                          <span className="text-[10px] text-muted-foreground">
                            {t.series}
                          </span>
                        </span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
          {tournament && (
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0 h-10 w-10"
              onClick={onTournamentClear}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Auto-fills surface and tier. Leave blank for manual selection.
        </p>
      </div>
      <div>
        <label className="text-sm font-medium text-muted-foreground block mb-1.5">
          Surface
        </label>
        <Tabs value={surface} onValueChange={locked ? undefined : onSurfaceChange}>
          <TabsList className="w-full">
            <TabsTrigger value="Hard" className="flex-1" disabled={locked}>Hard</TabsTrigger>
            <TabsTrigger value="Clay" className="flex-1" disabled={locked}>Clay</TabsTrigger>
            <TabsTrigger value="Grass" className="flex-1" disabled={locked}>Grass</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-sm font-medium text-muted-foreground block mb-1.5">
            Tournament Tier
          </label>
          <Select value={series} onValueChange={handleSeriesChange} disabled={locked}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SERIES_OPTIONS.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="text-sm font-medium text-muted-foreground block mb-1.5">
            Round
          </label>
          <Select value={round} onValueChange={onRoundChange}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ROUND_OPTIONS.map((r) => (
                <SelectItem key={r} value={r}>
                  {r}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">Format:</span>
        <span className="font-medium">
          {isGrandSlam ? "Best of 5" : "Best of 3"}
        </span>
        {isGrandSlam && (
          <span className="text-xs text-muted-foreground">(Grand Slam)</span>
        )}
      </div>
    </div>
  );
}
