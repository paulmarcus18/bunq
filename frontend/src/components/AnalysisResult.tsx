import { AnalysisResponse } from "@/types/analysis";
import { RiskBadge } from "./RiskBadge";

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

export function AnalysisResult({ analysis }: { analysis: AnalysisResponse }) {
  const details = [
    { label: "Receiver", value: analysis.recipient_name ?? analysis.sender ?? "Unknown" },
    { label: "IBAN", value: analysis.iban ?? "Not found" },
    { label: "Reference", value: analysis.payment_reference ?? "Not found" },
    { label: "Due date", value: analysis.due_date ?? "No deadline detected" },
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
        <RiskBadge level={analysis.risk_level} />
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
        <p className="mt-2 text-lg font-semibold capitalize text-slate-950">
          {labelize(analysis.recommended_action)}
        </p>
        <p className="mt-2 text-sm leading-6 text-slate-600">{analysis.reasoning}</p>
        <p className="mt-3 text-xs text-slate-500">
          Urgency: <span className="font-semibold capitalize">{analysis.urgency}</span>
          {" · "}
          Confidence: <span className="font-semibold">{Math.round(analysis.confidence * 100)}%</span>
        </p>
      </div>
    </section>
  );
}
