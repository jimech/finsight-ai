import { UserButton } from "@clerk/nextjs";
import { auth } from "@clerk/nextjs/server";
import Link from "next/link";

export default async function DashboardPage() {
  const { userId } = await auth();

  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-16">
      <div className="mx-auto w-full max-w-2xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              Dashboard
            </h1>
            <p className="mt-2 text-zinc-600 dark:text-zinc-400">
              Your personal finance overview will live here.
            </p>
          </div>
          <UserButton />
        </div>
        <div className="mt-8 rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Signed in as Clerk user{" "}
            <span className="font-mono text-zinc-900 dark:text-zinc-100">
              {userId}
            </span>
          </p>
          <Link
            href="/"
            className="mt-4 inline-block text-sm font-medium text-zinc-900 underline dark:text-zinc-100"
          >
            Back to home
          </Link>
        </div>
      </div>
    </main>
  );
}
