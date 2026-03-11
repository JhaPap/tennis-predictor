import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPct(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatElo(elo: number): string {
  return Math.round(elo).toLocaleString();
}

export const SURFACE_COLORS: Record<string, string> = {
  Hard: "bg-blue-500",
  Clay: "bg-orange-500",
  Grass: "bg-green-500",
  Carpet: "bg-purple-500",
};

export const SURFACE_TEXT_COLORS: Record<string, string> = {
  Hard: "text-blue-400",
  Clay: "text-orange-400",
  Grass: "text-emerald-400",
};

export const SERIES_BADGE: Record<string, string> = {
  "Grand Slam": "bg-yellow-500/20 text-yellow-300 border border-yellow-500/30",
  "Masters 1000": "bg-purple-500/20 text-purple-300 border border-purple-500/30",
  "Masters Cup": "bg-purple-500/20 text-purple-300 border border-purple-500/30",
  "ATP500": "bg-blue-500/20 text-blue-300 border border-blue-500/30",
  "ATP250": "bg-slate-500/20 text-slate-300 border border-slate-500/30",
};

export const SURFACES = ["Hard", "Clay", "Grass"] as const;
export const SERIES_OPTIONS = [
  "ATP250",
  "ATP500",
  "Masters 1000",
  "Grand Slam",
  "Masters Cup",
] as const;
export const ROUND_OPTIONS = [
  "1st Round",
  "2nd Round",
  "3rd Round",
  "4th Round",
  "Quarterfinals",
  "Semifinals",
  "The Final",
] as const;
