interface SkeletonProps {
  className?: string;
}

export default function Skeleton({
  className = "",
}: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-xl bg-slate-200 dark:bg-slate-700 ${className}`}
    />
  );
}