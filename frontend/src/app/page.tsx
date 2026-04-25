"use client";

import { ElementType, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowDownCircle,
  Bell,
  ChevronRight,
  CircleDollarSign,
  Clock3,
  FileText,
  Heart,
  Home,
  Mail,
  MoreHorizontal,
  PieChart,
  Plus,
  ReceiptText,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
  Wallet,
  WalletCards,
} from "lucide-react";
import { ActionButton } from "@/components/ActionButton";
import { ActionReviewCard } from "@/components/ActionReviewCard";
import { AnalysisResult } from "@/components/AnalysisResult";
import { BunqPreflightCard } from "@/components/BunqPreflightCard";
import { BunqReceiptCard } from "@/components/BunqReceiptCard";
import { UploadCard } from "@/components/UploadCard";
import {
  AnalysisResponse,
  BunqAccountsResponse,
  BunqAccountSummary,
  ConfirmActionResponse,
} from "@/types/analysis";

const API_BASE = "/api";

type Screen = "home" | "inbox" | "budget" | "docs";

function dismissKeyboard() {
  if (typeof document === "undefined") {
    return;
  }

  const active = document.activeElement;
  if (active instanceof HTMLElement) {
    active.blur();
  }
}

function hasPositiveAmount(amount: number | null) {
  if (typeof amount !== "number") {
    return false;
  }

  return Number.isFinite(amount) && amount > 0;
}

