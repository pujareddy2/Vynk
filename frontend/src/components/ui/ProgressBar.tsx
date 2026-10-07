interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
}

export default function ProgressBar({
  value,
  max = 100,
  label,
  showValue = false,
}: ProgressBarProps) {
  const safeMax = Math.max(max, 1);
  const percentage = Math.min(
    100,
    Math.max(0, (value / safeMax) * 100),
  );

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="mb-2 flex items-center justify-between gap-4">
          {label && (
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              {label}
            </span>
          )}

          {showValue && (
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}

      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={safeMax}
        aria-valuenow={Math.min(value, safeMax)}
        className="h-2.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700"
      >
        <div
          className="h-full rounded-full bg-teal-500 transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}