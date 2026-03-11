"use client";

import { PlayerDetail } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";
import { formatPct } from "@/lib/utils";

interface SurfaceBreakdownProps {
  player: PlayerDetail;
}

export default function SurfaceBreakdown({ player }: SurfaceBreakdownProps) {
  const data = [
    {
      surface: "Hard",
      value: Math.round(player.win_rate_hard * 100),
      matches: player.matches_hard,
    },
    {
      surface: "Clay",
      value: Math.round(player.win_rate_clay * 100),
      matches: player.matches_clay,
    },
    {
      surface: "Grass",
      value: Math.round(player.win_rate_grass * 100),
      matches: player.matches_grass,
    },
    {
      surface: "Overall",
      value: Math.round(player.win_rate_overall * 100),
      matches: player.matches_played,
    },
  ];

  const radarData = [
    { axis: "Hard", value: player.win_rate_hard * 100 },
    { axis: "Clay", value: player.win_rate_clay * 100 },
    { axis: "Grass", value: player.win_rate_grass * 100 },
    { axis: "Overall", value: player.win_rate_overall * 100 },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Surface Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            {data.map(({ surface, value, matches }) => (
              <div key={surface}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-muted-foreground">{surface}</span>
                  <span className="font-medium">{value}%</span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${value}%` }}
                  />
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {matches} matches
                </div>
              </div>
            ))}
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="axis" tick={{ fontSize: 11 }} />
              <Radar
                dataKey="value"
                fill="#3b6fd4"
                fillOpacity={0.3}
                stroke="#3b6fd4"
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
