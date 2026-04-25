import { AnalysisResponse } from "@/types/analysis";

function formatCurrency(amount: number | null, currency: string) {
  if (amount === null) {
    return "Unknown";
  }

  return new Intl.NumberFormat("en-NL", {
    style: "currency",
    currency,
  }).format(amount);
}

function labelize(value: string) {
  return value.replaceAll("_", " ");
}

export function AnalysisResult({
  analysis,
  onChange,
}: {
  analysis: AnalysisResponse;
  onChange?: (patch: Partial<AnalysisResponse>) => void;
}) {
  const scheduleDisabled = analysis.auto_debit_detected || !analysis.due_date;
  const payNowDisabled = analysis.auto_debit_detected;
  const details = [
    { label: "Issuer", value: analysis.issuer_name ?? "Unknown" },
    { label: "Beneficiary", value: analysis.beneficiary_name ?? analysis.issuer_name ?? "Unknown" },
    { label: "IBAN", value: analysis.beneficiary_iban ?? "Not found" },
    { label: "Reference", value: analysis.payment_reference ?? "Not found" },
    { label: "Due date", value: analysis.due_date ?? "No deadline detected" },
    {
      label: "Payment mode",
      value: analysis.auto_debit_detected
        ? "Automatic debit"
        : analysis.manual_payment_required
          ? "Manual transfer"
          : "Review only",
    },
  ];

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Analysis result
          </p>
          <h3 className="mt-2 text-2xl font-semibold capitalize text-slate-950">
            {labelize(analysis.document_type)}
          </h3>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
          {analysis.action_required ? "Action ready" : "Review needed"}
        </span>
      </div>

      <div className="mt-5 rounded-3xl bg-slate-950 p-5 text-white">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-300">Amount</p>
        <p className="mt-2 text-3xl font-semibold">
          {formatCurrency(analysis.amount, analysis.currency)}
        </p>
        <p className="mt-2 text-sm text-slate-300">{analysis.summary}</p>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        {details.map((item) => (
          <div key={item.label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.15em] text-slate-500">{item.label}</p>
            <p className="mt-2 text-sm font-medium text-slate-900">{item.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-5 rounded-3xl border border-slate-200 bg-white p-4">
        <p className="text-xs uppercase tracking-[0.15em] text-slate-500">Recommended action</p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <button
            type="button"
            disabled={payNowDisabled}
            onClick={() =>
              onChange?.({
                recommended_action: "pay_now",
              })
            }
            className={`rounded-2xl px-4 py-3 text-sm font-semibold transition ${
              analysis.recommended_action === "pay_now"
                ? "bg-slate-950 text-white"
                : "border border-slate-200 bg-slate-50 text-slate-700"
            } ${payNowDisabled ? "cursor-not-allowed opacity-50" : ""}`}
          >
            Pay now
          </button>
          <button
            type="button"
            disabled={scheduleDisabled}
            onClick={() =>
              onChange?.({
                recommended_action: "schedule_payment",
              })
            }
            className={`rounded-2xl px-4 py-3 text-sm font-semibold transition ${
              analysis.recommended_action === "schedule_payment"
                ? "bg-slate-950 text-white"
                : "border border-slate-200 bg-slate-50 text-slate-700"
            } ${scheduleDisabled ? "cursor-not-allowed opacity-50" : ""}`}
          >
            Schedule
          </button>
        </div>

        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.15em] text-slate-500">Chosen date</p>
              <p className="mt-1 text-sm text-slate-700">
                {analysis.due_date ?? "No due date detected yet"}
              </p>
            </div>
            <input
              type="date"
              value={analysis.due_date ?? ""}
              onChange={(event) => onChange?.({ due_date: event.target.value || null })}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-400"
            />
          </div>
          {analysis.recommended_action === "schedule_payment" ? (
            <p className="mt-3 text-sm text-slate-600">
              FinPilot will create a bunq scheduled payment before this due date.
            </p>
          ) : null}
        </div>

        {analysis.auto_debit_detected ? (
          <p className="mt-3 text-sm font-medium text-emerald-700">
            Automatic debit detected. FinPilot is avoiding a duplicate manual payment.
          </p>
        ) : null}
        {!analysis.auto_debit_detected && !analysis.due_date ? (
          <p className="mt-3 text-sm font-medium text-amber-700">
            Add a due date to enable the schedule option.
          </p>
        ) : null}
        {!analysis.auto_debit_detected && analysis.manual_payment_required ? (
          <p className="mt-3 text-sm font-medium text-slate-700">
            Manual payment is required before a bunq action can be created.
          </p>
        ) : null}
      </div>
    </section>
  );
}
