import Link from "next/link";

import { OnboardingForm } from "@/components/onboarding-form";

export default function OnboardingPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-16">
      <div className="mx-auto w-full max-w-xl">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Set up your profile
        </h1>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Tell FinSight about your financial goals so your coach can personalize
          guidance.
        </p>
        <div className="mt-8">
          <OnboardingForm />
        </div>
        <Link
          href="/dashboard"
          className="mt-6 inline-block text-sm font-medium text-zinc-900 underline dark:text-zinc-100"
        >
          Back to dashboard
        </Link>
      </div>
    </main>
  );
}
