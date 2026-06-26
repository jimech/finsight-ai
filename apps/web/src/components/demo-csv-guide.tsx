const COLUMNS = [
  "date",
  "description",
  "merchant",
  "amount",
  "category",
] as const;

export function DemoCsvGuide() {
  return (
    <section className="rounded-xl border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
        Demo data format
      </h2>
      <p className="mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
        Upload a CSV export from your bank or card provider. Include a header
        row with these columns:
      </p>
      <ul className="mt-4 flex flex-wrap gap-2">
        {COLUMNS.map((column) => (
          <li
            key={column}
            className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 font-mono text-xs text-zinc-800 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
          >
            {column}
          </li>
        ))}
      </ul>
      <p className="mt-4 text-xs leading-5 text-zinc-500 dark:text-zinc-400">
        Example row:{" "}
        <span className="font-mono text-zinc-700 dark:text-zinc-300">
          2024-01-15, Morning coffee, Blue Bottle, -5.50, Food &amp; Drink
        </span>
      </p>
      <p className="mt-2 text-xs leading-5 text-zinc-500 dark:text-zinc-400">
        Use negative amounts for spending and positive amounts for income.
      </p>
    </section>
  );
}
