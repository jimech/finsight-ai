"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { FormEvent, useState } from "react";

import {
  type TransactionSearchResult,
  generateTransactionEmbeddings,
  searchTransactions,
} from "@/lib/api";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export function TransactionSearchPanel() {
  const { getToken } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<TransactionSearchResult[]>([]);
  const [embeddingsEnabled, setEmbeddingsEnabled] = useState<boolean | null>(
    null,
  );
  const [searching, setSearching] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generateMessage, setGenerateMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || searching) {
      return;
    }

    setSearching(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) {
        setError("Unable to get authentication token.");
        return;
      }

      const response = await searchTransactions(token, {
        query: trimmed,
        top_k: 5,
      });
      setResults(response.results);
      setEmbeddingsEnabled(response.embeddings_enabled);
      if (response.results.length === 0) {
        setError(
          "No matching transaction snippets found. Generate embeddings first.",
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setSearching(false);
    }
  }

  async function handleGenerateEmbeddings() {
    setGenerating(true);
    setError(null);
    setGenerateMessage(null);
    try {
      const token = await getToken();
      if (!token) {
        setError("Unable to get authentication token.");
        return;
      }

      const response = await generateTransactionEmbeddings(token);
      setGenerateMessage(
        `Generated ${response.generated} embeddings, skipped ${response.skipped}.`,
      );
      setEmbeddingsEnabled(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate embeddings.",
      );
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      {embeddingsEnabled === false && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950">
          <p className="text-sm text-amber-900 dark:text-amber-100">
            Embeddings API is disabled. FinSight uses deterministic fake
            embeddings in this mode so search still works for development and
            tests.
          </p>
        </div>
      )}

      <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
          Generate embeddings
        </h2>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Create searchable vectors for your imported transactions. Safe to run
          multiple times; existing embeddings are skipped.
        </p>
        <button
          type="button"
          onClick={() => void handleGenerateEmbeddings()}
          disabled={generating}
          className="mt-4 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {generating ? "Generating..." : "Generate embeddings"}
        </button>
        {generateMessage && (
          <p className="mt-3 text-sm text-emerald-700 dark:text-emerald-400">
            {generateMessage}
          </p>
        )}
      </div>

      <form
        onSubmit={handleSearch}
        className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950"
      >
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
          Search transactions
        </h2>
        <label htmlFor="transaction-search-query" className="sr-only">
          Search query
        </label>
        <input
          id="transaction-search-query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="coffee spending"
          className="mt-4 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
        />
        <button
          type="submit"
          disabled={searching || !query.trim()}
          className="mt-4 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {searching ? "Searching..." : "Search"}
        </button>
      </form>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {results.length > 0 && (
        <div className="space-y-4">
          {results.map((result) => (
            <article
              key={result.transaction_id}
              className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
            >
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                {result.citation_label}
              </p>
              <p className="mt-2 text-sm text-zinc-900 dark:text-zinc-100">
                {result.description}
                {result.merchant ? ` · ${result.merchant}` : ""}
              </p>
              <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                {result.date} · {result.category ?? "Uncategorized"} ·{" "}
                {formatCurrency(result.amount)}
              </p>
              {result.similarity_score !== null && (
                <p className="mt-1 text-xs text-zinc-500">
                  Similarity: {result.similarity_score}
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
