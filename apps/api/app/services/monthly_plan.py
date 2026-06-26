import json
import time
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_run import AIRun
from app.schemas.plan import (
    MonthlyPlanResponse,
    PlanCitation,
    PlanTarget,
    RecommendedCut,
    WeeklyStep,
)
from app.services.analytics import AnalyticsDateRange
from app.services.finance_tools import (
    get_profile_context_tool,
    get_recurring_expenses_tool,
    get_savings_opportunities_tool,
    get_spending_summary_tool,
)

BASE_ASSUMPTIONS = [
    "This plan is based only on uploaded transaction data.",
    "Positive transactions are treated as income.",
    "Negative transactions are treated as expenses.",
]

PLAN_CITATIONS = [
    PlanCitation(label="Spending Summary", source="transactions/summary"),
    PlanCitation(label="Recurring Expenses", source="transactions/recurring"),
    PlanCitation(label="Savings Opportunities", source="transactions/savings-opportunities"),
    PlanCitation(label="User Profile", source="profile"),
]

PLAN_GUARDRAILS = """
You are FinSight Coach creating a monthly action plan.
Use ONLY the provided deterministic plan data and tool outputs.
You may personalize wording in recommended_cuts.reason and weekly_steps.action only.
Do NOT change any numeric values. Do NOT add, remove, or rename categories.
Do NOT invent merchants, income, or savings totals.
Do not provide investment, tax, legal, or credit repair advice.
Do not guarantee financial outcomes.
Return valid JSON matching the exact structure of the provided plan.
""".strip()


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


def _cut_reason(category: str, savings_reason: Optional[str] = None) -> str:
    if savings_reason:
        return savings_reason
    return f"{category} appears flexible based on recent spending."


def _build_recommended_cuts(savings: Dict[str, Any]) -> List[RecommendedCut]:
    cuts: List[RecommendedCut] = []
    for item in savings.get("items", []):
        cuts.append(
            RecommendedCut(
                category=item["category"],
                current_spending=round(float(item["current_spending"]), 2),
                recommended_cut=round(float(item["potential_monthly_savings"]), 2),
                reason=_cut_reason(item["category"], item.get("reason")),
            )
        )
    return cuts


def _build_target(
    profile: Dict[str, Any],
    summary: Dict[str, Any],
    recommended_cuts: List[RecommendedCut],
) -> PlanTarget:
    total_potential = round(
        sum(cut.recommended_cut for cut in recommended_cuts),
        2,
    )
    profile_goal = profile.get("savings_goal")
    if profile_goal is not None:
        monthly_savings_goal = round(float(profile_goal), 2)
    elif total_potential > 0:
        monthly_savings_goal = total_potential
    else:
        monthly_savings_goal = 0.0

    if recommended_cuts:
        current_estimated_savings = round(
            sum(cut.recommended_cut for cut in recommended_cuts[:3]),
            2,
        )
    else:
        current_estimated_savings = round(
            max(0.0, float(summary.get("net_cashflow", 0))),
            2,
        )

    gap = round(max(0.0, monthly_savings_goal - current_estimated_savings), 2)
    return PlanTarget(
        monthly_savings_goal=monthly_savings_goal,
        current_estimated_savings=current_estimated_savings,
        gap=gap,
    )


