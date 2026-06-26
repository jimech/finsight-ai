import Link from "next/link";

import { TransactionsList } from "@/components/transactions-list";

export default function TransactionsPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-16">
      <div className="mx-auto w-full max-w-5xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              Transactions
            </h1>
            <p className="mt-2 text-zinc-600 dark:text-zinc-400">
              Your recently imported transactions.
            </p>
          </div>
          <Link
            href="/transactions/upload"
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            Upload CSV
          </Link>
        </div>
        <div className="mt-8">
          <TransactionsList />
        </div>
        <Link
          href="/dashboard"
          className="mt-6 inline-block text-sm font-medium text-zinc-900 underline dark:text-zinc-100"
        >
          Back to dashboard
        </Link>
      </div>
    </main>
  );
}
