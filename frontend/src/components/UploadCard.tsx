"use client";

interface UploadCardProps {
  file: File | null;
  text: string;
  isLoading: boolean;
  onFileChange: (file: File | null) => void;
  onTextChange: (text: string) => void;
  onSubmit: () => void;
}

export function UploadCard({
  file,
  text,
  isLoading,
  onFileChange,
  onTextChange,
  onSubmit,
}: UploadCardProps) {
  return (
    <section className="rounded-[28px] border border-white/80 bg-white p-5 shadow-panel">
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-bunqBlue">
          Upload inbox item
        </p>
        <h2 className="mt-2 text-xl font-semibold text-slate-950">
          Drop a bill, fine, tax letter, or scammy screenshot
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          We extract the payment details, score risk, and prepare the safest bunq
          action for review.
        </p>
      </div>

      <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center">
        <input
          type="file"
          className="hidden"
          accept=".jpg,.jpeg,.png,.webp,.heic,.pdf"
          onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
        />
        <span className="rounded-full bg-mint px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-900">
          {file ? "Document attached" : "Tap to upload"}
        </span>
        <span className="mt-3 text-sm font-medium text-slate-700">
          {file ? file.name : "Photo, screenshot, or PDF"}
        </span>
        <span className="mt-1 text-xs text-slate-500">
          JPG, PNG, WEBP, HEIC, PDF
        </span>
      </label>

      <div className="mt-4">
        <label className="mb-2 block text-sm font-medium text-slate-700">
          Optional pasted email or extra context
        </label>
        <textarea
          value={text}
          onChange={(event) => onTextChange(event.target.value)}
          rows={5}
          placeholder="Paste email text, payment note, or extra details here..."
          className="w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none ring-0 placeholder:text-slate-400 focus:border-slate-400"
        />
      </div>

      <button
        type="button"
        onClick={onSubmit}
        disabled={isLoading || (!file && !text.trim())}
        className="mt-4 w-full rounded-2xl bg-bunqBlue px-4 py-4 text-sm font-semibold text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {isLoading ? "Analyzing document..." : "Analyze with FinPilot"}
      </button>
    </section>
  );
}
