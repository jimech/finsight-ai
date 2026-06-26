import {
  Show,
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/nextjs";
import Link from "next/link";

const SIGNED_IN_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/transactions/upload", label: "Upload" },
  { href: "/transactions", label: "Transactions" },
  { href: "/coach", label: "Coach" },
  { href: "/plan", label: "Plan" },
] as const;

export function AuthHeader() {
  return (
    <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
        <Link
          href="/"
          className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-50"
        >
          FinSight AI
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <Show when="signed-in">
            <nav className="hidden items-center gap-1 md:flex">
              {SIGNED_IN_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="rounded-md px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-100"
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </Show>
          <Show when="signed-out">
            <SignInButton mode="modal">
              <button className="rounded-md px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-900">
                Sign in
              </button>
            </SignInButton>
            <SignUpButton mode="modal">
              <button className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300">
                Sign up
              </button>
            </SignUpButton>
          </Show>
          <Show when="signed-in">
            <UserButton />
          </Show>
        </div>
      </div>
    </header>
  );
}
