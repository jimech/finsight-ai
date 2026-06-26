import { UserButton } from "@clerk/nextjs";
import { auth } from "@clerk/nextjs/server";
import Link from "next/link";

import { DashboardNav } from "@/components/dashboard-nav";
import { EmptyState } from "@/components/empty-state";
import { PortfolioNotice } from "@/components/portfolio-notice";
import {
  type RecurringExpensesResponse,
  type SavingsOpportunitiesResponse,
  type SpendingSummary,
  getRecurringExpenses,
  getSavingsOpportunities,
  getSpendingSummary,
  getProfile,
  isProfileComplete,
} from "@/lib/api";

function formatCurrency(value: number | null): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Date(`${value}T00:00:00`).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <p className="text-sm text-zinc-500 dark:text-zinc-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
        {value}
      </p>
    </div>
  );
}

export default async function DashboardPage() {
  const { getToken } = await auth();
  const token = await getToken();

  let profile = null;
  let profileError: string | null = null;
  let summary: SpendingSummary | null = null;
  let summaryError: string | null = null;
  let recurring: RecurringExpensesResponse | null = null;
  let recurringError: string | null = null;
  let savings: SavingsOpportunitiesResponse | null = null;
  let savingsError: string | null = null;

  if (token) {
    try {
      profile = await getProfile(token);
    } catch {
      profileError = "Unable to load your profile.";
    }

    try {
      summary = await getSpendingSummary(token);
    } catch {
      summaryError = "Unable to load spending summary.";
    }

    try {
      recurring = await getRecurringExpenses(token);
    } catch {
      recurringError = "Unable to load recurring expenses.";
    }

    try {
      savings = await getSavingsOpportunities(token);
    } catch {
      savingsError = "Unable to load savings opportunities.";
    }
  }

  const complete = profile ? isProfileComplete(profile) : false;
  const hasTransactions = summary ? summary.transaction_count > 0 : false;

  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-10 sm:py-12">
      <div className="mx-auto w-full max-w-5xl">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
              Command center
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              Dashboard
            </h1>
            <p className="mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
              Upload data, review insights, ask your coach, and build your
              monthly plan.
            </p>
          </div>
          <UserButton />
        </div>

        <div className="mt-8">
          <DashboardNav />
        </div>

        <div className="mt-8">
          <PortfolioNotice compact />
        </div>

        {profileError && (
          <p className="mt-8 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            {profileError}
          </p>
        )}

        {summaryError && (
          <p className="mt-8 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            {summaryError}
          </p>
        )}

        {recurringError && (
          <p className="mt-8 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            {recurringError}
          </p>
        )}

        {savingsError && (
          <p className="mt-8 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            {savingsError}
          </p>
        )}

        {!complete && !profileError && (
          <div className="mt-8">
            <EmptyState
              title="Complete your profile"
              description="Add your financial context so FinSight can personalize coaching, plans, and savings recommendations."
              action={{ href: "/onboarding", label: "Go to onboarding" }}
            />
          </div>
        )}

        {summary && !hasTransactions && (
          <div className="mt-8">
            <EmptyState
              title="No transactions yet"
              description="Upload a CSV with your spending history to unlock dashboard analytics, coach answers, and monthly plans."
              action={{
                href: "/transactions/upload",
                label: "Upload transactions",
              }}
              secondaryAction={{
                href: "/transactions",
                label: "View transactions",
              }}
            />
          </div>
        )}

        {complete && profile && (
          <div className="mt-8 rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
              Your profile
            </h2>
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-zinc-500 dark:text-zinc-400">Name</dt>
                <dd className="font-medium text-zinc-900 dark:text-zinc-100">
                  {profile.name}
                </dd>
              </div>
              <div>
                <dt className="text-zinc-500 dark:text-zinc-400">Email</dt>
                <dd className="font-medium text-zinc-900 dark:text-zinc-100">
                  {profile.email}
                </dd>
              </div>
              <div>
                <dt className="text-zinc-500 dark:text-zinc-400">
                  Monthly income
                </dt>
                <dd className="font-medium text-zinc-900 dark:text-zinc-100">
                  {formatCurrency(profile.monthly_income)}
                </dd>
              </div>
              <div>
                <dt className="text-zinc-500 dark:text-zinc-400">
                  Savings goal
                </dt>
                <dd className="font-medium text-zinc-900 dark:text-zinc-100">
                  {formatCurrency(profile.savings_goal)}
                </dd>
              </div>
            </dl>
            <Link
              href="/onboarding"
              className="mt-4 inline-block text-sm font-medium text-zinc-900 underline dark:text-zinc-100"
            >
              Edit profile
            </Link>
          </div>
        )}

        {summary && hasTransactions && (
          <div className="mt-8 space-y-8">
            <div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
                  Spending summary
                </h2>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  {formatDate(summary.start_date)} – {formatDate(summary.end_date)}
                </p>
              </div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <SummaryCard
                  label="Income"
                  value={formatCurrency(summary.income_total)}
                />
                <SummaryCard
                  label="Spending"
                  value={formatCurrency(summary.spending_total)}
                />
                <SummaryCard
                  label="Net cashflow"
                  value={formatCurrency(summary.net_cashflow)}
                />
                <SummaryCard
                  label="Transactions"
                  value={String(summary.transaction_count)}
                />
              </div>
            </div>

            {summary.largest_expense && (
              <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
                <h3 className="text-base font-medium text-zinc-900 dark:text-zinc-50">
                  Largest expense
                </h3>
                <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                  {summary.largest_expense.description} ·{" "}
                  {summary.largest_expense.merchant} ·{" "}
                  {formatDate(summary.largest_expense.date)}
                </p>
                <p className="mt-2 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                  {formatCurrency(summary.largest_expense.amount)}
                </p>
              </div>
            )}

            <div className="grid gap-8 lg:grid-cols-2">
              <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
                <h3 className="text-base font-medium text-zinc-900 dark:text-zinc-50">
                  Category breakdown
                </h3>
                <div className="mt-4 overflow-hidden rounded-md border border-zinc-200 dark:border-zinc-800">
                  <table className="min-w-full divide-y divide-zinc-200 text-sm dark:divide-zinc-800">
                    <thead className="bg-white dark:bg-zinc-900">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-zinc-500">
                          Category
                        </th>
                        <th className="px-4 py-3 text-right font-medium text-zinc-500">
                          Amount
                        </th>
                        <th className="px-4 py-3 text-right font-medium text-zinc-500">
                          %
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-200 bg-white dark:divide-zinc-800 dark:bg-zinc-900">
                      {summary.category_breakdown.map((item) => (
                        <tr key={item.category}>
                          <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100">
                            {item.category}
                          </td>
                          <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                            {formatCurrency(item.amount)}
                          </td>
                          <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                            {item.percentage_of_spending}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
                <h3 className="text-base font-medium text-zinc-900 dark:text-zinc-50">
                  Top merchants
                </h3>
                <div className="mt-4 overflow-hidden rounded-md border border-zinc-200 dark:border-zinc-800">
                  <table className="min-w-full divide-y divide-zinc-200 text-sm dark:divide-zinc-800">
                    <thead className="bg-white dark:bg-zinc-900">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-zinc-500">
                          Merchant
                        </th>
                        <th className="px-4 py-3 text-right font-medium text-zinc-500">
                          Amount
                        </th>
                        <th className="px-4 py-3 text-right font-medium text-zinc-500">
                          Count
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-200 bg-white dark:divide-zinc-800 dark:bg-zinc-900">
                      {summary.top_merchants.map((item) => (
                        <tr key={item.merchant}>
                          <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100">
                            {item.merchant}
                          </td>
                          <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                            {formatCurrency(item.amount)}
                          </td>
                          <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                            {item.transaction_count}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {summary && hasTransactions && (
          <div className="mt-8 grid gap-8 lg:grid-cols-2">
            <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
              <h3 className="text-base font-medium text-zinc-900 dark:text-zinc-50">
                Recurring expenses
              </h3>
              {recurring && recurring.items.length > 0 ? (
                <div className="mt-4 overflow-hidden rounded-md border border-zinc-200 dark:border-zinc-800">
                  <table className="min-w-full divide-y divide-zinc-200 text-sm dark:divide-zinc-800">
                    <thead className="bg-white dark:bg-zinc-900">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-zinc-500">
                          Merchant
                        </th>
                        <th className="px-4 py-3 text-right font-medium text-zinc-500">
                          Avg
                        </th>
                        <th className="px-4 py-3 text-right font-medium text-zinc-500">
                          Count
                        </th>
                        <th className="px-4 py-3 text-right font-medium text-zinc-500">
                          Confidence
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-200 bg-white dark:divide-zinc-800 dark:bg-zinc-900">
                      {recurring.items.map((item) => (
                        <tr key={item.merchant_or_description}>
                          <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100">
                            <div>{item.merchant_or_description}</div>
                            <div className="text-xs text-zinc-500 dark:text-zinc-400">
                              {item.category}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                            {formatCurrency(item.average_amount)}
                          </td>
                          <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                            {item.transaction_count}
                          </td>
                          <td className="px-4 py-3 text-right capitalize text-zinc-700 dark:text-zinc-300">
                            {item.confidence}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-400">
                  No recurring expenses detected yet. Upload more transactions
                  with similar charges over time.
                </p>
              )}
              {summary.recurring_expense_count > 0 && (
                <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-400">
                  Estimated recurring total:{" "}
                  {formatCurrency(summary.estimated_recurring_total)}
                </p>
              )}
            </div>

            <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
              <h3 className="text-base font-medium text-zinc-900 dark:text-zinc-50">
                Savings opportunities
              </h3>
              {savings && savings.items.length > 0 ? (
                <ul className="mt-4 space-y-4">
                  {savings.items.map((item) => (
                    <li
                      key={item.category}
                      className="rounded-md border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-medium text-zinc-900 dark:text-zinc-100">
                            {item.category}
                          </p>
                          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                            {item.reason}
                          </p>
                        </div>
                        <p className="text-right text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                          {formatCurrency(item.potential_monthly_savings)}
                        </p>
                      </div>
                      <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                        Current spending {formatCurrency(item.current_spending)} ·
                        Suggested reduction {item.suggested_reduction_percent}%
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-400">
                  No savings opportunities found yet. Add more spending
                  transactions to see suggestions.
                </p>
              )}
            </div>
          </div>
        )}

        {hasTransactions && (
          <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
              Quick actions
            </h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Continue exploring your imported data.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                href="/transactions"
                className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-100 dark:hover:bg-zinc-950"
              >
                View transactions
              </Link>
              <Link
                href="/transactions/search"
                className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-100 dark:hover:bg-zinc-950"
              >
                Search transactions
              </Link>
              <Link
                href="/transactions/upload"
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                Upload more data
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
