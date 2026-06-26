import { PageHeader } from "@/components/page-header";
import { MonthlyPlanView } from "@/components/monthly-plan-view";

export default function PlanPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-10 sm:py-12">
      <div className="mx-auto w-full max-w-3xl space-y-8">
        <PageHeader
          title="Monthly action plan"
          description="A structured plan built from your profile and transaction analytics, with savings targets, recommended cuts, and weekly steps."
        />
        <MonthlyPlanView />
      </div>
    </main>
  );
}
