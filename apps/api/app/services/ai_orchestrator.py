import json
import time
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_run import AIRun
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatResponse, Citation
from app.schemas.retrieval import TransactionSearchResult
from app.services.analytics import AnalyticsDateRange
from app.services.finance_tools import (
    get_profile_context_tool,
    get_recurring_expenses_tool,
    get_savings_opportunities_tool,
    get_spending_summary_tool,
)
from app.services.retrieval import (
    embeddings_available_for_user,
    search_user_transactions,
)

GUARDRAIL_INSTRUCTIONS = """
You are FinSight Coach, a helpful personal finance coach.
Deterministic tool outputs are the ONLY source of financial totals and aggregates.
Retrieved transactions are examples/evidence only — never use them to calculate totals.
Use ONLY the deterministic tool data and retrieved transaction snippets provided below.
Do not invent merchants, categories, transactions, or totals.
Cite retrieved transactions when referencing specific spending examples.
If retrieved transactions are missing, still answer from deterministic tools.
If transaction data is missing or limited, say so clearly.
Do not provide investment advice, tax advice, legal advice, or credit repair advice.
Do not guarantee financial outcomes.
Cite which data sources you used in your answer.
Keep advice practical and grounded in the user's actual data.
""".strip()

TOOL_DEFINITIONS = [
    {"source": "profile_context", "label": "User profile"},
    {"source": "spending_summary", "label": "Spending summary"},
    {"source": "recurring_expenses", "label": "Recurring expenses"},
    {"source": "savings_opportunities", "label": "Savings opportunities"},
]

RETRIEVAL_TOP_K = 5


def _run_finance_tools(
    db: Session,
    user_id: UUID,
    date_range: AnalyticsDateRange,
) -> Dict[str, Any]:
    return {
        "profile_context": get_profile_context_tool(db, user_id),
        "spending_summary": get_spending_summary_tool(db, user_id, date_range),
        "recurring_expenses": get_recurring_expenses_tool(db, user_id, date_range),
        "savings_opportunities": get_savings_opportunities_tool(
            db, user_id, date_range
        ),
    }


def _run_transaction_retrieval(
    db: Session,
    user_id: UUID,
    query: str,
) -> Tuple[List[TransactionSearchResult], Literal["available", "unavailable", "empty"]]:
    if not embeddings_available_for_user(db, user_id):
        return [], "unavailable"

    results = search_user_transactions(db, user_id, query, top_k=RETRIEVAL_TOP_K)
    if not results:
        return [], "empty"
    return results, "available"


def _tool_citations() -> List[Citation]:
    return [Citation(**tool) for tool in TOOL_DEFINITIONS]


def _transaction_citation(result: TransactionSearchResult) -> Citation:
    return Citation(
        source=f"transaction:{result.transaction_id}",
        label=result.citation_label,
        transaction_id=result.transaction_id,
        date=result.date,
        description=result.description,
        merchant=result.merchant,
        amount=result.amount,
        category=result.category,
    )


def _retrieval_status_citation(
    status: Literal["available", "unavailable", "empty"],
) -> Optional[Citation]:
    if status == "unavailable":
        return Citation(
            source="transactions/retrieval",
            label="Transaction retrieval unavailable — generate embeddings first",
        )
    if status == "empty":
        return Citation(
            source="transactions/retrieval",
            label="Transaction retrieval returned no matching snippets",
        )
    return None


def _build_citations(
    retrieved: List[TransactionSearchResult],
    retrieval_status: Literal["available", "unavailable", "empty"],
) -> List[Citation]:
    citations = _tool_citations()
    status_citation = _retrieval_status_citation(retrieval_status)
    if status_citation:
        citations.append(status_citation)
    citations.extend(_transaction_citation(result) for result in retrieved)
    return citations


def _build_grounded_prompt(
    user_message: str,
    tool_outputs: Dict[str, Any],
    retrieved: List[TransactionSearchResult],
    retrieval_status: Literal["available", "unavailable", "empty"],
) -> str:
    retrieved_payload = [result.model_dump(mode="json") for result in retrieved]
    context = {
        "deterministic_tools": tool_outputs,
        "retrieved_transactions": retrieved_payload,
        "retrieval_status": retrieval_status,
    }
    context_json = json.dumps(context, indent=2, default=str)
    return (
        f"{GUARDRAIL_INSTRUCTIONS}\n\n"
        f"Grounded context:\n{context_json}\n\n"
        f"User question:\n{user_message}"
    )


def _format_currency(value: float) -> str:
    return f"${value:,.2f}"


def _append_retrieved_transactions(
    lines: List[str],
    retrieved: List[TransactionSearchResult],
    retrieval_status: Literal["available", "unavailable", "empty"],
) -> None:
    if retrieved:
        lines.append("Relevant transaction examples (retrieval evidence only, not totals):")
        for result in retrieved:
            merchant = result.merchant or result.description
            category = result.category or "Uncategorized"
            lines.append(
                f"- {result.citation_label}: {_format_currency(result.amount)} "
                f"({category}) via {merchant}"
            )
        lines.append("")
        return

    if retrieval_status == "unavailable":
        lines.append(
            "Transaction retrieval was unavailable. Generate embeddings to cite specific transactions."
        )
        lines.append("")
    elif retrieval_status == "empty":
        lines.append(
            "Transaction retrieval returned no matching snippets for this question."
        )
        lines.append("")


