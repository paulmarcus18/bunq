"use client";

import { useRef } from "react";

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
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const isAudio =
    file?.type.startsWith("audio/") ||
    /\.(m4a|mp3|wav|webm|ogg)$/i.test(file?.name ?? "");

  return (
    <section className="rounded-[28px] border border-white/80 bg-white p-5 shadow-panel">
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-bunqBlue">
          Run a deBunq check
        </p>
        <h2 className="mt-2 text-xl font-semibold text-slate-950">
          Got a payment request? Check it before paying.
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Drop a bill, screenshot, scammy email, or a forwarded WhatsApp voice note.
          deBunq scores how trustworthy it is and only lets bunq pay when the request looks safe.
        </p>
      </div>

      <input
        ref={cameraInputRef}
        type="file"
        className="hidden"
        accept="image/*"
        capture="environment"
        onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
      />
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".jpg,.jpeg,.png,.webp,.heic,.pdf"
        onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
      />
      <input
        ref={audioInputRef}
        type="file"
        className="hidden"
        accept="audio/*,.m4a,.mp3,.wav,.webm,.ogg"
        onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
      />

      <div className="flex min-h-36 flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center">
        <span className="rounded-full bg-mint px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-900">
          {file ? (isAudio ? "Voice note attached" : "Document attached") : "deBunq ready"}
        </span>
        <span className="mt-3 text-sm font-medium text-slate-700">
          {file
            ? file.name
            : "Photo of a bill, screenshot of an email, PDF, or a forwarded voice note"}
        </span>
        <span className="mt-1 text-xs text-slate-500">
          Image: JPG · PNG · HEIC · PDF · Audio: M4A · MP3 · WAV
        </span>

        <div className="mt-5 grid w-full grid-cols-1 gap-3 sm:grid-cols-3">
          <button
            type="button"
            onClick={() => cameraInputRef.current?.click()}
            className="rounded-2xl bg-bunqBlue px-3 py-3 text-sm font-semibold text-white transition hover:bg-blue-600"
          >
            Snap a bill
          </button>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="rounded-2xl border border-slate-200 bg-white px-3 py-3 text-sm font-semibold text-slate-900 transition hover:border-slate-300"
          >
            Upload screenshot
          </button>
          <button
            type="button"
            onClick={() => audioInputRef.current?.click()}
            className="rounded-2xl bg-slate-900 px-3 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            Forward voice note
          </button>
        </div>
      </div>

      <div className="mt-4">
        <label className="mb-2 block text-sm font-medium text-slate-700">
          Or paste an email or message you received
        </label>
        <textarea
          value={text}
          onChange={(event) => onTextChange(event.target.value)}
          rows={5}
          placeholder="Paste an email, WhatsApp message, payment note, or other suspicious text here..."
          className="w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none ring-0 placeholder:text-slate-400 focus:border-slate-400"
        />
      </div>

      <button
        type="button"
        onClick={onSubmit}
        disabled={isLoading || (!file && !text.trim())}
        className="mt-4 w-full rounded-2xl bg-bunqBlue px-4 py-4 text-sm font-semibold text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {isLoading
          ? isAudio
            ? "Transcribing & scoring..."
            : "Scoring trust..."
          : "Run deBunq check"}
      </button>
    </section>
  );
}
