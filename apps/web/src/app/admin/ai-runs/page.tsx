import { PageHeader } from "@/components/page-header";
import { AiRunsPanel } from "@/components/ai-runs-panel";

export default function AdminAiRunsPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-10 sm:py-12">
      <div className="mx-auto w-full max-w-5xl space-y-8">
        <PageHeader
          title="My AI runs"
          description="Review coach and monthly plan AI runs, then record citation, groundedness, and safety evaluations."
        />
        <AiRunsPanel />
      </div>
    </main>
  );
}
