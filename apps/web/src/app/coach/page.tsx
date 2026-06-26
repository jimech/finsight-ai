import { PageHeader } from "@/components/page-header";
import { CoachChat } from "@/components/coach-chat";

export default function CoachPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-10 sm:py-12">
      <div className="mx-auto w-full max-w-3xl space-y-8">
        <PageHeader
          title="FinSight Coach"
          description="Ask questions grounded in your profile and transaction analytics. Answers cite deterministic data—not invented totals."
        />
        <CoachChat />
      </div>
    </main>
  );
}
