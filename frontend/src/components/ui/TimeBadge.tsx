interface TimeBadgeProps {
  time: string;
  label?: string;
}

export default function TimeBadge({
  time,
  label = "Time",
}: TimeBadgeProps) {
  return (
    <div className="inline-flex items-center gap-2 rounded-xl bg-slate-100 px-3 py-2 dark:bg-slate-800">
      <span
        aria-hidden="true"
        className="text-sm"
      >
        🕒
      </span>

      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </p>

        <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
          {time}
        </p>
      </div>
    </div>
  );
}