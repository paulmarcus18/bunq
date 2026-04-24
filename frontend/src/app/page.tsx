"use client";

import { useState } from "react";
import { ActionButton } from "@/components/ActionButton";
import { AnalysisResult } from "@/components/AnalysisResult";
import { UploadCard } from "@/components/UploadCard";
import { AnalysisResponse, ConfirmActionResponse } from "@/types/analysis";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [confirmResult, setConfirmResult] = useState<ConfirmActionResponse | null>(null);

  async function handleAnalyze() {
    setAnalysisLoading(true);
    setError(null);
    setSuccessMessage(null);
    setConfirmResult(null);

    try {
      const formData = new FormData();
      if (file) {
        formData.append("file", file);
      }
      if (text.trim()) {
        formData.append("text", text.trim());
      }

      const response = await fetch(`${API_BASE}/analyze-document`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Analysis failed");
      }

      const data = (await response.json()) as AnalysisResponse;
      setAnalysis(data);
    } catch (submissionError) {
      const message =
        submissionError instanceof Error ? submissionError.message : "Unknown error";
      setError(message);
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function handleConfirmAction() {
    if (!analysis) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await fetch(`${API_BASE}/confirm-action`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ analysis }),
      });

      if (!response.ok) {
        throw new Error("Could not prepare bunq action");
      }

      const data = (await response.json()) as ConfirmActionResponse;
      setConfirmResult(data);
      setSuccessMessage(data.message);
    } catch (confirmError) {
      const message =
        confirmError instanceof Error ? confirmError.message : "Unknown error";
      setError(message);
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-md px-4 pb-28 pt-6">
      <section className="mb-5 rounded-[32px] bg-slate-950 px-5 py-6 text-white shadow-panel">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200">
          FinPilot Inbox
        </p>
        <h1 className="mt-3 text-3xl font-semibold leading-tight">
          Your AI inbox copilot for confusing money requests
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-300">
          Upload a financial document, screenshot, or pasted email. We extract the
          key payment details, flag scams, and prepare a safe bunq next step.
        </p>
      </section>

      <div className="space-y-5">
        <UploadCard
          file={file}
          text={text}
          isLoading={analysisLoading}
          onFileChange={setFile}
          onTextChange={setText}
          onSubmit={handleAnalyze}
        />

        {analysisLoading ? (
          <section className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-panel">
            <p className="text-sm font-medium text-slate-600">Analyzing your document...</p>
            <div className="mt-4 space-y-3">
              <div className="h-4 animate-pulse rounded-full bg-slate-200" />
              <div className="h-24 animate-pulse rounded-3xl bg-slate-100" />
              <div className="h-4 animate-pulse rounded-full bg-slate-200" />
            </div>
          </section>
        ) : null}

        {analysis ? <AnalysisResult analysis={analysis} /> : null}

        {error ? (
          <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {error}
          </section>
        ) : null}

        {successMessage ? (
          <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
            <p className="font-semibold">{successMessage}</p>
            {confirmResult ? (
              <p className="mt-2 leading-6">
                Prepared {confirmResult.prepared_action.type.replaceAll("_", " ")} using{" "}
                {confirmResult.account_used}. No real payment was sent.
              </p>
            ) : null}
          </section>
        ) : null}
      </div>

      {analysis ? (
        <ActionButton
          label="Approve and prepare bunq action"
          loading={actionLoading}
          onClick={handleConfirmAction}
        />
      ) : null}
    </main>
  );
}
