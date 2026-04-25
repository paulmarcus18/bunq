import { AnalysisResponse, BunqAccountSummary } from "@/types/analysis";

function formatCurrency(amount: number | null, currency: string) {
  if (amount === null) return "—";
  return new Intl.NumberFormat("en-NL", { style: "currency", currency }).format(amount);
}

export function BunqPreflightCard({
  analysis,
  selectedAccount,
}: {
  analysis: AnalysisResponse;
  selectedAccount: BunqAccountSummary | null;
}) {
  if (!analysis.action_required) {
    return null;
  }

  const endpointPath =
    analysis.recommended_action === "schedule_payment"
      ? `POST /v1/user/{userId}/monetary-account/${selectedAccount?.id ?? "{accountId}"}/schedule-payment`
      : `POST /v1/user/{userId}/monetary-account/${selectedAccount?.id ?? "{accountId}"}/payment`;

  const actionLabel =
    analysis.recommended_action === "schedule_payment"
      ? "Scheduled bunq payment"
      : "Immediate bunq payment";

  return (
    <section className="overflow-hidden rounded-[28px] border border-blue-200 bg-white p-5 shadow-panel">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-700">bunq pre-flight</p>
          <h3 className="mt-1 text-lg font-black text-slate-950">{actionLabel}</h3>
        </div>
        <span className="rounded-full bg-blue-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-blue-700 ring-1 ring-blue-200">
          Sandbox
        </span>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">From</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">
            {selectedAccount?.description ?? "Pick an account"}
          </p>
          <p className="mt-1 truncate text-xs text-slate-500">
            {selectedAccount?.iban ?? "—"}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">To</p>
          <p className="mt-1 truncate text-sm font-semibold text-slate-900">
            {analysis.beneficiary_name ?? analysis.issuer_name ?? "Detected beneficiary"}
          </p>
          <p className="mt-1 truncate text-xs text-slate-500">
            {analysis.beneficiary_iban ?? "—"}
          </p>
        </div>
      </div>

      <div className="mt-4 flex items-end justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Amount</p>
          <p className="mt-1 text-2xl font-black text-slate-950">
            {formatCurrency(analysis.amount, analysis.currency)}
          </p>
        </div>
        {analysis.due_date ? (
          <div className="text-right">
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
              {analysis.recommended_action === "schedule_payment" ? "Scheduled for" : "Due date"}
            </p>
            <p className="mt-1 text-sm font-semibold text-slate-900">{analysis.due_date}</p>
          </div>
        ) : null}
      </div>

      {analysis.payment_reference ? (
        <div className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Reference</p>
          <p className="mt-1 break-all font-mono text-xs text-slate-900">{analysis.payment_reference}</p>
        </div>
      ) : null}

      <div className="mt-4 rounded-2xl bg-slate-950 p-3 text-slate-100">
        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">bunq API call</p>
        <p className="mt-1 break-all font-mono text-xs">{endpointPath}</p>
      </div>
    </section>
  );
}
