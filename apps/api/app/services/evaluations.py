from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_run import AIRun
from app.models.evaluation import Evaluation
from app.schemas.evaluation import (
    AIRunItem,
    EvaluationItem,
    EvaluationSubmit,
    EvaluationSummary,
    SuggestedScores,
)


def suggest_evaluation_scores(ai_run: AIRun) -> SuggestedScores:
    has_tool_calls = bool(ai_run.tool_calls)
    response_text = (ai_run.response or "").lower()
    has_citation_refs = (
        '"citations"' in response_text
        or "data sources" in response_text
        or "tool outputs" in response_text
        or has_tool_calls
    )

    return SuggestedScores(
        citation_score=0.8 if has_citation_refs else 0.3,
        calculation_score=0.85 if has_tool_calls else 0.5,
        groundedness_score=0.9 if has_tool_calls else 0.4,
        hallucination_flag=not has_tool_calls,
        safety_flag=False,
    )


def _evaluation_map_for_runs(
    db: Session,
    ai_run_ids: List[UUID],
) -> Dict[UUID, Evaluation]:
    if not ai_run_ids:
        return {}
    evaluations = list(
        db.scalars(select(Evaluation).where(Evaluation.ai_run_id.in_(ai_run_ids)))
    )
    return {evaluation.ai_run_id: evaluation for evaluation in evaluations}


def list_user_ai_runs(
    db: Session,
    user_id: UUID,
    limit: int,
    offset: int,
) -> Tuple[List[AIRunItem], int]:
    total = db.scalar(
        select(func.count()).select_from(AIRun).where(AIRun.user_id == user_id)
    ) or 0

    runs = list(
        db.scalars(
            select(AIRun)
            .where(AIRun.user_id == user_id)
            .order_by(AIRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )

    evaluation_by_run = _evaluation_map_for_runs(db, [run.id for run in runs])
    items: List[AIRunItem] = []
    for run in runs:
        evaluation = evaluation_by_run.get(run.id)
        items.append(
            AIRunItem(
                id=run.id,
                prompt=run.prompt,
                response=run.response,
                model=run.model,
                latency_ms=run.latency_ms,
                estimated_cost=float(run.estimated_cost)
                if run.estimated_cost is not None
                else None,
                retrieval_count=run.retrieval_count,
                tool_calls=run.tool_calls,
                created_at=run.created_at,
                evaluation=EvaluationSummary.model_validate(evaluation)
                if evaluation
                else None,
                suggested_scores=suggest_evaluation_scores(run),
            )
        )

    return items, total


def list_user_evaluations(
    db: Session,
    user_id: UUID,
) -> Tuple[List[EvaluationItem], int]:
    query = (
        select(Evaluation)
        .join(AIRun, Evaluation.ai_run_id == AIRun.id)
        .where(AIRun.user_id == user_id)
        .order_by(Evaluation.created_at.desc())
    )
    evaluations = list(db.scalars(query))
    items = [EvaluationItem.model_validate(evaluation) for evaluation in evaluations]
    return items, len(items)


def get_user_ai_run(
    db: Session,
    user_id: UUID,
    ai_run_id: UUID,
) -> Optional[AIRun]:
    return db.scalar(
        select(AIRun).where(AIRun.id == ai_run_id, AIRun.user_id == user_id)
    )


def upsert_evaluation(
    db: Session,
    user_id: UUID,
    ai_run_id: UUID,
    data: EvaluationSubmit,
) -> Optional[Evaluation]:
    ai_run = get_user_ai_run(db, user_id, ai_run_id)
    if ai_run is None:
        return None

    evaluation = db.scalar(
        select(Evaluation).where(Evaluation.ai_run_id == ai_run_id)
    )
    if evaluation is None:
        evaluation = Evaluation(ai_run_id=ai_run_id)
        db.add(evaluation)

    evaluation.citation_score = data.citation_score
    evaluation.calculation_score = data.calculation_score
    evaluation.groundedness_score = data.groundedness_score
    evaluation.hallucination_flag = data.hallucination_flag
    evaluation.safety_flag = data.safety_flag

    db.commit()
    db.refresh(evaluation)
    return evaluation
