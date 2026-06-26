"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", description: "Overview & insights" },
  {
    href: "/transactions/upload",
    label: "Upload",
    description: "Import CSV data",
  },
  {
    href: "/transactions",
    label: "Transactions",
    description: "View imports",
  },
  { href: "/coach", label: "Coach", description: "Ask FinSight AI" },
  { href: "/plan", label: "Monthly plan", description: "Action plan" },
  {
    href: "/admin/ai-runs",
    label: "AI runs",
    description: "Review outputs",
  },
] as const;

function isActive(pathname: string, href: string) {
  if (href === "/dashboard") {
    return pathname === href;
  }

  return pathname.startsWith(href);
}

export function DashboardNav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="App navigation"
      className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
    >
      {NAV_ITEMS.map((item) => {
        const active = isActive(pathname, item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-xl border p-4 transition-colors ${
              active
                ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                : "border-zinc-200 bg-white hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700 dark:hover:bg-zinc-950"
            }`}
          >
            <p className="text-sm font-semibold">{item.label}</p>
            <p
              className={`mt-1 text-xs ${
                active
                  ? "text-zinc-300 dark:text-zinc-600"
                  : "text-zinc-500 dark:text-zinc-400"
              }`}
            >
              {item.description}
            </p>
          </Link>
        );
      })}
    </nav>
  );
}
