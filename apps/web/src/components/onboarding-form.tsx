"use client";

import { useAuth } from "@clerk/nextjs";
import { FormEvent, useEffect, useState } from "react";

import {
  type CoachingTone,
  type FinancialPriority,
  type Profile,
  getProfile,
  updateProfile,
} from "@/lib/api";

const FINANCIAL_PRIORITIES: { value: FinancialPriority; label: string }[] = [
  { value: "save_money", label: "Save money" },
  { value: "reduce_spending", label: "Reduce spending" },
  { value: "pay_down_debt", label: "Pay down debt" },
  { value: "build_emergency_fund", label: "Build emergency fund" },
  { value: "understand_spending", label: "Understand spending" },
];

const COACHING_TONES: { value: CoachingTone; label: string }[] = [
  { value: "supportive", label: "Supportive" },
  { value: "direct", label: "Direct" },
  { value: "playful", label: "Playful" },
];

type FormState = {
  name: string;
  monthly_income: string;
  savings_goal: string;
  current_savings: string;
  financial_priority: FinancialPriority | "";
  coaching_tone: CoachingTone | "";
};

const emptyForm: FormState = {
  name: "",
  monthly_income: "",
  savings_goal: "",
  current_savings: "",
  financial_priority: "",
  coaching_tone: "",
};

function profileToForm(profile: Profile): FormState {
  return {
    name: profile.name ?? "",
    monthly_income:
      profile.monthly_income !== null ? String(profile.monthly_income) : "",
    savings_goal:
      profile.savings_goal !== null ? String(profile.savings_goal) : "",
    current_savings:
      profile.current_savings !== null ? String(profile.current_savings) : "",
    financial_priority:
      (profile.financial_priority as FinancialPriority | null) ?? "",
    coaching_tone: (profile.coaching_tone as CoachingTone | null) ?? "",
  };
}

export function OnboardingForm() {
  const { getToken } = useAuth();
  const [form, setForm] = useState<FormState>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    async function loadProfile() {
      try {
        const token = await getToken();
        if (!token) {
          setError("Unable to get authentication token.");
          return;
        }
        const profile = await getProfile(token);
        setForm(profileToForm(profile));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load profile.");
      } finally {
        setLoading(false);
      }
    }

    void loadProfile();
  }, [getToken]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(false);

    const monthlyIncome = Number(form.monthly_income);
    const savingsGoal = Number(form.savings_goal);
    const currentSavings = Number(form.current_savings);

    if (
      [monthlyIncome, savingsGoal, currentSavings].some(
        (value) => Number.isNaN(value) || value < 0,
      )
    ) {
      setError("Money values must be valid non-negative numbers.");
      setSubmitting(false);
      return;
    }

    if (!form.financial_priority || !form.coaching_tone) {
      setError("Please select a financial priority and coaching tone.");
      setSubmitting(false);
      return;
    }

    try {
      const token = await getToken();
      if (!token) {
        setError("Unable to get authentication token.");
        return;
      }

      await updateProfile(token, {
        name: form.name.trim(),
        monthly_income: monthlyIncome,
        savings_goal: savingsGoal,
        current_savings: currentSavings,
        financial_priority: form.financial_priority,
        coaching_tone: form.coaching_tone,
      });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Loading your profile...
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="name" className="mb-1 block text-sm font-medium">
          Name
        </label>
        <input
          id="name"
          type="text"
          required
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        />
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        <div>
          <label
            htmlFor="monthly_income"
            className="mb-1 block text-sm font-medium"
          >
            Monthly income
          </label>
          <input
            id="monthly_income"
            type="number"
            min="0"
            step="0.01"
            required
            value={form.monthly_income}
            onChange={(e) =>
              setForm({ ...form, monthly_income: e.target.value })
            }
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
        <div>
          <label
            htmlFor="savings_goal"
            className="mb-1 block text-sm font-medium"
          >
            Savings goal
          </label>
          <input
            id="savings_goal"
            type="number"
            min="0"
            step="0.01"
            required
            value={form.savings_goal}
            onChange={(e) => setForm({ ...form, savings_goal: e.target.value })}
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
        <div>
          <label
            htmlFor="current_savings"
            className="mb-1 block text-sm font-medium"
          >
            Current savings
          </label>
          <input
            id="current_savings"
            type="number"
            min="0"
            step="0.01"
            required
            value={form.current_savings}
            onChange={(e) =>
              setForm({ ...form, current_savings: e.target.value })
            }
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
      </div>

      <div>
        <label
          htmlFor="financial_priority"
          className="mb-1 block text-sm font-medium"
        >
          Financial priority
        </label>
        <select
          id="financial_priority"
          required
          value={form.financial_priority}
          onChange={(e) =>
            setForm({
              ...form,
              financial_priority: e.target.value as FinancialPriority,
            })
          }
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        >
          <option value="" disabled>
            Select a priority
          </option>
          {FINANCIAL_PRIORITIES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="coaching_tone" className="mb-1 block text-sm font-medium">
          Coaching tone
        </label>
        <select
          id="coaching_tone"
          required
          value={form.coaching_tone}
          onChange={(e) =>
            setForm({
              ...form,
              coaching_tone: e.target.value as CoachingTone,
            })
          }
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        >
          <option value="" disabled>
            Select a tone
          </option>
          {COACHING_TONES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {success && (
        <p className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700 dark:border-green-900 dark:bg-green-950 dark:text-green-300">
          Profile saved successfully.
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
      >
        {submitting ? "Saving..." : "Save profile"}
      </button>
    </form>
  );
}
