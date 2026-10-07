interface NotificationDotProps {
  count?: number;
  showZero?: boolean;
}

export default function NotificationDot({
  count = 0,
  showZero = false,
}: NotificationDotProps) {
  if (count === 0 && !showZero) {
    return null;
  }

  const displayCount = count > 99 ? "99+" : count;

  return (
    <span className="absolute -right-1 -top-1 flex min-h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white shadow-sm">
      {displayCount}
    </span>
  );
}