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
}: {
  analysis: AnalysisResponse;
}) {
  const suspiciousBlocked = analysis.is_suspicious;
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
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${
            suspiciousBlocked
              ? "border border-rose-200 bg-rose-50 text-rose-700"
              : "border border-slate-200 bg-slate-50 text-slate-600"
          }`}
        >
          {suspiciousBlocked ? "Blocked" : analysis.action_required ? "Action ready" : "Review needed"}
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
        {details.map((item) => {
          const isLongField = item.label === "IBAN" || item.label === "Reference";
          const isBeneficiary = item.label === "Beneficiary";

          return (
            <div
              key={item.label}
              className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <p className="text-xs uppercase tracking-[0.15em] text-slate-500">
                {item.label}
              </p>
              <p
                className={`mt-2 text-sm font-medium text-slate-900 ${
                  isLongField
                    ? "break-all"
                    : isBeneficiary
                      ? "break-words"
                      : ""
                }`}
              >
                {item.value}
              </p>
            </div>
          );
        })}
      </div>

      {suspiciousBlocked ? (
        <div className="mt-5 rounded-3xl border border-rose-200 bg-rose-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-rose-700">
            Potential phishing detected
          </p>
          <p className="mt-2 text-sm text-rose-800">
            FinPilot spotted warning signs and is blocking bunq payment creation for this request.
          </p>
          {analysis.phishing_signals.length ? (
            <ul className="mt-3 space-y-2 text-sm text-rose-800">
              {analysis.phishing_signals.map((signal) => (
                <li key={signal}>• {signal}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}