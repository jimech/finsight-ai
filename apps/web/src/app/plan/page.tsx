import Link from "next/link";

import { MonthlyPlanView } from "@/components/monthly-plan-view";

export default function PlanPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-16">
      <div className="mx-auto w-full max-w-3xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              Monthly action plan
            </h1>
            <p className="mt-2 text-zinc-600 dark:text-zinc-400">
              A structured plan built from your profile and transaction
              analytics.
            </p>
          </div>
          <Link
            href="/dashboard"
            className="text-sm font-medium text-zinc-900 underline dark:text-zinc-100"
          >
            Back to dashboard
          </Link>
        </div>

        <div className="mt-8">
          <MonthlyPlanView />
        </div>
      </div>
    </main>
  );
}
