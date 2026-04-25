"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  ChevronRight,
  Clock3,
  FileText,
  Home,
  Mail,
  PieChart,
  Plus,
  ReceiptText,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
  WalletCards,
} from "lucide-react";
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

  const detectedTotal = useMemo(() => {
    if (!analysis) return "€0.00";

    const possibleAmount =
      "amount" in analysis && typeof analysis.amount === "string"
        ? analysis.amount
        : "total_amount" in analysis && typeof analysis.total_amount === "string"
          ? analysis.total_amount
          : "Ready";

    return possibleAmount;
  }, [analysis]);

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
      const message = confirmError instanceof Error ? confirmError.message : "Unknown error";
      setError(message);
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-[#050505] text-white">
      <div className="pointer-events-none fixed inset-0 opacity-75">
        <div className="absolute -left-28 top-0 h-72 w-72 rounded-full bg-orange-500/25 blur-3xl" />
        <div className="absolute right-[-7rem] top-24 h-80 w-80 rounded-full bg-fuchsia-600/25 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-96 w-96 rounded-full bg-blue-600/20 blur-3xl" />
      </div>

      <section className="relative mx-auto flex min-h-screen w-full max-w-md flex-col px-5 pb-32 pt-6">
        <header className="mb-5 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/40">
              FinPilot Lens
            </p>
            <h1 className="mt-1 text-4xl font-black tracking-tight">Inbox</h1>
          </div>

          <div className="flex items-center gap-2">
            <button className="relative grid h-11 w-11 place-items-center rounded-full bg-white/10 ring-1 ring-white/10 backdrop-blur">
              <Bell className="h-5 w-5" />
              <span className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full bg-orange-500" />
            </button>
            <button className="grid h-11 w-11 place-items-center rounded-full bg-gradient-to-br from-orange-500 via-red-500 to-fuchsia-600 shadow-lg shadow-orange-500/25">
              <Plus className="h-5 w-5" />
            </button>
          </div>
        </header>

        <motion.section
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="relative mb-4 overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.07] p-5 shadow-2xl shadow-black/40 backdrop-blur-xl"
        >
          <div className="absolute right-[-3rem] top-[-3rem] h-36 w-36 rounded-full bg-gradient-to-br from-orange-500 to-fuchsia-600 opacity-30 blur-2xl" />
          <div className="relative flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/45">
                Smart money requests
              </p>
              <div className="mt-2 flex items-end gap-2">
                <h2 className="text-4xl font-black tracking-tight">{detectedTotal}</h2>
                <span className="mb-1 rounded-full bg-emerald-500/15 px-2 py-1 text-xs font-bold text-emerald-300">
                  {analysis ? "analyzed" : "upload"}
                </span>
              </div>
              <p className="mt-2 max-w-[15rem] text-sm leading-5 text-white/55">
                Drop a bill, fine, screenshot, or email. We extract the payment details and prepare a safe bunq next step.
              </p>
            </div>
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-orange-500 via-red-500 to-fuchsia-600 shadow-xl shadow-orange-500/30">
              <ReceiptText className="h-7 w-7" />
            </div>
          </div>
        </motion.section>

        <div className="mb-4 grid grid-cols-3 gap-2">
          <QuickAction icon={Upload} label="Upload" tone="from-orange-500 to-red-500" />
          <QuickAction icon={Search} label="Extract" tone="from-blue-500 to-cyan-400" />
          <QuickAction icon={WalletCards} label="Prepare" tone="from-fuchsia-500 to-purple-500" />
        </div>

        <section className="mb-5 rounded-[1.75rem] border border-white/10 bg-[#151515]/90 p-4 shadow-2xl shadow-black/30 backdrop-blur-xl">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-black">Scan a document</h2>
              <p className="text-sm text-white/45">PDF, image, screenshot, or pasted text</p>
            </div>
            <span className="rounded-full bg-blue-500/15 px-3 py-1 text-xs font-black text-blue-300 ring-1 ring-blue-500/25">
              AI Lens
            </span>
          </div>

          <div className="rounded-[1.5rem] bg-white text-slate-950 shadow-xl shadow-black/20">
            <UploadCard
              file={file}
              text={text}
              isLoading={analysisLoading}
              onFileChange={setFile}
              onTextChange={setText}
              onSubmit={handleAnalyze}
            />
          </div>
        </section>

        {analysisLoading ? (
          <motion.section
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-5 rounded-[1.75rem] border border-white/10 bg-white/[0.07] p-5 shadow-2xl shadow-black/30 backdrop-blur-xl"
          >
            <div className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <p className="font-black">Analyzing your document...</p>
                <p className="text-sm text-white/45">Finding IBAN, amount, due date, reference and risk.</p>
              </div>
            </div>
            <div className="mt-4 space-y-3">
              <div className="h-4 animate-pulse rounded-full bg-white/10" />
              <div className="h-24 animate-pulse rounded-3xl bg-white/10" />
              <div className="h-4 animate-pulse rounded-full bg-white/10" />
            </div>
          </motion.section>
        ) : null}

        {analysis ? (
          <motion.section
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-5 overflow-hidden rounded-[1.75rem] border border-white/10 bg-[#151515] shadow-2xl shadow-black/30"
          >
            <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
              <div className="flex items-center gap-3">
                <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-emerald-400 to-blue-500">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="font-black">Analysis result</h2>
                  <p className="text-sm text-white/45">Review before preparing a bunq action</p>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-white/25" />
            </div>

            <div className="bg-white text-slate-950">
              <AnalysisResult analysis={analysis} />
            </div>
          </motion.section>
        ) : null}

        {error ? (
          <motion.section
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-5 flex gap-3 rounded-[1.5rem] border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100"
          >
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-300" />
            <div>
              <p className="font-black">Something went wrong</p>
              <p className="mt-1 text-red-100/80">{error}</p>
            </div>
          </motion.section>
        ) : null}

        {successMessage ? (
          <motion.section
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-5 rounded-[1.5rem] border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-100"
          >
            <div className="flex gap-3">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-300" />
              <div>
                <p className="font-black">{successMessage}</p>
                {confirmResult ? (
                  <p className="mt-2 leading-6 text-emerald-100/80">
                    Prepared {confirmResult.prepared_action.type.replaceAll("_", " ")} using {confirmResult.account_used}. No real payment was sent.
                  </p>
                ) : null}
              </div>
            </div>
          </motion.section>
        ) : null}

        <section className="rounded-[1.75rem] border border-white/10 bg-white/[0.06] p-4 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-yellow-400 to-orange-500">
              <Clock3 className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <h4 className="font-black">Safe by default</h4>
              <p className="text-sm text-white/50">FinPilot prepares the action only. You stay in control before anything reaches bunq.</p>
            </div>
          </div>
        </section>
      </section>

      <nav className="fixed bottom-4 left-1/2 z-20 flex w-[min(24rem,calc(100%-2rem))] -translate-x-1/2 items-center justify-around rounded-[1.75rem] border border-white/10 bg-black/80 px-4 py-3 shadow-2xl shadow-black/60 backdrop-blur-xl">
        <NavItem icon={Home} label="Home" />
        <NavItem icon={Mail} label="Inbox" active />
        <NavItem icon={PieChart} label="Budget" />
        <NavItem icon={FileText} label="Docs" />
      </nav>

      {analysis ? (
        <div className="fixed bottom-[5.9rem] left-1/2 z-30 w-[min(24rem,calc(100%-2rem))] -translate-x-1/2">
          <ActionButton
            label="Approve and prepare bunq action"
            loading={actionLoading}
            onClick={handleConfirmAction}
          />
        </div>
      ) : null}
    </main>
  );
}

function QuickAction({
  icon: Icon,
  label,
  tone,
}: {
  icon: React.ElementType;
  label: string;
  tone: string;
}) {
  return (
    <button
      type="button"
      className={`flex h-14 items-center justify-center gap-2 rounded-2xl bg-gradient-to-r ${tone} text-sm font-black shadow-lg shadow-black/25 transition hover:scale-[1.02] active:scale-[0.98]`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}

function NavItem({
  icon: Icon,
  label,
  active = false,
}: {
  icon: React.ElementType;
  label: string;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      className={`flex flex-col items-center gap-1 text-[11px] font-bold transition ${
        active ? "text-white" : "text-white/35 hover:text-white/70"
      }`}
    >
      <span
        className={`grid h-9 w-9 place-items-center rounded-2xl ${
          active
            ? "bg-gradient-to-br from-orange-500 via-red-500 to-fuchsia-600 shadow-lg shadow-orange-500/20"
            : "bg-transparent"
        }`}
      >
        <Icon className="h-5 w-5" />
      </span>
      {label}
    </button>
  );
}