def _build_weekly_steps(
    recommended_cuts: List[RecommendedCut],
    recurring: Dict[str, Any],
    limited_data: bool,
) -> List[WeeklyStep]:
    if limited_data:
        return [
            WeeklyStep(
                week=1,
                action="Upload your transaction CSV so FinSight can build a data-backed plan.",
            ),
            WeeklyStep(
                week=2,
                action="Complete your profile with income, savings goal, and financial priority.",
            ),
            WeeklyStep(
                week=3,
                action="Review imported categories and merchants for accuracy.",
            ),
            WeeklyStep(
                week=4,
                action="Return here to generate an updated monthly plan once data is available.",
            ),
        ]

    steps: List[WeeklyStep] = []
    for index, cut in enumerate(recommended_cuts[:3], start=1):
        remaining = round(cut.current_spending - cut.recommended_cut, 2)
        steps.append(
            WeeklyStep(
                week=index,
                action=(
                    f"Set a {cut.category} budget of ${remaining:,.2f}, "
                    f"about ${cut.recommended_cut:,.2f} lower than recent spending."
                ),
            )
        )

    recurring_items = recurring.get("items", [])
    if recurring_items and len(steps) < 4:
        top_recurring = recurring_items[0]
        steps.append(
            WeeklyStep(
                week=len(steps) + 1,
                action=(
                    f"Review recurring charge {top_recurring['merchant_or_description']} "
                    f"(${top_recurring['average_amount']:,.2f} avg) for possible savings."
                ),
            )
        )

    while len(steps) < 4:
        steps.append(
            WeeklyStep(
                week=len(steps) + 1,
                action="Track weekly spending against your targets and adjust as needed.",
            )
        )

    return steps[:4]


def _build_assumptions(
    limited_data: bool,
    profile: Dict[str, Any],
) -> List[str]:
    assumptions = list(BASE_ASSUMPTIONS)
    if limited_data:
        assumptions.append(
            "Transaction data is limited or missing, so this plan focuses on setup steps."
        )
    if not profile.get("profile_complete"):
        assumptions.append(
            "Your profile is incomplete, so savings targets may use defaults."
        )
    return assumptions


def build_deterministic_monthly_plan(
    tool_outputs: Dict[str, Any],
) -> Dict[str, Any]:
    profile = tool_outputs["profile_context"]
    summary = tool_outputs["spending_summary"]
    recurring = tool_outputs["recurring_expenses"]
    savings = tool_outputs["savings_opportunities"]

    limited_data = summary.get("transaction_count", 0) == 0
    recommended_cuts = _build_recommended_cuts(savings)
    target = _build_target(profile, summary, recommended_cuts)
    weekly_steps = _build_weekly_steps(recommended_cuts, recurring, limited_data)
    assumptions = _build_assumptions(limited_data, profile)

    return {
        "target": target,
        "recommended_cuts": recommended_cuts,
        "weekly_steps": weekly_steps,
        "assumptions": assumptions,
        "citations": list(PLAN_CITATIONS),
    }


def _numeric_plan_snapshot(plan: Dict[str, Any]) -> Dict[str, Any]:
    target = plan["target"]
    if isinstance(target, PlanTarget):
        target_data = target.model_dump()
    else:
        target_data = target

    cuts = plan["recommended_cuts"]
    return {
        "target": target_data,
        "recommended_cuts": [
            {
                "category": cut.category if isinstance(cut, RecommendedCut) else cut["category"],
                "current_spending": cut.current_spending
                if isinstance(cut, RecommendedCut)
                else cut["current_spending"],
                "recommended_cut": cut.recommended_cut
                if isinstance(cut, RecommendedCut)
                else cut["recommended_cut"],
            }
            for cut in cuts
        ],
    }


def _numbers_match(
    original: Dict[str, Any],
    candidate: MonthlyPlanResponse,
) -> bool:
    return _numeric_plan_snapshot(original) == _numeric_plan_snapshot(
        candidate.model_dump()
    )


