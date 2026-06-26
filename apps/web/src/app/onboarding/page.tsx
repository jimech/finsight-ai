import { OnboardingForm } from "@/components/onboarding-form";
import { PageHeader } from "@/components/page-header";
import { PortfolioNotice } from "@/components/portfolio-notice";

export default function OnboardingPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-10 sm:py-12">
      <div className="mx-auto w-full max-w-xl space-y-8">
        <PageHeader
          title="Set up your profile"
          description="Add your financial context and coaching preferences. This helps personalize plans and coach tone—it does not change deterministic spending calculations."
        />

        <PortfolioNotice compact />

        <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <OnboardingForm />
        </section>
      </div>
    </main>
  );
}
