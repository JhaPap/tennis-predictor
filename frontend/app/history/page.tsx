"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getPredictionHistory, getCalibration } from "@/lib/api";
import { formatDate, formatPct, SURFACE_COLORS, cn } from "@/lib/utils";
import { ChevronLeft, ChevronRight } from "lucide-react";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
  Legend,
} from "recharts";

export default function HistoryPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["prediction-history", page],
    queryFn: () => getPredictionHistory(page, 25),
    staleTime: 30_000,
  });

  const { data: calibration = [] } = useQuery({
    queryKey: ["calibration"],
    queryFn: getCalibration,
    staleTime: Infinity,
  });

  const items = data?.items || [];
  const totalPages = data?.pages || 1;

  return (
    <div className="max-w-5xl mx-auto space-y-7">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Prediction History</h1>
        <p className="text-muted-foreground text-sm mt-1">
          All match predictions you have made.
        </p>
      </div>

      {data && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Total Predictions", value: data.total },
            {
              label: "Resolved",
              value: items.filter((i) => i.was_correct !== null).length,
            },
            {
              label: "Correct",
              value: items.filter((i) => i.was_correct === true).length,
            },
          ].map(({ label, value }) => (
            <div key={label} className="bg-card rounded-xl shadow-sm p-4 text-center">
              <div className="text-2xl font-bold">{value}</div>
              <div className="text-xs text-muted-foreground mt-1">{label}</div>
            </div>
          ))}
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 10 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : (
        <>
          <div className="rounded-xl shadow-sm">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Matchup</TableHead>
                  <TableHead>Surface</TableHead>
                  <TableHead className="text-right">P1 Prob</TableHead>
                  <TableHead className="text-center">Outcome</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                      {formatDate(log.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium text-sm">
                        {log.player1_name.split(" ")[0]} vs {log.player2_name.split(" ")[0]}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {log.series} · {log.round}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded text-white text-xs",
                          SURFACE_COLORS[log.surface] || "bg-gray-400"
                        )}
                      >
                        {log.surface}
                      </span>
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatPct(log.p1_win_prob * 100)}
                    </TableCell>
                    <TableCell className="text-center">
                      {log.was_correct === null ? (
                        <Badge variant="outline" className="text-xs">
                          Pending
                        </Badge>
                      ) : log.was_correct ? (
                        <Badge className="bg-green-100 text-green-800 text-xs">
                          Correct
                        </Badge>
                      ) : (
                        <Badge className="bg-red-100 text-red-800 text-xs">
                          Wrong
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {items.length === 0 && (
                  <TableRow>
                    <TableCell
                      colSpan={5}
                      className="text-center text-muted-foreground py-8"
                    >
                      No predictions yet. Go to the Predict page to get started.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page === totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}

      {/* Model Calibration Chart */}
      {calibration.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Model Calibration (2024 Test Set)</CardTitle>
            <p className="text-xs text-muted-foreground">
              Green line shows actual win rate per predicted confidence bucket. A well-calibrated
              model follows the diagonal — if it says 70%, it wins ~70% of the time.
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <ComposedChart data={calibration} margin={{ top: 8, right: 20, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-20" />
                <XAxis dataKey="bucket_label" tick={{ fontSize: 11 }} />
                <YAxis
                  yAxisId="left"
                  tickFormatter={(v) => `${Math.round(v * 100)}%`}
                  domain={[0.4, 1]}
                  tick={{ fontSize: 11 }}
                  width={42}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tick={{ fontSize: 11 }}
                  width={38}
                />
                <Tooltip
                  formatter={(value: unknown, name: string) => {
                    if (name === "actual_rate") return [`${Math.round((value as number) * 100)}%`, "Actual Rate"];
                    if (name === "predicted_avg") return [`${Math.round((value as number) * 100)}%`, "Predicted Avg"];
                    return [value as number, "Count"];
                  }}
                />
                <Legend />
                <Bar yAxisId="right" dataKey="count" fill="#94a3b8" opacity={0.4} name="count" />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="actual_rate"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="actual_rate"
                />
                <ReferenceLine
                  yAxisId="left"
                  segment={[
                    { x: calibration[0]?.bucket_label, y: calibration[0]?.predicted_avg },
                    { x: calibration[calibration.length - 1]?.bucket_label, y: calibration[calibration.length - 1]?.predicted_avg },
                  ]}
                  stroke="#94a3b8"
                  strokeDasharray="5 5"
                  label={{ value: "Perfect", fontSize: 10, fill: "#94a3b8" }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