def _call_openai_for_plan(
    plan_content: Dict[str, Any],
    tool_outputs: Dict[str, Any],
) -> Tuple[Dict[str, Any], str, int, str]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    plan_json = {
        "target": plan_content["target"].model_dump(),
        "recommended_cuts": [cut.model_dump() for cut in plan_content["recommended_cuts"]],
        "weekly_steps": [step.model_dump() for step in plan_content["weekly_steps"]],
        "assumptions": plan_content["assumptions"],
        "citations": [citation.model_dump() for citation in plan_content["citations"]],
    }
    prompt = (
        f"{PLAN_GUARDRAILS}\n\n"
        f"Tool outputs:\n{json.dumps(tool_outputs, indent=2, default=str)}\n\n"
        f"Deterministic plan (preserve all numbers exactly):\n"
        f"{json.dumps(plan_json, indent=2)}"
    )

    started = time.perf_counter()
    completion = client.chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PLAN_GUARDRAILS},
            {
                "role": "user",
                "content": (
                    "Personalize only the reason and weekly step action text in this plan. "
                    "Return the full plan JSON with identical numeric values.\n\n"
                    f"{json.dumps(plan_json, indent=2)}"
                ),
            },
        ],
        temperature=0.3,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    response_text = completion.choices[0].message.content or "{}"
    parsed = json.loads(response_text)
    parsed["citations"] = plan_json["citations"]
    parsed["assumptions"] = plan_json["assumptions"]
    candidate = MonthlyPlanResponse.model_validate(
        {**parsed, "ai_run_id": "00000000-0000-0000-0000-000000000000"}
    )

    if not _numbers_match(plan_content, candidate):
        return plan_content, prompt, latency_ms, settings.openai_model

    return {
        "target": candidate.target,
        "recommended_cuts": candidate.recommended_cuts,
        "weekly_steps": candidate.weekly_steps,
        "assumptions": candidate.assumptions,
        "citations": candidate.citations,
    }, prompt, latency_ms, settings.openai_model


def generate_monthly_plan(
    db: Session,
    user_id: UUID,
    date_range: AnalyticsDateRange,
) -> MonthlyPlanResponse:
    tool_outputs = _run_finance_tools(db, user_id, date_range)
    plan_content = build_deterministic_monthly_plan(tool_outputs)
    deterministic_copy = deepcopy(plan_content)

    latency_ms: Optional[int] = None
    model: Optional[str] = "deterministic-fallback"
    prompt = json.dumps(
        {
            "tool_outputs": tool_outputs,
            "deterministic_plan": {
                **plan_content,
                "target": plan_content["target"].model_dump(),
                "recommended_cuts": [
                    cut.model_dump() for cut in plan_content["recommended_cuts"]
                ],
                "weekly_steps": [
                    step.model_dump() for step in plan_content["weekly_steps"]
                ],
                "citations": [
                    citation.model_dump() for citation in plan_content["citations"]
                ],
            },
        },
        indent=2,
        default=str,
    )
    response_payload = {
        "target": plan_content["target"].model_dump(),
        "recommended_cuts": [cut.model_dump() for cut in plan_content["recommended_cuts"]],
        "weekly_steps": [step.model_dump() for step in plan_content["weekly_steps"]],
        "assumptions": plan_content["assumptions"],
        "citations": [citation.model_dump() for citation in plan_content["citations"]],
    }
    response_text = json.dumps(response_payload, indent=2, default=str)

    if settings.ai_enabled:
        try:
            personalized, prompt, latency_ms, model = _call_openai_for_plan(
                plan_content,
                tool_outputs,
            )
            plan_content = personalized
            response_payload = {
                "target": plan_content["target"].model_dump()
                if isinstance(plan_content["target"], PlanTarget)
                else plan_content["target"],
                "recommended_cuts": [
                    cut.model_dump() if isinstance(cut, RecommendedCut) else cut
                    for cut in plan_content["recommended_cuts"]
                ],
                "weekly_steps": [
                    step.model_dump() if isinstance(step, WeeklyStep) else step
                    for step in plan_content["weekly_steps"]
                ],
                "assumptions": plan_content["assumptions"],
                "citations": [
                    citation.model_dump()
                    if isinstance(citation, PlanCitation)
                    else citation
                    for citation in plan_content["citations"]
                ],
            }
            response_text = json.dumps(response_payload, indent=2, default=str)
        except Exception:
            plan_content = deterministic_copy
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
    db.commit()
    db.refresh(ai_run)

    return MonthlyPlanResponse(
        target=plan_content["target"],
        recommended_cuts=plan_content["recommended_cuts"],
        weekly_steps=plan_content["weekly_steps"],
        assumptions=plan_content["assumptions"],
        citations=plan_content["citations"],
        ai_run_id=ai_run.id,
    )
