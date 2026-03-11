"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown, User } from "lucide-react";
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
import { cn } from "@/lib/utils";
import { searchPlayers } from "@/lib/api";
import { PlayerSummary } from "@/lib/types";

interface PlayerSelectorProps {
  label: string;
  value: PlayerSummary | null;
  onChange: (player: PlayerSummary | null) => void;
  excludeId?: number;
}

export default function PlayerSelector({
  label,
  value,
  onChange,
  excludeId,
}: PlayerSelectorProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const { data: players = [] } = useQuery({
    queryKey: ["players-search", search],
    queryFn: () => searchPlayers(search, 30),
    staleTime: 30_000,
  });

  const filtered = players.filter((p) => p.id !== excludeId);

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-muted-foreground">{label}</label>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between h-11"
          >
            {value ? (
              <span className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                {value.name}
                {value.current_rank && (
                  <span className="text-xs text-muted-foreground">
                    #{value.current_rank}
                  </span>
                )}
              </span>
            ) : (
              <span className="text-muted-foreground">Select player...</span>
            )}
            <ChevronsUpDown className="h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80 p-0">
          <Command>
            <CommandInput
              placeholder="Search players..."
              value={search}
              onValueChange={setSearch}
            />
            <CommandList>
              <CommandEmpty>No players found.</CommandEmpty>
              <CommandGroup>
                {filtered.map((player) => (
                  <CommandItem
                    key={player.id}
                    value={player.name}
                    onSelect={() => {
                      onChange(player.id === value?.id ? null : player);
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value?.id === player.id ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <span className="flex-1">{player.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {player.current_rank ? `#${player.current_rank}` : ""}
                      {" · "}
                      {Math.round(player.elo_overall)} Elo
                    </span>
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
