"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity } from "lucide-react";
import type { ServeStats } from "@/lib/types";

// League-average benchmarks (from charting dataset)
const MEANS = {
  ace_rate: 0.067,
  df_rate: 0.040,
  first_serve_pct: 0.611,
  first_serve_win_pct: 0.683,
  second_serve_win_pct: 0.480,
  return_win_pct: 0.337,
};

interface StatCellProps {
  label: string;
  value: number;
  meanKey: keyof typeof MEANS;
  higherIsBetter: boolean;
  format?: (v: number) => string;
}

function pct(v: number) {
  return `${(v * 100).toFixed(1)}%`;
}

function StatCell({ label, value, meanKey, higherIsBetter, format = pct }: StatCellProps) {
  const mean = MEANS[meanKey];
  const delta = value - mean;
  const isGood = higherIsBetter ? delta > 0.003 : delta < -0.003;
  const isBad = higherIsBetter ? delta < -0.003 : delta > 0.003;

  return (
    <div className="flex flex-col gap-1">
      <div className="text-xl font-bold tracking-tight">{format(value)}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="flex items-center gap-1">
        <div className="h-1 flex-1 rounded-full bg-muted overflow-hidden">
          {/* Simple bar: clamp value into a 0-100 range for visual */}
          <div
            className={`h-full rounded-full transition-all ${
              isGood
                ? "bg-emerald-500"
                : isBad
                ? "bg-red-500"
                : "bg-muted-foreground/40"
            }`}
            style={{ width: `${Math.min(100, Math.max(5, (value / (mean * 2)) * 100))}%` }}
          />
        </div>
        <span
          className={`text-[10px] font-medium ${
            isGood ? "text-emerald-500" : isBad ? "text-red-400" : "text-muted-foreground"
          }`}
        >
          {isGood ? "▲" : isBad ? "▼" : "—"}
        </span>
      </div>
    </div>
  );
}

export default function ServeReturnCard({ stats }: { stats: ServeStats }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Activity className="h-4 w-4 text-primary" />
            Serve &amp; Return Profile
          </CardTitle>
          {stats.has_data ? (
            <Badge variant="secondary" className="text-xs font-normal">
              {stats.charted_matches} matches charted
            </Badge>
          ) : (
            <Badge variant="outline" className="text-xs font-normal text-muted-foreground">
              League average
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-x-6 gap-y-4">
          <StatCell
            label="Ace Rate"
            value={stats.ace_rate}
            meanKey="ace_rate"
            higherIsBetter={true}
          />
          <StatCell
            label="Double Fault Rate"
            value={stats.df_rate}
            meanKey="df_rate"
            higherIsBetter={false}
          />
          <StatCell
            label="1st Serve In"
            value={stats.first_serve_pct}
            meanKey="first_serve_pct"
            higherIsBetter={true}
          />
          <StatCell
            label="1st Serve Win %"
            value={stats.first_serve_win_pct}
            meanKey="first_serve_win_pct"
            higherIsBetter={true}
          />
          <StatCell
            label="2nd Serve Win %"
            value={stats.second_serve_win_pct}
            meanKey="second_serve_win_pct"
            higherIsBetter={true}
          />
          <StatCell
            label="Return Win %"
            value={stats.return_win_pct}
            meanKey="return_win_pct"
            higherIsBetter={true}
          />
        </div>
      </CardContent>
    </Card>
  );
}
