import { type ReactNode } from "react";
import type { FieldValues, UseFormHandleSubmit } from "react-hook-form";

export default function PredictionForm<T extends FieldValues>({
  children,
  handleSubmit,
  onSubmit,
  isSubmitting,
  onReset,
  submitLabel = "Run prediction",
  resetLabel = "Reset form",
}: {
  children: ReactNode;
  handleSubmit: UseFormHandleSubmit<T>;
  onSubmit: (values: T) => Promise<void>;
  isSubmitting: boolean;
  onReset: () => void;
  submitLabel?: string;
  resetLabel?: string;
}) {
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      {children}
      <div className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        <p className="font-semibold">Clinical note</p>
        <p className="mt-1">Input values should reflect the latest patient measurements. Predictions are supportive only and should be reviewed by a clinician.</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {isSubmitting ? "Predicting..." : submitLabel}
        </button>
        <button
          type="button"
          onClick={onReset}
          className="rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-200"
        >
          {resetLabel}
        </button>
      </div>
    </form>
  );
}
