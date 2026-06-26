const COLUMNS = [
  "date",
  "description",
  "merchant",
  "amount",
  "category",
] as const;

const EXAMPLE_ROWS = [
  {
    date: "2026-01-02",
    description: "STARBUCKS #123",
    merchant: "Starbucks",
    amount: "-5.75",
    category: "Coffee",
  },
  {
    date: "2026-01-03",
    description: "PAYROLL ACME INC",
    merchant: "Acme Inc",
    amount: "3500.00",
    category: "Income",
  },
  {
    date: "2026-01-04",
    description: "TRADER JOES",
    merchant: "Trader Joes",
    amount: "-86.21",
    category: "Groceries",
  },
] as const;

const COPY_SNIPPET = `date,description,merchant,amount,category
2026-01-02,STARBUCKS #123,Starbucks,-5.75,Coffee
2026-01-03,PAYROLL ACME INC,Acme Inc,3500.00,Income
2026-01-04,TRADER JOES,Trader Joes,-86.21,Groceries`;

export function DemoCsvGuide() {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
        Demo CSV format
      </h2>
      <p className="mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
        Upload a CSV with a header row. Required columns are{" "}
        <span className="font-mono text-zinc-800 dark:text-zinc-200">
          date
        </span>
        ,{" "}
        <span className="font-mono text-zinc-800 dark:text-zinc-200">
          description
        </span>
        , and{" "}
        <span className="font-mono text-zinc-800 dark:text-zinc-200">
          amount
        </span>
        . Optional: merchant, category.
      </p>
      <ul className="mt-4 flex flex-wrap gap-2">
        {COLUMNS.map((column) => (
          <li
            key={column}
            className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-1.5 font-mono text-xs text-zinc-800 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-200"
          >
            {column}
          </li>
        ))}
      </ul>

      <div className="mt-6 overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
        <table className="min-w-full divide-y divide-zinc-200 text-sm dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-950">
            <tr>
              {COLUMNS.map((column) => (
                <th
                  key={column}
                  className="px-4 py-3 text-left font-medium text-zinc-500"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 bg-white dark:divide-zinc-800 dark:bg-zinc-900">
            {EXAMPLE_ROWS.map((row) => (
              <tr key={row.date}>
                <td className="px-4 py-3 font-mono text-xs text-zinc-700 dark:text-zinc-300">
                  {row.date}
                </td>
                <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100">
                  {row.description}
                </td>
                <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">
                  {row.merchant}
                </td>
                <td className="px-4 py-3 font-mono text-zinc-700 dark:text-zinc-300">
                  {row.amount}
                </td>
                <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">
                  {row.category}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-4 text-xs text-zinc-500 dark:text-zinc-400">
        Use negative amounts for spending and positive amounts for income.
      </p>

      <div className="mt-4">
        <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
          Copyable snippet
        </p>
        <pre className="mt-2 overflow-x-auto rounded-lg bg-zinc-950 p-4 text-xs leading-6 text-zinc-100">
          {COPY_SNIPPET}
        </pre>
      </div>
    </section>
  );
}
