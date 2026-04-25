import { AnalysisResponse } from "@/types/analysis";

const RISK_THEME = {
  safe: {
    ring: "stroke-emerald-500",
    text: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    label: "Safe to pay",
    pillBg: "bg-emerald-100",
  },
  caution: {
    ring: "stroke-amber-500",
    text: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
    label: "Review before paying",
    pillBg: "bg-amber-100",
  },
  blocked: {
    ring: "stroke-rose-500",
    text: "text-rose-700",
    bg: "bg-rose-50",
    border: "border-rose-200",
    label: "Likely scam — blocked",
    pillBg: "bg-rose-100",
  },
} as const;

const SUB_LABELS: Record<keyof AnalysisResponse["trust_breakdown"], string> = {
  issuer_authenticity: "Issuer authenticity",
  urgency_pressure: "No urgency pressure",
  payment_detail_completeness: "Payment details",
  modality_risk: "Source channel",
};

function ScoreRing({ score, riskLevel }: { score: number; riskLevel: AnalysisResponse["risk_level"] }) {
  const theme = RISK_THEME[riskLevel];
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.max(0, Math.min(100, score)) / 100);

  return (
    <div className="relative h-28 w-28 shrink-0">
      <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
        <circle cx="50" cy="50" r={radius} className="fill-none stroke-slate-200" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r={radius}
          className={`fill-none ${theme.ring}`}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-3xl font-black leading-none ${theme.text}`}>{score}</span>
        <span className="mt-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
          / 100
        </span>
      </div>
    </div>
  );
}

function SubScoreBar({ label, value }: { label: string; value: number }) {
  const tone = value >= 75 ? "bg-emerald-500" : value >= 40 ? "bg-amber-500" : "bg-rose-500";
  return (
    <div>
      <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
        <span>{label}</span>
        <span className="text-slate-500">{value}</span>
      </div>
      <div className="mt-1 h-2 w-full rounded-full bg-slate-200">
        <div className={`h-2 rounded-full ${tone}`} style={{ width: `${Math.max(4, Math.min(100, value))}%` }} />
      </div>
    </div>
  );
}

export function TrustScoreCard({ analysis }: { analysis: AnalysisResponse }) {
  const theme = RISK_THEME[analysis.risk_level];
  const breakdown = analysis.trust_breakdown;
  const positives = analysis.trust_reasons.filter((reason) => reason.polarity === "positive");
  const negatives = analysis.trust_reasons.filter((reason) => reason.polarity === "negative");

  return (
    <section className={`overflow-hidden rounded-[28px] border ${theme.border} ${theme.bg} p-5`}>
      <div className="flex items-center gap-5">
        <ScoreRing score={analysis.trust_score} riskLevel={analysis.risk_level} />
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">deBunq TrustScore</p>
          <h3 className={`mt-1 text-xl font-black leading-tight ${theme.text}`}>{theme.label}</h3>
          <p className="mt-1 text-sm text-slate-700">{analysis.summary}</p>
          {analysis.input_modality === "voice" ? (
            <span className={`mt-2 inline-block rounded-full ${theme.pillBg} px-2 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${theme.text}`}>
              Voice message check
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {(Object.keys(SUB_LABELS) as (keyof typeof SUB_LABELS)[]).map((key) => (
          <SubScoreBar key={key} label={SUB_LABELS[key]} value={breakdown[key]} />
        ))}
      </div>

      {positives.length || negatives.length ? (
        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {positives.length ? (
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-emerald-700">What looks right</p>
              <ul className="mt-2 space-y-2">
                {positives.map((reason) => (
                  <li key={reason.text} className="flex gap-2 text-sm text-slate-800">
                    <span className="text-emerald-600">✓</span>
                    <span>{reason.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {negatives.length ? (
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-rose-700">Red flags</p>
              <ul className="mt-2 space-y-2">
                {negatives.map((reason) => (
                  <li key={reason.text} className="flex gap-2 text-sm text-slate-800">
                    <span className="text-rose-600">✗</span>
                    <span>{reason.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
