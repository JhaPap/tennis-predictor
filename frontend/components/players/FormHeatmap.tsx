"use client";

import { RecentMatch } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface FormHeatmapProps {
  matches: RecentMatch[];
}

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MAX_DOTS = 8;

export default function FormHeatmap({ matches }: FormHeatmapProps) {
  if (matches.length === 0) return null;

  // Group matches by YYYY-MM
  const byMonth: Record<string, { won: boolean }[]> = {};
  for (const m of matches) {
    const key = m.date.slice(0, 7); // "YYYY-MM"
    if (!byMonth[key]) byMonth[key] = [];
    byMonth[key].push({ won: m.won });
  }

  // Take last 12 months that appear in data (sorted ascending)
  const sortedKeys = Object.keys(byMonth).sort().slice(-12);

  if (sortedKeys.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Form by Month</CardTitle>
        <p className="text-xs text-muted-foreground">Recent match results grouped by month</p>
      </CardHeader>
      <CardContent>
        <div className="flex gap-3 overflow-x-auto pb-1">
          {sortedKeys.map((key) => {
            const monthMatches = byMonth[key];
            const visible = monthMatches.slice(0, MAX_DOTS);
            const [year, monthNum] = key.split("-");
            const label = MONTH_LABELS[parseInt(monthNum, 10) - 1];
            const wins = visible.filter((m) => m.won).length;
            const total = visible.length;

            return (
              <div key={key} className="flex flex-col items-center gap-1 min-w-[36px]">
                {/* Dots (top to bottom = oldest to newest) */}
                <div className="flex flex-col-reverse gap-1">
                  {visible.map((m, i) => (
                    <div
                      key={i}
                      title={m.won ? "Win" : "Loss"}
                      className={`h-3 w-3 rounded-full ${
                        m.won ? "bg-green-500" : "bg-red-400"
                      }`}
                    />
                  ))}
                </div>
                {/* Month label */}
                <span className="text-[10px] text-muted-foreground mt-1 whitespace-nowrap">
                  {label}
                </span>
                {/* Win/total */}
                <span className="text-[10px] text-muted-foreground">
                  {wins}/{total}
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
