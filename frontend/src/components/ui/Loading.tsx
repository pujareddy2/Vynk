interface LoadingProps {
  text?: string;
  fullPage?: boolean;
}

export default function Loading({
  text = "Loading...",
  fullPage = false,
}: LoadingProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="flex items-center gap-2">
        <span className="h-3 w-3 animate-bounce rounded-full bg-teal-500 [animation-delay:-0.3s]" />
        <span className="h-3 w-3 animate-bounce rounded-full bg-teal-500 [animation-delay:-0.15s]" />
        <span className="h-3 w-3 animate-bounce rounded-full bg-teal-500" />
      </div>

      <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
        {text}
      </p>
    </div>
  );

  if (fullPage) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-6">
        {content}
      </div>
    );
  }

  return <div className="flex justify-center p-8">{content}</div>;
}