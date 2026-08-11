import { HTMLInputTypeAttribute, ReactNode } from "react";
import { type FieldError, type UseFormRegisterReturn } from "react-hook-form";

export default function FormField({
  label,
  type = "text",
  placeholder,
  description,
  error,
  register,
  children,
}: {
  label: string;
  type?: HTMLInputTypeAttribute;
  placeholder?: string;
  description?: string;
  error?: FieldError;
  register?: UseFormRegisterReturn;
  children?: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-medium text-slate-700">{label}</span>
      {children ? (
        children
      ) : (
        <input
          type={type}
          placeholder={placeholder}
          {...(register ?? {})}
          className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
        />
      )}
      {description ? <p className="mt-2 text-xs text-slate-500">{description}</p> : null}
      {error ? <p className="mt-2 text-xs text-red-600">{error.message}</p> : null}
    </label>
  );
}
