import { AnalysisResponse } from "@/types/analysis";

export function ActionReviewCard({
  analysis,
  onChange,
}: {
  analysis: AnalysisResponse;
  onChange?: (patch: Partial<AnalysisResponse>) => void;
}) {
  const suspiciousBlocked = analysis.is_suspicious;
  const scheduleDisabled = suspiciousBlocked || analysis.auto_debit_detected || !analysis.due_date;
  const payNowDisabled = suspiciousBlocked || analysis.auto_debit_detected;

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
        Payment setup
      </p>
      <h3 className="mt-2 text-xl font-semibold text-slate-950">
        Choose how FinPilot should act
      </h3>

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

        {suspiciousBlocked ? (
          <p className="mt-3 text-sm font-medium text-rose-700">
            bunq actions are disabled while this request is marked as suspicious.
          </p>
        ) : null}
        {analysis.auto_debit_detected ? (
          <p className="mt-3 text-sm font-medium text-emerald-700">
            Automatic debit detected. FinPilot is avoiding a duplicate manual payment.
          </p>
        ) : null}
        {!suspiciousBlocked && !analysis.auto_debit_detected && !analysis.due_date ? (
          <p className="mt-3 text-sm font-medium text-amber-700">
            Add a due date to enable the schedule option.
          </p>
        ) : null}
        {!suspiciousBlocked && !analysis.auto_debit_detected && analysis.manual_payment_required ? (
          <p className="mt-3 text-sm font-medium text-slate-700">
            Manual payment is required before a bunq action can be created.
          </p>
        ) : null}
      </div>
    </section>
  );
}
