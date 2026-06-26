import Link from "next/link";

import { DemoCsvGuide } from "@/components/demo-csv-guide";
import { PageHeader } from "@/components/page-header";
import { TransactionUploadForm } from "@/components/transaction-upload-form";

export default function TransactionUploadPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-10 sm:py-12">
      <div className="mx-auto w-full max-w-2xl space-y-8">
        <PageHeader
          title="Upload transactions"
          description="Import a CSV export from your bank or card provider to build your transaction history and unlock analytics."
        />
        <DemoCsvGuide />
        <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
            Choose a file
          </h2>
          <div className="mt-4">
            <TransactionUploadForm />
          </div>
        </section>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          After upload, return to the{" "}
          <Link
            href="/dashboard"
            className="font-medium text-zinc-900 underline dark:text-zinc-100"
          >
            dashboard
          </Link>{" "}
          to review spending insights.
        </p>
      </div>
    </main>
  );
}