function formatAmount(amount: number | null) {
  if (amount === null || !hasPositiveAmount(amount)) {
    return "€0.00";
  }

  return new Intl.NumberFormat("nl-NL", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

function normalizeAnalysis(analysis: AnalysisResponse): AnalysisResponse {
  const dueDate = analysis.due_date?.trim() || null;
  const beneficiaryIban = analysis.beneficiary_iban?.trim() || null;
  const hasPaymentDetails =
    Boolean(beneficiaryIban) &&
    hasPositiveAmount(analysis.amount) &&
    analysis.manual_payment_required;

  let recommendedAction = analysis.recommended_action;
  let actionRequired = false;

  if (analysis.is_suspicious) {
    recommendedAction = "review_manually";
  } else if (analysis.auto_debit_detected) {
    recommendedAction = "ignore";
  } else if (recommendedAction === "schedule_payment") {
    actionRequired = hasPaymentDetails && Boolean(dueDate);
  } else if (recommendedAction === "pay_now") {
    actionRequired = hasPaymentDetails;
  }

  return {
    ...analysis,
    beneficiary_iban: beneficiaryIban,
    due_date: dueDate,
    recommended_action: recommendedAction,
    action_required: actionRequired,
  };
}

export default function HomePage() {
  const [activeScreen, setActiveScreen] = useState<Screen>("inbox");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [accountsLoading, setAccountsLoading] = useState(false);
  const [accountsLoaded, setAccountsLoaded] = useState(false);
  const [accountsError, setAccountsError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [confirmResult, setConfirmResult] = useState<ConfirmActionResponse | null>(null);
  const [bunqAccounts, setBunqAccounts] = useState<BunqAccountSummary[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);

  const detectedTotal = useMemo(() => {
    if (!analysis) {
      return "€0.00";
    }

    return formatAmount(analysis.amount);
  }, [analysis]);

  async function readErrorMessage(response: Response, fallback: string) {
    try {
      const payload = (await response.json()) as { detail?: string };
      return payload.detail ?? fallback;
    } catch {
      return fallback;
    }
  }

  async function handleAnalyze() {
    dismissKeyboard();
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
        throw new Error(await readErrorMessage(response, "Analysis failed"));
      }

      const data = (await response.json()) as AnalysisResponse;
      setAnalysis(normalizeAnalysis(data));
      setActiveScreen("inbox");
    } catch (submissionError) {
      const message =
        submissionError instanceof Error ? submissionError.message : "Unknown error";
      setError(message);
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function loadAccounts(force = false) {
    if (accountsLoading || (accountsLoaded && !force)) {
      return;
    }

    setAccountsLoading(true);
    setAccountsError(null);

    try {
      const response = await fetch(`${API_BASE}/bunq/accounts`, {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "Could not load bunq accounts"));
      }

      const data = (await response.json()) as BunqAccountsResponse;
      setBunqAccounts(data.accounts ?? []);
      setSelectedAccountId((current) => {
        if (current && (data.accounts ?? []).some((account) => account.id === current)) {
          return current;
        }
        return data.accounts?.[0]?.id ?? null;
      });
      setAccountsLoaded(true);
    } catch (accountsLoadError) {
      const message =
        accountsLoadError instanceof Error
          ? accountsLoadError.message
          : "Could not load bunq accounts";
      setAccountsError(message);
    } finally {
      setAccountsLoading(false);
    }
  }

  async function handleConfirmAction() {
    if (!analysis || !analysis.action_required || !selectedAccountId) {
      return;
    }

    dismissKeyboard();
    setActionLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await fetch(`${API_BASE}/confirm-action`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ analysis, source_account_id: selectedAccountId }),
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "Could not prepare bunq action"));
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

  function handleAnalysisChange(patch: Partial<AnalysisResponse>) {
    setAnalysis((current) => {
      if (!current) {
        return current;
      }

      return normalizeAnalysis({
        ...current,
        ...patch,
      });
    });
  }

  useEffect(() => {
    if (!analysis || analysis.is_suspicious || analysis.auto_debit_detected) {
      return;
    }
    void loadAccounts();
  }, [analysis]); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedAccount =
    bunqAccounts.find((account) => account.id === selectedAccountId) ?? null;
  const canConfirm = Boolean(analysis?.action_required && selectedAccountId);
  const buttonLabel = analysis?.action_required
    ? analysis.recommended_action === "schedule_payment"
      ? `Schedule from ${selectedAccount?.description ?? "selected account"}`
      : `Pay from ${selectedAccount?.description ?? "selected account"}`
    : "Confirm and create bunq action";

  return (
    <main className="min-h-screen overflow-hidden bg-[#050505] text-white">
      <div className="pointer-events-none fixed inset-0 opacity-75">
        <div className="absolute -left-28 top-0 h-72 w-72 rounded-full bg-orange-500/25 blur-3xl" />
        <div className="absolute right-[-7rem] top-24 h-80 w-80 rounded-full bg-fuchsia-600/25 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-96 w-96 rounded-full bg-blue-600/20 blur-3xl" />
      </div>

      <section className="relative mx-auto flex min-h-screen w-full max-w-md flex-col px-5 pb-32 pt-6">
        {activeScreen === "home" ? <BunqHomeScreen /> : null}
        {activeScreen === "inbox" ? (
          <InboxScreen
            file={file}
            text={text}
            analysis={analysis}
            analysisLoading={analysisLoading}
            error={error}
            successMessage={successMessage}
            confirmResult={confirmResult}
            detectedTotal={detectedTotal}
            accountsLoading={accountsLoading}
            accountsError={accountsError}
            bunqAccounts={bunqAccounts}
            selectedAccountId={selectedAccountId}
            selectedAccount={selectedAccount}
            onFileChange={setFile}
            onTextChange={setText}
            onAnalyze={handleAnalyze}
            onAnalysisChange={handleAnalysisChange}
            onRefreshAccounts={() => void loadAccounts(true)}
            onSelectAccount={setSelectedAccountId}
          />
        ) : null}
        {activeScreen === "budget" ? <BudgetScreen /> : null}
        {activeScreen === "docs" ? <DocsScreen /> : null}
      </section>

      <nav className="fixed bottom-4 left-1/2 z-20 flex w-[min(24rem,calc(100%-2rem))] -translate-x-1/2 items-center justify-around rounded-[1.75rem] border border-white/10 bg-black/80 px-4 py-3 shadow-2xl shadow-black/60 backdrop-blur-xl">
        <NavItem icon={Home} label="Home" active={activeScreen === "home"} onClick={() => setActiveScreen("home")} />
        <NavItem icon={Mail} label="Inbox" active={activeScreen === "inbox"} onClick={() => setActiveScreen("inbox")} />
        <NavItem icon={PieChart} label="Budget" active={activeScreen === "budget"} onClick={() => setActiveScreen("budget")} />
        <NavItem icon={FileText} label="Docs" active={activeScreen === "docs"} onClick={() => setActiveScreen("docs")} />
      </nav>

      {activeScreen === "inbox" && analysis ? (
        <div className="fixed bottom-[5.9rem] left-1/2 z-30 w-[min(24rem,calc(100%-2rem))] -translate-x-1/2">
          {!analysis.action_required ? (
            <div className="rounded-[1.4rem] border border-white/10 bg-black/85 px-4 py-3 text-center text-sm font-semibold text-white/65 shadow-2xl shadow-black/50 backdrop-blur-xl">
              {analysis.auto_debit_detected
                ? "Automatic debit detected. No manual bunq payment is needed."
                : analysis.risk_level === "blocked"
                  ? `TrustScore ${analysis.trust_score}/100 — bunq payment blocked until you review this manually.`
                : analysis.recommended_action === "schedule_payment" && !analysis.due_date
                  ? "Add a due date to enable scheduling."
                  : "Not enough payment details to create a bunq action yet."}
            </div>
          ) : (
            <ActionButton
              label={buttonLabel}
              disabled={!canConfirm || accountsLoading}
              loading={actionLoading}
              onClick={handleConfirmAction}
            />
          )}
        </div>
      ) : null}
    </main>
  );
}

