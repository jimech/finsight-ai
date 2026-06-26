"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import {
  type AIRunItem,
  type EvaluationSubmit,
  evaluateAiRun,
  getAiRuns,
} from "@/lib/api";

function previewText(value: string | null, maxLength = 180): string {
  if (!value) return "—";
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength)}...`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function EvaluationForm({
  run,
  onSaved,
}: {
  run: AIRunItem;
  onSaved: (runId: string, scores: EvaluationSubmit) => void;
}) {
  const { getToken } = useAuth();
  const defaults = run.evaluation ?? run.suggested_scores;
  const [citationScore, setCitationScore] = useState(
    String(defaults?.citation_score ?? 0.8),
  );
  const [calculationScore, setCalculationScore] = useState(
    String(defaults?.calculation_score ?? 0.8),
  );
  const [groundednessScore, setGroundednessScore] = useState(
    String(defaults?.groundedness_score ?? 0.8),
  );
  const [hallucinationFlag, setHallucinationFlag] = useState(
    defaults?.hallucination_flag ?? false,
  );
  const [safetyFlag, setSafetyFlag] = useState(defaults?.safety_flag ?? false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) {
        setError("Unable to get authentication token.");
        return;
      }

      const body: EvaluationSubmit = {
        citation_score: Number(citationScore),
        calculation_score: Number(calculationScore),
        groundedness_score: Number(groundednessScore),
        hallucination_flag: hallucinationFlag,
        safety_flag: safetyFlag,
      };

      await evaluateAiRun(token, run.id, body);
      onSaved(run.id, body);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save evaluation.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-4 rounded-md border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900">
      <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
        Evaluation
      </p>
      {run.evaluation ? (
        <p className="mt-1 text-xs text-emerald-700 dark:text-emerald-400">
          Saved evaluation on file
        </p>
      ) : (
        <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
          Suggested scores pre-filled from deterministic quality hints
        </p>
      )}
      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        <label className="text-sm text-zinc-700 dark:text-zinc-300">
          Citation score
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={citationScore}
            onChange={(event) => setCitationScore(event.target.value)}
            className="mt-1 w-full rounded-md border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </label>
        <label className="text-sm text-zinc-700 dark:text-zinc-300">
          Calculation score
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={calculationScore}
            onChange={(event) => setCalculationScore(event.target.value)}
            className="mt-1 w-full rounded-md border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </label>
        <label className="text-sm text-zinc-700 dark:text-zinc-300">
          Groundedness score
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={groundednessScore}
            onChange={(event) => setGroundednessScore(event.target.value)}
            className="mt-1 w-full rounded-md border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </label>
      </div>
      <div className="mt-3 flex flex-wrap gap-4 text-sm text-zinc-700 dark:text-zinc-300">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={hallucinationFlag}
            onChange={(event) => setHallucinationFlag(event.target.checked)}
          />
          Hallucination flag
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={safetyFlag}
            onChange={(event) => setSafetyFlag(event.target.checked)}
          />
          Safety flag
        </label>
      </div>
      {error && (
        <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
      <button
        type="button"
        onClick={() => void handleSave()}
        disabled={saving}
        className="mt-4 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900"
      >
        {saving ? "Saving..." : "Save evaluation"}
      </button>
    </div>
  );
}

export function AiRunsPanel() {
  const { getToken } = useAuth();
  const [runs, setRuns] = useState<AIRunItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadRuns() {
      try {
        const token = await getToken();
        if (!token) {
          setError("Unable to get authentication token.");
          return;
        }

        const response = await getAiRuns(token, { limit: 50 });
        setRuns(response.items);
        setTotal(response.total);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load AI runs.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadRuns();
  }, [getToken]);

  function handleEvaluationSaved(runId: string, scores: EvaluationSubmit) {
    setRuns((current) =>
      current.map((run) =>
        run.id === runId
          ? {
              ...run,
              evaluation: {
                id: run.evaluation?.id ?? runId,
                citation_score: scores.citation_score,
                calculation_score: scores.calculation_score,
                groundedness_score: scores.groundedness_score,
                hallucination_flag: scores.hallucination_flag,
                safety_flag: scores.safety_flag,
                created_at: new Date().toISOString(),
              },
            }
          : run,
      ),
    );
  }

  if (loading) {
    return (
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Loading AI runs...
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

  if (runs.length === 0) {
    return (
      <EmptyState
        title="No AI runs yet"
        description="Chat with FinSight Coach or generate a monthly plan to create logged AI runs you can review and evaluate here."
        action={{ href: "/coach", label: "Ask FinSight Coach" }}
        secondaryAction={{ href: "/plan", label: "Create monthly plan" }}
      />
    );
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Showing {runs.length} of {total} runs
      </p>
      {runs.map((run) => (
        <article
          key={run.id}
          className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                {run.model ?? "unknown model"}
              </p>
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                {formatDate(run.created_at)}
              </p>
            </div>
            <div className="text-right text-xs text-zinc-500 dark:text-zinc-400">
              <p>Latency: {run.latency_ms ?? "—"} ms</p>
              <p>Retrieval count: {run.retrieval_count ?? 0}</p>
            </div>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Prompt preview
              </p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-zinc-700 dark:text-zinc-300">
                {previewText(run.prompt)}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Response preview
              </p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-zinc-700 dark:text-zinc-300">
                {previewText(run.response)}
              </p>
            </div>
          </div>

          <div className="mt-4">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Tool calls
            </p>
            <pre className="mt-1 overflow-x-auto rounded-md bg-white p-3 text-xs text-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
              {run.tool_calls
                ? JSON.stringify(run.tool_calls, null, 2)
                : "None"}
            </pre>
          </div>

          <EvaluationForm run={run} onSaved={handleEvaluationSaved} />
        </article>
      ))}
    </div>
  );
}
