import Link from "next/link";

import { AiRunsPanel } from "@/components/ai-runs-panel";

export default function AdminAiRunsPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-16">
      <div className="mx-auto w-full max-w-5xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              My AI Runs
            </h1>
            <p className="mt-2 text-zinc-600 dark:text-zinc-400">
              Review your coach and plan AI runs, then record quality
              evaluations.
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
          <AiRunsPanel />
        </div>
      </div>
    </main>
  );
}
