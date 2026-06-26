"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { type MonthlyPlan, getMonthlyPlan } from "@/lib/api";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export function MonthlyPlanView() {
  const { getToken } = useAuth();
  const [plan, setPlan] = useState<MonthlyPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPlan() {
      try {
        const token = await getToken();
        if (!token) {
          setError("Unable to get authentication token.");
          return;
        }

        const response = await getMonthlyPlan(token);
        setPlan(response);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load monthly plan.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadPlan();
  }, [getToken]);

  if (loading) {
    return (
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Building your monthly plan...
      </p>
    );
  }

  if (error) {
    return (
      <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
        {error}
      </p>
    );
  }

  if (!plan) {
    return null;
  }

  const limitedData = plan.recommended_cuts.length === 0;

  return (
    <div className="space-y-8">
      {limitedData && (
        <EmptyState
          title="Limited plan data"
          description="Upload more transactions and complete your profile so FinSight can recommend category cuts and savings targets from your actual spending."
          action={{
            href: "/transactions/upload",
            label: "Upload transactions",
          }}
          secondaryAction={{
            href: "/onboarding",
            label: "Complete profile",
          }}
        />
      )}

      <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
          Savings target
        </h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Monthly goal</p>
            <p className="mt-1 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
              {formatCurrency(plan.target.monthly_savings_goal)}
            </p>
          </div>
          <div>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Estimated from cuts
            </p>
            <p className="mt-1 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
              {formatCurrency(plan.target.current_estimated_savings)}
            </p>
          </div>
          <div>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Gap</p>
            <p className="mt-1 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
              {formatCurrency(plan.target.gap)}
            </p>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
          Recommended cuts
        </h2>
        {plan.recommended_cuts.length > 0 ? (
          <div className="mt-4 overflow-hidden rounded-md border border-zinc-200 dark:border-zinc-800">
            <table className="min-w-full divide-y divide-zinc-200 text-sm dark:divide-zinc-800">
              <thead className="bg-white dark:bg-zinc-900">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-zinc-500">
                    Category
                  </th>
                  <th className="px-4 py-3 text-right font-medium text-zinc-500">
                    Current
                  </th>
                  <th className="px-4 py-3 text-right font-medium text-zinc-500">
                    Cut
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 bg-white dark:divide-zinc-800 dark:bg-zinc-900">
                {plan.recommended_cuts.map((cut) => (
                  <tr key={cut.category}>
                    <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100">
                      <div>{cut.category}</div>
                      <div className="text-xs text-zinc-500 dark:text-zinc-400">
                        {cut.reason}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                      {formatCurrency(cut.current_spending)}
                    </td>
                    <td className="px-4 py-3 text-right text-emerald-700 dark:text-emerald-400">
                      {formatCurrency(cut.recommended_cut)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-400">
            No spending cuts recommended yet. Add transactions to generate
            category-based recommendations.
          </p>
        )}
      </section>

      <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
          Weekly steps
        </h2>
        <ol className="mt-4 space-y-3">
          {plan.weekly_steps.map((step) => (
            <li
              key={step.week}
              className="rounded-md border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
            >
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Week {step.week}
              </p>
              <p className="mt-1 text-sm text-zinc-900 dark:text-zinc-100">
                {step.action}
              </p>
            </li>
          ))}
        </ol>
      </section>

      <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
          Assumptions
        </h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-zinc-700 dark:text-zinc-300">
          {plan.assumptions.map((assumption) => (
            <li key={assumption}>{assumption}</li>
          ))}
        </ul>
      </section>

      <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
          Data sources
        </h2>
        <ul className="mt-4 flex flex-wrap gap-2">
          {plan.citations.map((citation) => (
            <li
              key={citation.source}
              className="rounded-full bg-zinc-100 px-3 py-1 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
            >
              {citation.label}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
