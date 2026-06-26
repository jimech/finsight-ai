"use client";

import { useAuth } from "@clerk/nextjs";
import { FormEvent, useState } from "react";

import { uploadTransactionsCsv } from "@/lib/api";

export function TransactionUploadForm() {
  const { getToken } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (!file) {
      setError("Please choose a CSV file to upload.");
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Only .csv files are accepted.");
      return;
    }

    setSubmitting(true);
    try {
      const token = await getToken();
      if (!token) {
        setError("Unable to get authentication token.");
        return;
      }

      const result = await uploadTransactionsCsv(token, file);
      setSuccess(
        `Imported ${result.transactions_imported} transaction${
          result.transactions_imported === 1 ? "" : "s"
        } successfully.`,
      );
      setFile(null);
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="csv-file" className="mb-1 block text-sm font-medium">
          Transaction CSV
        </label>
        <input
          id="csv-file"
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="block w-full text-sm text-zinc-700 file:mr-4 file:rounded-md file:border-0 file:bg-zinc-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-zinc-700 dark:text-zinc-300 dark:file:bg-zinc-100 dark:file:text-zinc-900 dark:hover:file:bg-zinc-300"
        />
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          Required columns: date, description, amount. Optional: merchant,
          category. See the demo format guide below for an example.
        </p>
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {success && (
        <p className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700 dark:border-green-900 dark:bg-green-950 dark:text-green-300">
          {success}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
      >
        {submitting ? "Uploading..." : "Upload transactions"}
      </button>
    </form>
  );
}
