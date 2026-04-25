import { CheckCircle2, ShieldCheck } from "lucide-react";
import { ConfirmActionResponse } from "@/types/analysis";

function formatCurrency(amount: number | null, currency: string) {
  if (amount === null) return "—";
  return new Intl.NumberFormat("en-NL", { style: "currency", currency }).format(amount);
}

const STATE_LABEL: Record<string, string> = {
  created: "Processed",
  scheduled: "Scheduled",
  prepared: "Prepared",
  blocked: "Blocked",
  iban_invalid: "IBAN unverified",
  not_required: "No action",
};

export function BunqReceiptCard({ result }: { result: ConfirmActionResponse }) {
  const action = result.prepared_action;
  const isLive = action.bunq_action_id && action.bunq_mode === "live";
  const stateLabel = STATE_LABEL[action.execution_state] ?? action.execution_state;
  const actionType = action.bunq_action_type.replaceAll("_", " ");

  return (
    <section className="overflow-hidden rounded-[28px] border border-emerald-200 bg-white p-5 shadow-panel">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="grid h-12 w-12 place-items-center rounded-2xl bg-emerald-500 text-white">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-700">bunq receipt</p>
            <h3 className="mt-1 text-lg font-black text-slate-950">
              {isLive ? `bunq ${actionType} created` : "Action prepared"}
            </h3>
            <p className="text-sm text-slate-600">{result.message}</p>
          </div>
        </div>
        <span className="rounded-full bg-blue-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-blue-700 ring-1 ring-blue-200">
          {action.bunq_mode === "live" ? "Sandbox · live API" : "Mock"}
        </span>
      </div>

      <div className="mt-4 rounded-2xl bg-slate-950 p-4 text-white">
        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Amount</p>
        <p className="mt-1 text-3xl font-black">
          {formatCurrency(action.amount, action.currency)}
        </p>
        <p className="mt-2 text-sm text-slate-300">
          {action.beneficiary_name ?? "Detected beneficiary"}
          {action.beneficiary_iban ? ` · ${action.beneficiary_iban}` : ""}
        </p>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">From</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">{result.account_used}</p>
          {result.account_iban ? (
            <p className="mt-1 truncate text-xs text-slate-500">{result.account_iban}</p>
          ) : null}
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Status</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">{stateLabel}</p>
          {action.due_date ? (
            <p className="mt-1 truncate text-xs text-slate-500">For {action.due_date}</p>
          ) : null}
        </div>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">bunq id</p>
          <p className="mt-1 break-all font-mono text-sm font-semibold text-slate-900">
            {action.bunq_action_id ?? "—"}
          </p>
        </div>
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-700">deBunq TrustScore</p>
          </div>
          <p className="mt-1 text-sm font-semibold text-emerald-800">
            {action.trust_score}/100 · {action.risk_level}
          </p>
        </div>
      </div>

      {action.bunq_endpoint ? (
        <div className="mt-3 rounded-2xl bg-slate-950 p-3 text-slate-100">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">bunq API call</p>
          <p className="mt-1 break-all font-mono text-xs">{action.bunq_endpoint}</p>
        </div>
      ) : null}
    </section>
  );
}
