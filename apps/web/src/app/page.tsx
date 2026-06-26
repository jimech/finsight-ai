import { Show, SignInButton, SignUpButton } from "@clerk/nextjs";
import Link from "next/link";

import { AuthHeader } from "@/components/auth-header";
import { DemoCsvGuide } from "@/components/demo-csv-guide";

const STEPS = [
  {
    title: "Upload transactions",
    description:
      "Import a CSV from your bank or card provider to build your spending history.",
  },
  {
    title: "See spending insights",
    description:
      "Review category breakdowns, top merchants, recurring expenses, and savings opportunities.",
  },
  {
    title: "Ask FinSight Coach",
    description:
      "Get grounded answers about saving money, recurring charges, and where to cut back.",
  },
  {
    title: "Generate a monthly plan",
    description:
      "Turn your analytics into a structured plan with savings targets and weekly steps.",
  },
  {
    title: "Review AI runs",
    description:
      "Inspect coach and plan outputs, then record quality evaluations for your portfolio.",
  },
] as const;

export default function Home() {
  return (
    <>
      <AuthHeader />
      <main className="flex flex-1 flex-col">
        <section className="border-b border-zinc-200 bg-white px-6 py-16 dark:border-zinc-800 dark:bg-zinc-950">
          <div className="mx-auto max-w-4xl text-center">
            <p className="text-sm font-medium uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
              AI financial coach
            </p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-zinc-900 sm:text-5xl dark:text-zinc-50">
              FinSight AI
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-lg leading-8 text-zinc-600 dark:text-zinc-400">
              A production-style portfolio app that turns transaction data into
              spending insights, grounded AI coaching, and actionable monthly
              plans.
            </p>
            <Show when="signed-out">
              <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                <SignUpButton mode="modal">
                  <button className="rounded-md bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300">
                    Get started free
                  </button>
                </SignUpButton>
                <SignInButton mode="modal">
                  <button className="rounded-md border border-zinc-300 px-5 py-2.5 text-sm font-medium text-zinc-900 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-100 dark:hover:bg-zinc-900">
                    Sign in
                  </button>
                </SignInButton>
              </div>
            </Show>
            <Show when="signed-in">
              <div className="mt-8">
                <Link
                  href="/dashboard"
                  className="inline-block rounded-md bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
                >
                  Open dashboard
                </Link>
              </div>
            </Show>
          </div>
        </section>

        <section className="px-6 py-16">
          <div className="mx-auto max-w-5xl">
            <h2 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              How it works
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600 dark:text-zinc-400">
              FinSight AI connects your transaction data to deterministic
              analytics and an AI coach that cites real numbers—not invented
              totals.
            </p>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {STEPS.map((step, index) => (
                <article
                  key={step.title}
                  className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <span className="inline-flex size-8 items-center justify-center rounded-full bg-zinc-100 text-sm font-semibold text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100">
                    {index + 1}
                  </span>
                  <h3 className="mt-4 text-base font-semibold text-zinc-900 dark:text-zinc-50">
                    {step.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
                    {step.description}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-zinc-200 bg-zinc-50 px-6 py-16 dark:border-zinc-800 dark:bg-zinc-950">
          <div className="mx-auto max-w-3xl">
            <DemoCsvGuide />
          </div>
        </section>
      </main>
    </>
  );
}
