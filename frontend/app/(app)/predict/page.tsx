"use client";

import { useState, useEffect, Suspense } from "react";
import { useMutation } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import PlayerSelector from "@/components/predict/PlayerSelector";
import MatchContext from "@/components/predict/MatchContext";
import PredictionResult from "@/components/predict/PredictionResult";
import { predictMatch, getPlayer } from "@/lib/api";
import { PlayerSummary, PredictResponse } from "@/lib/types";
import { Zap } from "lucide-react";

function PredictPageInner() {
  const searchParams = useSearchParams();
  const [player1, setPlayer1] = useState<PlayerSummary | null>(null);
  const [player2, setPlayer2] = useState<PlayerSummary | null>(null);

  // Pre-fill from query params (?p1=ID&p2=ID)
  useEffect(() => {
    const p1Id = searchParams.get("p1");
    const p2Id = searchParams.get("p2");
    if (p1Id) {
      getPlayer(Number(p1Id))
        .then((p) =>
          setPlayer1({
            id: p.id,
            name: p.name,
            elo_overall: p.elo_overall,
            current_rank: p.current_rank,
            matches_played: p.matches_played,
            win_rate_overall: p.win_rate_overall,
          })
        )
        .catch(() => {});
    }
    if (p2Id) {
      getPlayer(Number(p2Id))
        .then((p) =>
          setPlayer2({
            id: p.id,
            name: p.name,
            elo_overall: p.elo_overall,
            current_rank: p.current_rank,
            matches_played: p.matches_played,
            win_rate_overall: p.win_rate_overall,
          })
        )
        .catch(() => {});
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const [surface, setSurface] = useState("Hard");
  const [series, setSeries] = useState("ATP250");
  const [round, setRound] = useState("1st Round");
  const [bestOf, setBestOf] = useState(3);
  const [tournament, setTournament] = useState("");

  function handleSeriesChange(v: string, derivedBestOf: number) {
    setSeries(v);
    setBestOf(derivedBestOf);
  }

  function handleTournamentSelect(name: string, tSurface: string, tSeries: string, tBestOf: number) {
    setTournament(name);
    setSurface(tSurface);
    setSeries(tSeries);
    setBestOf(tBestOf);
  }

  function handleTournamentClear() {
    setTournament("");
  }

  const mutation = useMutation({
    mutationFn: () =>
      predictMatch({
        player1_id: player1!.id,
        player2_id: player2!.id,
        surface,
        series,
        round,
        best_of: bestOf,
        tournament: tournament || undefined,
      }),
  });

  const canPredict = player1 && player2;

  return (
    <div className="max-w-5xl mx-auto space-y-7">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Match Predictor</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Select two players and match conditions to get a win probability.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Players</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <PlayerSelector
            label="Player 1"
            value={player1}
            onChange={setPlayer1}
            excludeId={player2?.id}
          />
          <PlayerSelector
            label="Player 2"
            value={player2}
            onChange={setPlayer2}
            excludeId={player1?.id}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Match Conditions</CardTitle>
        </CardHeader>
        <CardContent>
          <MatchContext
            surface={surface}
            series={series}
            round={round}
            tournament={tournament}
            onSurfaceChange={setSurface}
            onSeriesChange={handleSeriesChange}
            onRoundChange={setRound}
            onTournamentSelect={handleTournamentSelect}
            onTournamentClear={handleTournamentClear}
          />
        </CardContent>
      </Card>

      <Button
        className="w-full h-12 text-base rounded-xl"
        disabled={!canPredict || mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        <Zap className="mr-2 h-4 w-4" />
        {mutation.isPending ? "Predicting..." : "Predict Match"}
      </Button>

      {mutation.isPending && (
        <Card>
          <CardContent className="pt-6 space-y-3">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
      )}

      {mutation.error && (
        <Card className="ring-1 ring-destructive/30">
          <CardContent className="pt-6">
            <p className="text-destructive text-sm">
              {(mutation.error as Error).message}
            </p>
          </CardContent>
        </Card>
      )}

      {mutation.data && !mutation.isPending && (
        <PredictionResult
          result={mutation.data}
          requestParams={{
            player1_id: player1!.id,
            player2_id: player2!.id,
            surface,
            series,
            round,
            best_of: bestOf,
            tournament: tournament || undefined,
          }}
        />
      )}
    </div>
  );
}

export default function PredictPage() {
  return (
    <Suspense fallback={null}>
      <PredictPageInner />
    </Suspense>
  );
}
