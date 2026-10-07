interface PriceProps {
  amount: number;
  currency?: string;
  period?: string;
}

export default function Price({
  amount,
  currency = "₹",
  period,
}: PriceProps) {
  return (
    <span className="inline-flex items-baseline gap-1">
      <span className="text-2xl font-bold text-slate-900 dark:text-white">
        {currency}
        {amount.toLocaleString("en-IN")}
      </span>

      {period && (
        <span className="text-sm text-slate-500 dark:text-slate-400">
          {period}
        </span>
      )}
    </span>
  );
}