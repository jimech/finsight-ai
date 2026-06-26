"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import {
  type ChatHistoryMessage,
  type ChatCitation,
  getChatHistory,
  getSpendingSummary,
  sendChatMessage,
} from "@/lib/api";

function CitationList({ citations }: { citations: ChatCitation[] }) {
  if (citations.length === 0) {
    return null;
  }

  const toolCitations = citations.filter(
    (citation) => !citation.transaction_id,
  );
  const transactionCitations = citations.filter(
    (citation) => citation.transaction_id,
  );

  return (
    <div className="mt-3 space-y-3 border-t border-zinc-200 pt-3 dark:border-zinc-700">
      {toolCitations.length > 0 && (
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Data sources
          </p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {toolCitations.map((citation) => (
              <li
                key={`${citation.source}-${citation.label}`}
                className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
              >
                {citation.label}
              </li>
            ))}
          </ul>
        </div>
      )}

      {transactionCitations.length > 0 && (
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Transaction citations
          </p>
          <ul className="mt-2 space-y-2">
            {transactionCitations.map((citation) => (
              <li
                key={citation.transaction_id}
                className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
              >
                <p className="font-medium text-zinc-900 dark:text-zinc-100">
                  {citation.label}
                </p>
                <p className="mt-1">
                  {citation.description}
                  {citation.merchant ? ` · ${citation.merchant}` : ""}
                </p>
                <p className="mt-1 text-zinc-500 dark:text-zinc-400">
                  {citation.date} · {citation.category ?? "Uncategorized"}
                  {citation.amount !== undefined
                    ? ` · ${new Intl.NumberFormat("en-US", {
                        style: "currency",
                        currency: "USD",
                      }).format(citation.amount)}`
                    : ""}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function CoachChat() {
  const { getToken } = useAuth();
  const [messages, setMessages] = useState<ChatHistoryMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasTransactions, setHasTransactions] = useState<boolean | null>(null);

  useEffect(() => {
    async function loadChat() {
      try {
        const token = await getToken();
        if (!token) {
          setError("Unable to get authentication token.");
          return;
        }

        const [history, summary] = await Promise.all([
          getChatHistory(token),
          getSpendingSummary(token),
        ]);
        setMessages(history.messages);
        setHasTransactions(summary.transaction_count > 0);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load coach chat.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadChat();
  }, [getToken]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || sending) {
      return;
    }

    setSending(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        setError("Unable to get authentication token.");
        return;
      }

      const response = await sendChatMessage(token, { message: trimmed });
      setInput("");
      setMessages((current) => [
        ...current,
        {
          id: `local-user-${Date.now()}`,
          role: "user",
          content: trimmed,
          citations: null,
          created_at: new Date().toISOString(),
        },
        {
          id: response.ai_run_id,
          role: "assistant",
          content: response.message,
          citations: response.citations,
          created_at: new Date().toISOString(),
        },
      ]);
      setHasTransactions(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to send your message.",
      );
    } finally {
      setSending(false);
    }
  }

  if (loading) {
    return (
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Loading coach chat...
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {hasTransactions === false && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950">
          <p className="text-sm text-amber-900 dark:text-amber-100">
            Upload transactions first so FinSight Coach can answer with grounded
            spending data.
          </p>
          <Link
            href="/transactions/upload"
            className="mt-3 inline-block text-sm font-medium text-amber-900 underline dark:text-amber-100"
          >
            Upload transactions CSV
          </Link>
        </div>
      )}

      <div className="rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="max-h-[28rem] space-y-4 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Ask FinSight Coach about saving money, recurring expenses, or
              where to cut back. Answers use your deterministic analytics, not
              invented totals.
            </p>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={
                  message.role === "user"
                    ? "ml-8 rounded-lg bg-zinc-100 p-4 dark:bg-zinc-800"
                    : "mr-8 rounded-lg border border-zinc-200 p-4 dark:border-zinc-700"
                }
              >
                <p className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                  {message.role === "user" ? "You" : "FinSight Coach"}
                </p>
                <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-900 dark:text-zinc-100">
                  {message.content}
                </p>
                {message.role === "assistant" && message.citations && (
                  <CitationList citations={message.citations} />
                )}
              </div>
            ))
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="border-t border-zinc-200 p-4 dark:border-zinc-800"
        >
          <label htmlFor="coach-message" className="sr-only">
            Message
          </label>
          <textarea
            id="coach-message"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            rows={3}
            placeholder="How can I save more money this month?"
            className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
          />
          <div className="mt-3 flex justify-end">
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
            >
              {sending ? "Sending..." : "Send"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
