type PageContainerProps = {
  children: React.ReactNode;
};

export default function PageContainer({
  children,
}: PageContainerProps) {
  return (
    <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">
      {children}
    </main>
  );
}