function BunqHomeScreen() {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
      <header className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 overflow-hidden rounded-full bg-gradient-to-br from-orange-400 via-pink-500 to-blue-500 p-[2px]">
            <div className="grid h-full w-full place-items-center rounded-full bg-black text-sm font-black">L</div>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/35">10:10</p>
            <h1 className="text-4xl font-black tracking-tight">Home</h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button type="button" className="grid h-10 w-10 place-items-center rounded-full bg-white/10 ring-1 ring-white/10">
            <Search className="h-5 w-5 text-white/80" />
          </button>
          <button type="button" className="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-purple-600 to-fuchsia-500 ring-2 ring-orange-500/80">
            <MoreHorizontal className="h-5 w-5" />
          </button>
        </div>
      </header>

      <section className="mb-4 rounded-[1.75rem] border border-white/10 bg-[#1a1a1a] p-4 shadow-2xl shadow-black/35">
        <div className="flex items-center justify-between">
          <div className="flex-1 text-center">
            <p className="text-xs font-medium text-white/35">Net Wealth</p>
            <p className="mt-1 text-2xl font-black tracking-tight">€1,559.76</p>
            <div className="mt-1 flex items-center justify-center gap-1 text-xs font-bold text-white/35">
              <span>This Week</span>
              <span className="text-emerald-400">▲ €241.93</span>
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-white/25" />
        </div>
      </section>

      <div className="mb-5 grid grid-cols-3 gap-2">
        <OutlineAction icon={ArrowDownCircle} label="Pay" tone="orange" />
        <OutlineAction icon={CircleDollarSign} label="Request" tone="blue" />
        <OutlineAction icon={Plus} label="Add Money" tone="purple" />
      </div>

      <section className="mb-5">
        <div className="mb-2 flex items-center justify-between px-1">
          <h2 className="text-sm font-black">Bank Accounts</h2>
          <p className="text-sm font-black text-white/70">€850.52</p>
        </div>

        <div className="overflow-hidden rounded-[1.65rem] border border-white/10 bg-[#1a1a1a] shadow-2xl shadow-black/35">
          <BankAccountRow
            icon={CircleDollarSign}
            iconClass="bg-blue-600"
            name="Personal"
            iban="NL15 BUNQ 2100 0752 09"
            amount="€450.00"
          />
          <BankAccountRow
            icon={Heart}
            iconClass="bg-rose-600"
            name="Joint"
            iban="NL16 BUNQ 2100 0653 94"
            amount="€200.00"
          />
          <BankAccountRow
            icon={Wallet}
            iconClass="bg-purple-600"
            name="Everyday"
            iban=""
            amount=""
            badges
          />
          <button type="button" className="w-full border-t border-white/10 px-4 py-3 text-left text-sm font-bold text-blue-400">
            Add an Extra Bank Account
          </button>
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between px-1">
          <h2 className="text-sm font-black">Recent Transactions</h2>
          <Search className="h-4 w-4 text-white/70" />
        </div>

        <div className="space-y-3">
          <TransactionRow logo="Uber" title="Uber" subtitle="Card payment" amount="€ -22.12" />
          <TransactionRow logo="AH" title="Albert Heijn" subtitle="Groceries" amount="€ -41.80" />
          <TransactionRow logo="+" title="Payment received" subtitle="Tikkie request" amount="€ +65.00" positive />
        </div>
      </section>
    </motion.div>
  );
}

