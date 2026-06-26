type PortfolioNoticeProps = {
  compact?: boolean;
};

export function PortfolioNotice({ compact = false }: PortfolioNoticeProps) {
  return (
    <div
      className={`rounded-xl border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 ${
        compact ? "p-4" : "p-6"
      }`}
    >
      <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
        Portfolio demo — not financial advice
      </p>
      <p
        className={`mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-400 ${
          compact ? "" : "max-w-3xl"
        }`}
      >
        FinSight AI is a demo project. Spending totals and plans come from
        deterministic backend analytics. AI coach answers cite those tools and
        retrieved transaction snippets—they do not replace professional
        financial, tax, or legal advice.
      </p>
    </div>
  );
}
