import { AnalysisResponse } from "@/types/analysis";
import { TrustScoreCard } from "@/components/TrustScoreCard";

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
            Document type
          </p>
          <h3 className="mt-2 text-2xl font-semibold capitalize text-slate-950">
            {labelize(analysis.document_type)}
          </h3>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
          {formatCurrency(analysis.amount, analysis.currency)}
        </span>
      </div>

      {analysis.transcript ? (
        <div className="mt-5 rounded-3xl border border-indigo-200 bg-indigo-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-700">
            Heard from voice note
          </p>
          <p className="mt-2 text-sm italic leading-6 text-indigo-900">
            &ldquo;{analysis.transcript}&rdquo;
          </p>
        </div>
      ) : null}

      <div className="mt-5">
        <TrustScoreCard analysis={analysis} />
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
    </section>
  );
}
