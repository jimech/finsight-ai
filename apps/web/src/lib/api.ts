const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type CoachingTone = "supportive" | "direct" | "playful";

export type FinancialPriority =
  | "save_money"
  | "reduce_spending"
  | "pay_down_debt"
  | "build_emergency_fund"
  | "understand_spending";

export type Profile = {
  id: string;
  email: string;
  name: string | null;
  monthly_income: number | null;
  savings_goal: number | null;
  current_savings: number | null;
  financial_priority: FinancialPriority | string | null;
  coaching_tone: CoachingTone | string | null;
  created_at: string;
  updated_at: string;
};

export type ProfileUpdate = {
  name?: string;
  monthly_income?: number;
  savings_goal?: number;
  current_savings?: number;
  financial_priority?: FinancialPriority;
  coaching_tone?: CoachingTone;
};

export function isProfileComplete(profile: Profile): boolean {
  return Boolean(
    profile.name &&
      profile.monthly_income !== null &&
      profile.savings_goal !== null &&
      profile.current_savings !== null &&
      profile.financial_priority &&
      profile.coaching_tone,
  );
}

async function apiRequest<T>(
  path: string,
  token: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string | { msg: string }[] };
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        message = body.detail.map((item) => item.msg).join(", ");
      }
    } catch {
      // keep default message
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export function getProfile(token: string): Promise<Profile> {
  return apiRequest<Profile>("/profile", token);
}

export function updateProfile(
  token: string,
  data: ProfileUpdate,
): Promise<Profile> {
  return apiRequest<Profile>("/profile", token, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export type TransactionUploadResult = {
  upload_id: string;
  status: string;
  transactions_imported: number;
};

export type UploadListItem = {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export async function uploadTransactionsCsv(
  token: string,
  file: File,
): Promise<TransactionUploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/uploads/transactions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    let message = `Upload failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (typeof body.detail === "string") {
        message = body.detail;
      }
    } catch {
      // keep default message
    }
    throw new Error(message);
  }

  return response.json() as Promise<TransactionUploadResult>;
}

export function getUploads(token: string): Promise<UploadListItem[]> {
  return apiRequest<UploadListItem[]>("/uploads", token);
}

export type Transaction = {
  id: string;
  date: string;
  description: string;
  merchant: string | null;
  amount: number;
  category: string | null;
  source_file_id: string | null;
  created_at: string;
};

export type TransactionListResponse = {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
};

export type TransactionUpdate = {
  merchant?: string;
  category?: string;
};

export type TransactionQuery = {
  limit?: number;
  offset?: number;
  category?: string;
  merchant?: string;
  start_date?: string;
  end_date?: string;
};

function buildQueryString(
  params: Record<string, string | number | undefined> = {},
): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function getTransactions(
  token: string,
  params: TransactionQuery = {},
): Promise<TransactionListResponse> {
  return apiRequest<TransactionListResponse>(
    `/transactions${buildQueryString(params)}`,
    token,
  );
}

export function updateTransaction(
  token: string,
  transactionId: string,
  data: TransactionUpdate,
): Promise<Transaction> {
  return apiRequest<Transaction>(`/transactions/${transactionId}`, token, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export type CategoryBreakdownItem = {
  category: string;
  amount: number;
  transaction_count: number;
  percentage_of_spending: number;
};

export type TopMerchantItem = {
  merchant: string;
  amount: number;
  transaction_count: number;
};

export type LargestExpense = {
  id: string;
  date: string;
  description: string;
  merchant: string;
  amount: number;
  category: string;
};

export type SavingsOpportunity = {
  category: string;
  current_spending: number;
  suggested_reduction_percent: number;
  potential_monthly_savings: number;
  reason: string;
};

export type RecurringExpense = {
  merchant_or_description: string;
  average_amount: number;
  transaction_count: number;
  first_seen: string;
  last_seen: string;
  confidence: "high" | "medium";
  category: string;
};

export type SpendingSummary = {
  start_date: string | null;
  end_date: string | null;
  transaction_count: number;
  income_total: number;
  spending_total: number;
  net_cashflow: number;
  average_transaction_amount: number;
  largest_expense: LargestExpense | null;
  category_breakdown: CategoryBreakdownItem[];
  top_merchants: TopMerchantItem[];
  uncategorized_count: number;
  recurring_expense_count: number;
  estimated_recurring_total: number;
  top_savings_opportunity: SavingsOpportunity | null;
};

export type RecurringExpensesResponse = {
  start_date: string | null;
  end_date: string | null;
  items: RecurringExpense[];
};

export type SavingsOpportunitiesResponse = {
  start_date: string | null;
  end_date: string | null;
  items: SavingsOpportunity[];
};

export type CategoryBreakdownResponse = {
  start_date: string | null;
  end_date: string | null;
  items: CategoryBreakdownItem[];
};

export type AnalyticsQuery = {
  start_date?: string;
  end_date?: string;
};

export function getSpendingSummary(
  token: string,
  params: AnalyticsQuery = {},
): Promise<SpendingSummary> {
  return apiRequest<SpendingSummary>(
    `/transactions/summary${buildQueryString(params)}`,
    token,
  );
}

export function getCategoryBreakdown(
  token: string,
  params: AnalyticsQuery = {},
): Promise<CategoryBreakdownResponse> {
  return apiRequest<CategoryBreakdownResponse>(
    `/transactions/categories${buildQueryString(params)}`,
    token,
  );
}

export function getRecurringExpenses(
  token: string,
  params: AnalyticsQuery = {},
): Promise<RecurringExpensesResponse> {
  return apiRequest<RecurringExpensesResponse>(
    `/transactions/recurring${buildQueryString(params)}`,
    token,
  );
}

export function getSavingsOpportunities(
  token: string,
  params: AnalyticsQuery = {},
): Promise<SavingsOpportunitiesResponse> {
  return apiRequest<SavingsOpportunitiesResponse>(
    `/transactions/savings-opportunities${buildQueryString(params)}`,
    token,
  );
}

export type ChatCitation = {
  source: string;
  label: string;
  transaction_id?: string;
  date?: string;
  description?: string;
  merchant?: string | null;
  amount?: number;
  category?: string | null;
};

export type ChatResponse = {
  message: string;
  citations: ChatCitation[];
  ai_run_id: string;
};

export type ChatHistoryMessage = {
  id: string;
  role: string;
  content: string;
  citations: ChatCitation[] | null;
  created_at: string;
};

export type ChatHistoryResponse = {
  messages: ChatHistoryMessage[];
};

export type ChatRequest = {
  message: string;
  start_date?: string;
  end_date?: string;
};

export function sendChatMessage(
  token: string,
  body: ChatRequest,
): Promise<ChatResponse> {
  return apiRequest<ChatResponse>("/chat", token, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getChatHistory(token: string): Promise<ChatHistoryResponse> {
  return apiRequest<ChatHistoryResponse>("/chat/history", token);
}

export type PlanTarget = {
  monthly_savings_goal: number;
  current_estimated_savings: number;
  gap: number;
};

export type RecommendedCut = {
  category: string;
  current_spending: number;
  recommended_cut: number;
  reason: string;
};

export type WeeklyStep = {
  week: number;
  action: string;
};

export type PlanCitation = {
  label: string;
  source: string;
};

export type MonthlyPlan = {
  target: PlanTarget;
  recommended_cuts: RecommendedCut[];
  weekly_steps: WeeklyStep[];
  assumptions: string[];
  citations: PlanCitation[];
  ai_run_id: string;
};

export type MonthlyPlanRequest = {
  start_date?: string;
  end_date?: string;
};

export function getMonthlyPlan(
  token: string,
  body: MonthlyPlanRequest = {},
): Promise<MonthlyPlan> {
  return apiRequest<MonthlyPlan>("/plans/monthly", token, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type EvaluationSummary = {
  id: string;
  citation_score: number | null;
  calculation_score: number | null;
  groundedness_score: number | null;
  hallucination_flag: boolean;
  safety_flag: boolean;
  created_at: string;
};

export type SuggestedScores = {
  citation_score: number;
  calculation_score: number;
  groundedness_score: number;
  hallucination_flag: boolean;
  safety_flag: boolean;
};

export type AIRunItem = {
  id: string;
  prompt: string;
  response: string | null;
  model: string | null;
  latency_ms: number | null;
  estimated_cost: number | null;
  retrieval_count: number | null;
  tool_calls: unknown;
  created_at: string;
  evaluation: EvaluationSummary | null;
  suggested_scores: SuggestedScores | null;
};

export type AIRunListResponse = {
  items: AIRunItem[];
  total: number;
  limit: number;
  offset: number;
};

export type EvaluationItem = {
  id: string;
  ai_run_id: string;
  citation_score: number | null;
  calculation_score: number | null;
  groundedness_score: number | null;
  hallucination_flag: boolean;
  safety_flag: boolean;
  created_at: string;
};

export type EvaluationListResponse = {
  items: EvaluationItem[];
  total: number;
};

export type EvaluationSubmit = {
  citation_score: number;
  calculation_score: number;
  groundedness_score: number;
  hallucination_flag: boolean;
  safety_flag: boolean;
};

export type AIRunQuery = {
  limit?: number;
  offset?: number;
};

export function getAiRuns(
  token: string,
  params: AIRunQuery = {},
): Promise<AIRunListResponse> {
  return apiRequest<AIRunListResponse>(
    `/admin/ai-runs${buildQueryString(params)}`,
    token,
  );
}

export function getEvaluations(token: string): Promise<EvaluationListResponse> {
  return apiRequest<EvaluationListResponse>("/admin/evaluations", token);
}

export function evaluateAiRun(
  token: string,
  aiRunId: string,
  body: EvaluationSubmit,
): Promise<EvaluationItem> {
  return apiRequest<EvaluationItem>(`/admin/evaluate/${aiRunId}`, token, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type EmbeddingGenerateResponse = {
  generated: number;
  skipped: number;
};

export type TransactionSearchResult = {
  transaction_id: string;
  date: string;
  description: string;
  merchant: string | null;
  amount: number;
  category: string | null;
  similarity_score: number | null;
  citation_label: string;
};

export type TransactionSearchResponse = {
  query: string;
  results: TransactionSearchResult[];
  embeddings_enabled: boolean;
};

export type TransactionSearchRequest = {
  query: string;
  top_k?: number;
};

export function generateTransactionEmbeddings(
  token: string,
): Promise<EmbeddingGenerateResponse> {
  return apiRequest<EmbeddingGenerateResponse>(
    "/transactions/embeddings/generate",
    token,
    { method: "POST" },
  );
}

export function searchTransactions(
  token: string,
  body: TransactionSearchRequest,
): Promise<TransactionSearchResponse> {
  return apiRequest<TransactionSearchResponse>("/transactions/search", token, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
