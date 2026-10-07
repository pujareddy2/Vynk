interface RatingProps {
  value: number;
  max?: number;
  showValue?: boolean;
}

export default function Rating({
  value,
  max = 5,
  showValue = true,
}: RatingProps) {
  const safeValue = Math.min(Math.max(value, 0), max);

  return (
    <div
      className="inline-flex items-center gap-2"
      aria-label={`Rating ${safeValue} out of ${max}`}
    >
      <div className="flex items-center">
        {Array.from({ length: max }, (_, index) => (
          <span
            key={index}
            className={
              index < Math.round(safeValue)
                ? "text-amber-400"
                : "text-slate-300 dark:text-slate-600"
            }
          >
            ★
          </span>
        ))}
      </div>

      {showValue && (
        <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">
          {safeValue.toFixed(1)}
        </span>
      )}
    </div>
  );
}