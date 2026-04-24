"use client";

interface ActionButtonProps {
  disabled?: boolean;
  loading?: boolean;
  onClick: () => void;
  label: string;
}

export function ActionButton({
  disabled,
  loading,
  onClick,
  label,
}: ActionButtonProps) {
  return (
    <div className="sticky bottom-0 left-0 right-0 mt-6 border-t border-slate-200 bg-white/90 px-4 py-4 backdrop-blur">
      <button
        type="button"
        onClick={onClick}
        disabled={disabled || loading}
        className="w-full rounded-2xl bg-slate-950 px-5 py-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {loading ? "Preparing action..." : label}
      </button>
    </div>
  );
}
