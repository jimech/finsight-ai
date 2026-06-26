"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { type Transaction, getTransactions } from "@/lib/api";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function formatDate(value: string): string {
  return new Date(`${value}T00:00:00`).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function TransactionsList() {
  const { getToken } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTransactions() {
      try {
        const token = await getToken();
        if (!token) {
          setError("Unable to get authentication token.");
          return;
        }

        const response = await getTransactions(token, { limit: 50 });
        setTransactions(response.items);
        setTotal(response.total);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load transactions.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadTransactions();
  }, [getToken]);

  if (loading) {
    return (
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Loading transactions...
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

  if (transactions.length === 0) {
    return (
      <EmptyState
        title="No transactions yet"
        description="Upload a CSV with your spending history to populate this list and unlock dashboard analytics."
        action={{
          href: "/transactions/upload",
          label: "Upload transactions",
        }}
        secondaryAction={{
          href: "/dashboard",
          label: "Back to dashboard",
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Showing {transactions.length} of {total} transactions
      </p>
      <div className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
        <table className="min-w-full divide-y divide-zinc-200 text-sm dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-950">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-zinc-500">
                Date
              </th>
              <th className="px-4 py-3 text-left font-medium text-zinc-500">
                Description
              </th>
              <th className="px-4 py-3 text-left font-medium text-zinc-500">
                Merchant
              </th>
              <th className="px-4 py-3 text-left font-medium text-zinc-500">
                Category
              </th>
              <th className="px-4 py-3 text-right font-medium text-zinc-500">
                Amount
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 bg-white dark:divide-zinc-800 dark:bg-zinc-900">
            {transactions.map((transaction) => (
              <tr key={transaction.id}>
                <td className="px-4 py-3 whitespace-nowrap text-zinc-700 dark:text-zinc-300">
                  {formatDate(transaction.date)}
                </td>
                <td className="px-4 py-3 text-zinc-900 dark:text-zinc-100">
                  {transaction.description}
                </td>
                <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">
                  {transaction.merchant ?? "—"}
                </td>
                <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">
                  {transaction.category ?? "—"}
                </td>
                <td className="px-4 py-3 text-right font-medium whitespace-nowrap text-zinc-900 dark:text-zinc-100">
                  {formatCurrency(transaction.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
