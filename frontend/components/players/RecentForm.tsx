"use client";

import { RecentMatch } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn, SURFACE_COLORS, formatDate } from "@/lib/utils";

interface RecentFormProps {
  matches: RecentMatch[];
}

export default function RecentForm({ matches }: RecentFormProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Recent Form</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {/* W/L pill strip */}
        <div className="flex gap-1 mb-3">
          {matches.slice(0, 10).map((m) => (
            <div
              key={m.id}
              title={`vs ${m.opponent_name} · ${m.score || ""}`}
              className={cn(
                "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white",
                m.won ? "bg-green-500" : "bg-red-400"
              )}
            >
              {m.won ? "W" : "L"}
            </div>
          ))}
        </div>

        {/* Match list */}
        <div className="space-y-1">
          {matches.slice(0, 10).map((m) => (
            <div
              key={m.id}
              className="flex items-center justify-between text-sm py-1 border-b last:border-0"
            >
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "text-xs font-bold",
                    m.won ? "text-green-600" : "text-red-500"
                  )}
                >
                  {m.won ? "W" : "L"}
                </span>
                <span className="text-muted-foreground truncate max-w-[140px]">
                  vs {m.opponent_name}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span
                  className={cn(
                    "px-1.5 py-0.5 rounded text-white text-xs",
                    SURFACE_COLORS[m.surface] || "bg-gray-400"
                  )}
                >
                  {m.surface[0]}
                </span>
                <span>{m.score || ""}</span>
                <span>{formatDate(m.date)}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
