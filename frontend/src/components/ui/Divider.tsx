interface DividerProps {
  label?: string;
}

export default function Divider({ label }: DividerProps) {
  if (!label) {
    return <div className="h-px w-full bg-slate-200 dark:bg-slate-700" />;
  }

  return (
    <div className="flex items-center gap-4">
      <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />

      <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </span>

      <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
    </div>
  );
}