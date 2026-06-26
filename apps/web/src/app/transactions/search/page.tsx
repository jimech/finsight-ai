import { PageHeader } from "@/components/page-header";
import { TransactionSearchPanel } from "@/components/transaction-search-panel";

export default function TransactionSearchPage() {
  return (
    <main className="flex min-h-full flex-1 flex-col px-6 py-10 sm:py-12">
      <div className="mx-auto w-full max-w-3xl space-y-8">
        <PageHeader
          title="Search transactions"
          description="Generate embeddings for your imports, then search by natural language. Retrieved snippets power AI coach transaction citations."
        />

        <TransactionSearchPanel />
      </div>
    </main>
  );
}
