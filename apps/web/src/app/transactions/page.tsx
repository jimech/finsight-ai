import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { TransactionsList } from "@/components/transactions-list";

export default function TransactionsPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-10 sm:py-12">
      <div className="mx-auto w-full max-w-5xl space-y-8">
        <PageHeader
          title="Transactions"
          description="Browse your recently imported transactions and confirm your data looks correct before using coach and plan features."
          action={
            <Link
              href="/transactions/upload"
              className="inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
            >
              Upload CSV
            </Link>
          }
        />
        <TransactionsList />
      </div>
    </main>
  );
}