def _build_fallback_response(
    user_message: str,
    tool_outputs: Dict[str, Any],
    retrieved: List[TransactionSearchResult],
    retrieval_status: Literal["available", "unavailable", "empty"],
) -> str:
    profile = tool_outputs["profile_context"]
    summary = tool_outputs["spending_summary"]
    recurring = tool_outputs["recurring_expenses"]
    savings = tool_outputs["savings_opportunities"]

    lines = [
        "Here is what I found from your FinSight data (deterministic analytics, not estimates I calculated myself):",
        "",
    ]

    transaction_count = summary.get("transaction_count", 0)
    if transaction_count == 0:
        lines.extend(
            [
                "I do not see any imported transactions yet. Upload a CSV on the Transactions page so I can give grounded spending guidance.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"- Spending total: {_format_currency(summary.get('spending_total', 0))}",
                f"- Income total: {_format_currency(summary.get('income_total', 0))}",
                f"- Net cashflow: {_format_currency(summary.get('net_cashflow', 0))}",
                f"- Recurring expenses detected: {summary.get('recurring_expense_count', 0)} "
                f"(estimated total {_format_currency(summary.get('estimated_recurring_total', 0))})",
                "",
            ]
        )

        top_opportunity = summary.get("top_savings_opportunity")
        if top_opportunity:
            lines.append(
                f"- Top savings opportunity: {top_opportunity['category']} — "
                f"current spending {_format_currency(top_opportunity['current_spending'])}, "
                f"potential monthly savings {_format_currency(top_opportunity['potential_monthly_savings'])} "
                f"({top_opportunity['suggested_reduction_percent']}% suggested reduction)."
            )
            lines.append("")

        if recurring.get("items"):
            lines.append("Recurring expenses:")
            for item in recurring["items"][:3]:
                lines.append(
                    f"- {item['merchant_or_description']}: "
                    f"{_format_currency(item['average_amount'])} avg "
                    f"({item['transaction_count']} charges, {item['confidence']} confidence)"
                )
            lines.append("")

        if savings.get("items"):
            lines.append("Savings opportunities:")
            for item in savings["items"][:3]:
                lines.append(
                    f"- {item['category']}: "
                    f"{_format_currency(item['potential_monthly_savings'])} potential monthly savings"
                )
            lines.append("")

    _append_retrieved_transactions(lines, retrieved, retrieval_status)

    if not profile.get("profile_complete"):
        lines.append(
            "Your profile is incomplete. Finish onboarding so coaching can reflect your goals and preferred tone."
        )
        lines.append("")

    lines.extend(
        [
            f"Regarding your question: {user_message}",
            "",
            "I cannot provide investment, tax, legal, or credit repair advice, and I cannot guarantee outcomes. "
            "Financial totals come from deterministic analytics. Retrieved transactions are cited examples only.",
        ]
    )

    return "\n".join(lines)


def _build_tool_calls_payload(
    tool_outputs: Dict[str, Any],
    user_message: str,
    retrieved: List[TransactionSearchResult],
    retrieval_status: Literal["available", "unavailable", "empty"],
) -> List[Dict[str, Any]]:
    calls = [
        {"tool": name, "output": output} for name, output in tool_outputs.items()
    ]
    calls.append(
        {
            "tool": "transaction_retrieval",
            "output": {
                "query": user_message,
                "top_k": RETRIEVAL_TOP_K,
                "status": retrieval_status,
                "result_count": len(retrieved),
                "results": [result.model_dump(mode="json") for result in retrieved],
            },
        }
    )
    return calls


def _call_openai(prompt: str) -> Tuple[str, Optional[int], Optional[str]]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    started = time.perf_counter()
    completion = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": GUARDRAIL_INSTRUCTIONS},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    message = completion.choices[0].message.content or ""
    return message.strip(), latency_ms, settings.openai_model


def process_chat_message(
    db: Session,
    user_id: UUID,
    user_message: str,
    date_range: AnalyticsDateRange,
) -> ChatResponse:
    tool_outputs = _run_finance_tools(db, user_id, date_range)
    retrieved, retrieval_status = _run_transaction_retrieval(
        db,
        user_id,
        user_message,
    )
    citations = _build_citations(retrieved, retrieval_status)
    prompt = _build_grounded_prompt(
        user_message,
        tool_outputs,
        retrieved,
        retrieval_status,
    )

    latency_ms: Optional[int] = None
    model: Optional[str] = None
    if settings.ai_enabled:
        response_text, latency_ms, model = _call_openai(prompt)
    else:
        response_text = _build_fallback_response(
            user_message,
            tool_outputs,
            retrieved,
            retrieval_status,
        )
        model = "deterministic-fallback"

    ai_run = AIRun(
        user_id=user_id,
        prompt=prompt,
        response=response_text,
        model=model,
        latency_ms=latency_ms,
        estimated_cost=None,
        retrieval_count=len(retrieved),
        tool_calls=_build_tool_calls_payload(
            tool_outputs,
            user_message,
            retrieved,
            retrieval_status,
        ),
    )
    db.add(ai_run)
    db.flush()

    citation_payload = [citation.model_dump(mode="json") for citation in citations]
    db.add(
        ChatMessage(
            user_id=user_id,
            role="user",
            content=user_message,
            citations=None,
        )
    )
    db.add(
        ChatMessage(
            user_id=user_id,
            role="assistant",
            content=response_text,
            citations=citation_payload,
        )
    )
    db.commit()
    db.refresh(ai_run)

    return ChatResponse(
        message=response_text,
        citations=citations,
        ai_run_id=ai_run.id,
    )


def get_chat_history(db: Session, user_id: UUID, limit: int = 50) -> List[ChatMessage]:
    query = (
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    return list(db.scalars(query))
