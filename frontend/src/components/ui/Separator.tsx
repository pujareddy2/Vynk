interface SeparatorProps {
  orientation?: "horizontal" | "vertical";
  className?: string;
}

export default function Separator({
  orientation = "horizontal",
  className = "",
}: SeparatorProps) {
  if (orientation === "vertical") {
    return (
      <div
        aria-hidden="true"
        className={`h-full w-px bg-slate-200 dark:bg-slate-700 ${className}`}
      />
    );
  }

  return (
    <div
      aria-hidden="true"
      className={`h-px w-full bg-slate-200 dark:bg-slate-700 ${className}`}
    />
  );
}