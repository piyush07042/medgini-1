import type { ReactNode } from "react";
import { Inbox } from "lucide-react";

export default function EmptyState({
  title,
  description,
  icon,
  action,
  secondaryAction,
}: {
  title: string;
  description: string;
  icon?: ReactNode;
  action?: ReactNode;
  secondaryAction?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-slate-200 bg-slate-50/80 px-6 py-10 text-center transition-all">
      <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-brand-600 shadow-sm ring-1 ring-slate-200/80">
        {icon ?? <Inbox className="h-6 w-6" />}
      </div>
      <p className="text-base font-semibold text-slate-900">{title}</p>
      <p className="mt-2 max-w-sm text-sm leading-6 text-slate-600">{description}</p>
      {(action || secondaryAction) && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {action}
          {secondaryAction}
        </div>
      )}
    </div>
  );
}