function InboxScreen({
  file,
  text,
  analysis,
  analysisLoading,
  error,
  successMessage,
  confirmResult,
  detectedTotal,
  accountsLoading,
  accountsError,
  bunqAccounts,
  selectedAccountId,
  selectedAccount,
  onFileChange,
  onTextChange,
  onAnalyze,
  onAnalysisChange,
  onRefreshAccounts,
  onSelectAccount,
}: {
  file: File | null;
  text: string;
  analysis: AnalysisResponse | null;
  analysisLoading: boolean;
  error: string | null;
  successMessage: string | null;
  confirmResult: ConfirmActionResponse | null;
  detectedTotal: string;
  accountsLoading: boolean;
  accountsError: string | null;
  bunqAccounts: BunqAccountSummary[];
  selectedAccountId: string | null;
  selectedAccount: BunqAccountSummary | null;
  onFileChange: (file: File | null) => void;
  onTextChange: (text: string) => void;
  onAnalyze: () => void;
  onAnalysisChange: (patch: Partial<AnalysisResponse>) => void;
  onRefreshAccounts: () => void;
  onSelectAccount: (accountId: string) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <header className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/40">deBunq · scam shield</p>
          <p className="mt-1 max-w-[16rem] text-xs font-medium leading-4 text-white/45">
            Score every bill, screenshot, email, or voice note before bunq pays anyone.
          </p>
          <h1 className="mt-2 text-4xl font-black tracking-tight">Inbox</h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="relative grid h-11 w-11 place-items-center rounded-full bg-white/10 ring-1 ring-white/10 backdrop-blur"
          >
            <Bell className="h-5 w-5" />
            <span className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full bg-orange-500" />
          </button>

          <button
            type="button"
            className="grid h-11 w-11 place-items-center rounded-full bg-gradient-to-br from-orange-500 via-red-500 to-fuchsia-600 shadow-lg shadow-orange-500/25"
          >
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
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/45">deBunq TrustScore</p>

            <div className="mt-2 flex items-end gap-2">
              <h2 className="text-4xl font-black tracking-tight">
                {analysis ? `${analysis.trust_score}/100` : detectedTotal}
              </h2>
              <span
                className={`mb-1 rounded-full px-2 py-1 text-xs font-bold ${
                  analysis
                    ? analysis.risk_level === "safe"
                      ? "bg-emerald-500/15 text-emerald-300"
                      : analysis.risk_level === "blocked"
                        ? "bg-rose-500/15 text-rose-300"
                        : "bg-amber-500/15 text-amber-300"
                    : "bg-emerald-500/15 text-emerald-300"
                }`}
              >
                {analysis
                  ? analysis.risk_level === "safe"
                    ? "safe"
                    : analysis.risk_level === "blocked"
                      ? "blocked"
                      : "review"
                  : "ready"}
              </span>
            </div>

            <p className="mt-2 max-w-[16rem] text-sm leading-5 text-white/55">
              Forward a bill, screenshot, email, or WhatsApp voice note. deBunq scores it before bunq pays anyone.
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
            <h2 className="text-lg font-black">Check a payment request</h2>
            <p className="text-sm text-white/45">PDF, photo, screenshot, voice note, or pasted text</p>
          </div>

          <span className="rounded-full bg-blue-500/15 px-3 py-1 text-xs font-black text-blue-300 ring-1 ring-blue-500/25">
            Multimodal AI
          </span>
        </div>

        <div className="rounded-[1.5rem] bg-white text-slate-950 shadow-xl shadow-black/20">
          <UploadCard
            file={file}
            text={text}
            isLoading={analysisLoading}
            onFileChange={onFileChange}
            onTextChange={onTextChange}
            onSubmit={onAnalyze}
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
              <p className="font-black">Scoring this request with deBunq...</p>
              <p className="text-sm text-white/45">Transcribing, parsing, and weighing scam signals across modalities.</p>
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
                <h2 className="font-black">deBunq result</h2>
                <p className="text-sm text-white/45">Trust score, red flags, and bunq next step</p>
              </div>
            </div>

            <ChevronRight className="h-5 w-5 text-white/25" />
          </div>

          <div className="bg-white text-slate-950">
            <AnalysisResult analysis={analysis} />
          </div>
        </motion.section>
      ) : null}

      {analysis && !analysis.is_suspicious && !analysis.auto_debit_detected ? (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-5 overflow-hidden rounded-[1.75rem] border border-white/10 bg-[#151515] shadow-2xl shadow-black/30"
        >
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400">
                <WalletCards className="h-5 w-5" />
              </div>
              <div>
                <h2 className="font-black">Choose bunq account</h2>
                <p className="text-sm text-white/45">Pick the account to use before confirming</p>
              </div>
            </div>

            <button
              type="button"
              onClick={onRefreshAccounts}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-black uppercase tracking-[0.12em] text-white/70"
            >
              Refresh
            </button>
          </div>

          <div className="space-y-3 bg-white p-4 text-slate-950">
            {accountsLoading ? (
              <p className="text-sm text-slate-600">Loading your bunq accounts...</p>
            ) : null}

            {!accountsLoading && bunqAccounts.length ? (
              <div className="space-y-3">
                {bunqAccounts.map((account) => {
                  const isSelected = account.id === selectedAccountId;
                  return (
                    <button
                      key={account.id}
                      type="button"
                      onClick={() => onSelectAccount(account.id)}
                      className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                        isSelected
                          ? "border-slate-950 bg-slate-950 text-white"
                          : "border-slate-200 bg-slate-50 text-slate-900"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-sm font-semibold">{account.description}</p>
                          <p
                            className={`mt-1 truncate text-xs ${
                              isSelected ? "text-slate-300" : "text-slate-500"
                            }`}
                          >
                            {account.iban ?? "IBAN unavailable"}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold">
                            {account.balance} {account.currency}
                          </p>
                          <p
                            className={`mt-1 text-xs ${
                              isSelected ? "text-cyan-200" : "text-slate-500"
                            }`}
                          >
                            {isSelected ? "Selected" : "Tap to use"}
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : null}

            {!accountsLoading && !bunqAccounts.length ? (
              <p className="text-sm text-slate-600">No bunq accounts are available yet.</p>
            ) : null}

            {selectedAccount ? (
              <p className="text-sm text-slate-600">
                FinPilot will create the bunq action from{" "}
                <span className="font-semibold text-slate-900">{selectedAccount.description}</span>
                {selectedAccount.iban ? ` (${selectedAccount.iban})` : ""}.
              </p>
            ) : null}

            {accountsError ? (
              <p className="text-sm font-medium text-rose-700">{accountsError}</p>
            ) : null}

            {analysis.action_required && !selectedAccountId && !accountsLoading && !accountsError ? (
              <p className="text-sm font-medium text-amber-700">
                Select a bunq account before confirming the action.
              </p>
            ) : null}
          </div>
        </motion.section>
      ) : null}

      {analysis ? (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-5">
          <ActionReviewCard analysis={analysis} onChange={onAnalysisChange} />
        </motion.div>
      ) : null}

      {analysis && analysis.action_required && !confirmResult ? (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-5">
          <BunqPreflightCard analysis={analysis} selectedAccount={selectedAccount} />
        </motion.div>
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

      {confirmResult ? (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-5"
        >
          <BunqReceiptCard result={confirmResult} />
        </motion.section>
      ) : successMessage ? (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-5 rounded-[1.5rem] border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-100"
        >
          <p className="font-black">{successMessage}</p>
        </motion.section>
      ) : null}

      <section className="rounded-[1.75rem] border border-white/10 bg-white/[0.06] p-4 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-yellow-400 to-orange-500">
            <Clock3 className="h-5 w-5" />
          </div>

          <div className="flex-1">
            <h4 className="font-black">Safe by default</h4>
            <p className="text-sm text-white/50">
              deBunq prepares the action only. You stay in control before anything reaches bunq.
            </p>
          </div>
        </div>
      </section>
    </motion.div>
  );
}

function BudgetScreen() {
  return (
    <PlaceholderScreen
      eyebrow="Budget"
      title="Budget"
      amount="€1,284.20"
      badge="72% safe"
      description="A simple spending overview using standard demo values. Real budgeting can be connected later."
      cards={[
        ["Bills", "€412.40", "Due this month"],
        ["Groceries", "€268.10", "€81.90 left"],
        ["Transport", "€96.35", "On track"],
      ]}
    />
  );
}

function DocsScreen() {
  return (
    <PlaceholderScreen
      eyebrow="Documents"
      title="Docs"
      amount="18"
      badge="stored"
      description="A clean document vault for bills, fines, tax letters, and proof of payment."
      cards={[
        ["Parking fine", "PDF", "Uploaded today"],
        ["Energy bill", "PDF", "Analyzed"],
        ["Tax letter", "Image", "Needs review"],
      ]}
    />
  );
}

function PlaceholderScreen({
  eyebrow,
  title,
  amount,
  badge,
  description,
  cards,
}: {
  eyebrow: string;
  title: string;
  amount: string;
  badge: string;
  description: string;
  cards: string[][];
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
      <header className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/40">{eyebrow}</p>
          <h1 className="mt-1 text-4xl font-black tracking-tight">{title}</h1>
        </div>
        <button type="button" className="grid h-11 w-11 place-items-center rounded-full bg-gradient-to-br from-orange-500 via-red-500 to-fuchsia-600 shadow-lg shadow-orange-500/25">
          <Plus className="h-5 w-5" />
        </button>
      </header>

      <section className="relative mb-4 overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.07] p-5 shadow-2xl shadow-black/40 backdrop-blur-xl">
        <div className="absolute right-[-3rem] top-[-3rem] h-36 w-36 rounded-full bg-gradient-to-br from-blue-500 to-fuchsia-600 opacity-30 blur-2xl" />
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/45">Overview</p>
        <div className="mt-2 flex items-end gap-2">
          <h2 className="text-4xl font-black tracking-tight">{amount}</h2>
          <span className="mb-1 rounded-full bg-emerald-500/15 px-2 py-1 text-xs font-bold text-emerald-300">{badge}</span>
        </div>
        <p className="mt-2 max-w-[18rem] text-sm leading-5 text-white/55">{description}</p>
      </section>

      <div className="space-y-3">
        {cards.map(([name, value, subtitle]) => (
          <div key={name} className="flex items-center justify-between rounded-[1.5rem] border border-white/10 bg-[#151515] p-4 shadow-xl shadow-black/20">
            <div className="flex items-center gap-3">
              <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-orange-500 to-fuchsia-600">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-black">{name}</h3>
                <p className="text-sm text-white/45">{subtitle}</p>
              </div>
            </div>
            <p className="font-black">{value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function QuickAction({ icon: Icon, label, tone }: { icon: ElementType; label: string; tone: string }) {
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

function OutlineAction({ icon: Icon, label, tone }: { icon: ElementType; label: string; tone: "orange" | "blue" | "purple" }) {
  const styles = {
    orange: "border-orange-500 text-orange-300 shadow-orange-500/15",
    blue: "border-blue-500 text-blue-300 shadow-blue-500/15",
    purple: "border-fuchsia-500 text-fuchsia-300 shadow-fuchsia-500/15",
  };

  return (
    <button
      type="button"
      className={`flex h-12 items-center justify-center gap-2 rounded-2xl border-2 bg-black/20 text-xs font-black shadow-lg ${styles[tone]}`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}

function BankAccountRow({
  icon: Icon,
  iconClass,
  name,
  iban,
  amount,
  badges = false,
}: {
  icon: ElementType;
  iconClass: string;
  name: string;
  iban: string;
  amount: string;
  badges?: boolean;
}) {
  return (
    <div className="flex items-center gap-3 border-b border-white/10 px-4 py-3 last:border-b-0">
      <div className={`grid h-12 w-12 place-items-center rounded-2xl ${iconClass}`}>
        <Icon className="h-6 w-6 text-white" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-bold">{name}</p>
        {iban ? <p className="truncate text-xs text-white/40">{iban}</p> : null}
        {badges ? (
          <div className="mt-1 flex gap-1">
            <span className="grid h-5 w-5 place-items-center rounded-md bg-orange-500/20 text-xs">🍴</span>
            <span className="grid h-5 w-5 place-items-center rounded-md bg-yellow-500/20 text-xs">👕</span>
          </div>
        ) : null}
      </div>
      {amount ? <p className="font-black">{amount}</p> : <ChevronRight className="h-5 w-5 text-white/25" />}
    </div>
  );
}

function TransactionRow({
  logo,
  title,
  subtitle,
  amount,
  positive = false,
}: {
  logo: string;
  title: string;
  subtitle: string;
  amount: string;
  positive?: boolean;
}) {
  return (
    <div className="flex items-center gap-3 rounded-[1.45rem] bg-[#171717] p-3 shadow-xl shadow-black/20">
      <div className="grid h-12 w-12 place-items-center rounded-full bg-black text-xs font-black">{logo}</div>
      <div className="flex-1">
        <p className="font-bold">{title}</p>
        <p className="text-xs text-white/40">{subtitle}</p>
      </div>
      <p className={`font-black ${positive ? "text-emerald-400" : "text-orange-400"}`}>{amount}</p>
    </div>
  );
}

function NavItem({
  icon: Icon,
  label,
  active = false,
  onClick,
}: {
  icon: ElementType;
  label: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
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
