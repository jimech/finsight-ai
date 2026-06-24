import { Show, SignInButton, SignUpButton } from "@clerk/nextjs";
import Link from "next/link";

import { AuthHeader } from "@/components/auth-header";

export default function Home() {
  return (
    <>
      <AuthHeader />
      <main className="flex flex-1 flex-col items-center justify-center px-6 py-16">
        <div className="max-w-xl text-center">
          <h1 className="text-4xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            FinSight AI
          </h1>
          <p className="mt-4 text-lg text-zinc-600 dark:text-zinc-400">
            Your AI-powered personal finance coach.
          </p>
          <Show when="signed-out">
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <SignInButton mode="modal">
                <button className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-100 dark:hover:bg-zinc-900">
                  Sign in
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300">
                  Get started
                </button>
              </SignUpButton>
            </div>
          </Show>
          <Show when="signed-in">
            <div className="mt-8">
              <Link
                href="/dashboard"
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                Go to dashboard
              </Link>
            </div>
          </Show>
        </div>
      </main>
    </>
  );
}
