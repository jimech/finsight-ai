import Link from "next/link";

import { TransactionSearchPanel } from "@/components/transaction-search-panel";

export default function TransactionSearchPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-16">
      <div className="mx-auto w-full max-w-3xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              Search transactions
            </h1>
            <p className="mt-2 text-zinc-600 dark:text-zinc-400">
              Find relevant transaction snippets for future AI citations.
            </p>
          </div>
          <Link
            href="/transactions"
            className="text-sm font-medium text-zinc-900 underline dark:text-zinc-100"
          >
            Back to transactions
          </Link>
        </div>

        <div className="mt-8">
          <TransactionSearchPanel />
        </div>
      </div>
    </main>
  );
}
