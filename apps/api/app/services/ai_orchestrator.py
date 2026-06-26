import json
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_run import AIRun
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatResponse, Citation
from app.services.analytics import AnalyticsDateRange
from app.services.finance_tools import (
    get_profile_context_tool,
    get_recurring_expenses_tool,
    get_savings_opportunities_tool,
    get_spending_summary_tool,
)

GUARDRAIL_INSTRUCTIONS = """
You are FinSight Coach, a helpful personal finance coach.
Use ONLY the deterministic tool data provided below. Do not invent merchants, categories, transactions, or totals.
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


def _build_citations() -> List[Citation]:
    return [Citation(**tool) for tool in TOOL_DEFINITIONS]


def _build_grounded_prompt(
    user_message: str,
    tool_outputs: Dict[str, Any],
) -> str:
    context_json = json.dumps(tool_outputs, indent=2, default=str)
    return (
        f"{GUARDRAIL_INSTRUCTIONS}\n\n"
        f"Deterministic tool outputs:\n{context_json}\n\n"
        f"User question:\n{user_message}"
    )


def _format_currency(value: float) -> str:
    return f"${value:,.2f}"


def _build_fallback_response(
    user_message: str,
    tool_outputs: Dict[str, Any],
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
            "This response is based only on your profile and imported transaction analytics.",
        ]
    )

    return "\n".join(lines)


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
    citations = _build_citations()
    prompt = _build_grounded_prompt(user_message, tool_outputs)

    latency_ms: Optional[int] = None
    model: Optional[str] = None
    if settings.ai_enabled:
        response_text, latency_ms, model = _call_openai(prompt)
    else:
        response_text = _build_fallback_response(user_message, tool_outputs)
        model = "deterministic-fallback"

    ai_run = AIRun(
        user_id=user_id,
        prompt=prompt,
        response=response_text,
        model=model,
        latency_ms=latency_ms,
        estimated_cost=None,
        retrieval_count=0,
        tool_calls=[
            {"tool": name, "output": output} for name, output in tool_outputs.items()
        ],
    )
    db.add(ai_run)
    db.flush()

    citation_payload = [citation.model_dump() for citation in citations]
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
