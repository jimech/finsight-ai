import Link from "next/link";

import { TransactionUploadForm } from "@/components/transaction-upload-form";

export default function TransactionUploadPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-16">
      <div className="mx-auto w-full max-w-xl">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Upload transactions
        </h1>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Import a CSV export from your bank or card provider to build your
          transaction history.
        </p>
        <div className="mt-8">
          <TransactionUploadForm />
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
