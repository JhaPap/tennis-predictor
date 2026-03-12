"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3 } from "lucide-react";

type Status = "loading" | "success" | "error";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<Status>("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token found in the URL.");
      return;
    }
    verifyEmail(token)
      .then((data) => {
        setStatus("success");
        setMessage(data.message);
      })
      .catch((err: unknown) => {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Verification failed.");
      });
  }, [token]);

  return (
    <Card className="w-full max-w-sm text-center">
      <CardHeader className="space-y-2">
        <div className="flex justify-center">
          <BarChart3 className="h-8 w-8 text-primary" />
        </div>
        <CardTitle>
          {status === "loading" && "Verifying…"}
          {status === "success" && "Email verified!"}
          {status === "error" && "Verification failed"}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {status === "loading" && (
          <p className="text-sm text-muted-foreground">Checking your token…</p>
        )}
        {status === "success" && (
          <>
            <p className="text-sm text-muted-foreground">{message}</p>
            <Link href="/auth/login" className="text-primary hover:underline text-sm">
              Go to login
            </Link>
          </>
        )}
        {status === "error" && (
          <>
            <p className="text-sm text-destructive">{message}</p>
            <Link href="/auth/login" className="text-primary hover:underline text-sm">
              Back to login
            </Link>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Suspense fallback={
        <Card className="w-full max-w-sm text-center">
          <CardHeader>
            <CardTitle>Verifying…</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Checking your token…</p>
          </CardContent>
        </Card>
      }>
        <VerifyEmailContent />
      </Suspense>
    </div>
  );
}
