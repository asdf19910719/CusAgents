from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import load_settings
from app.db.models.llm_cache import LlmCache
from app.db.models.prompt_template import PromptTemplate
from app.services.conversation_service import ConversationService
from app.services.cost_service import CostService
from app.services.runtime_health_service import RuntimeHealthService


router = APIRouter(prefix="/admin", tags=["admin"])


def get_conversation_service():
    settings = load_settings(allow_placeholder_llm_api_key=True)
    return ConversationService(
        idle_timeout_seconds=settings.conversation_idle_timeout_seconds,
        compact_trigger_count=settings.conversation_compact_trigger_count,
        keep_recent_count=settings.conversation_keep_recent_count,
        retention_seconds=settings.conversation_retention_seconds,
        cleanup_batch_size=settings.conversation_cleanup_batch_size,
    )


@router.get("/templates")
def list_templates(db: Session = Depends(get_db)):
    templates = db.execute(select(PromptTemplate).order_by(PromptTemplate.id)).scalars().all()
    return [
        {
            "id": template.id,
            "template_name": template.template_name,
            "template_version": template.template_version,
            "step_name": template.step_name,
            "is_active": template.is_active,
        }
        for template in templates
    ]


@router.post("/cache/clear")
def clear_cache(db: Session = Depends(get_db)):
    deleted = db.query(LlmCache).delete()
    db.commit()
    return {"deleted": deleted}


@router.get("/stats/cost")
def get_cost_stats(db: Session = Depends(get_db)):
    return CostService().overall_stats(db)


@router.get("/runtime/health")
def get_runtime_health(db: Session = Depends(get_db)):
    settings = load_settings(allow_placeholder_llm_api_key=True)
    return RuntimeHealthService(settings).collect(db)


@router.get("/conversations")
def list_conversations(
    limit: int = 20,
    db: Session = Depends(get_db),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    return conversation_service.list_session_overviews(db, limit=limit)


@router.post("/conversations/cleanup")
def cleanup_conversations(
    retention_seconds: int | None = None,
    batch_size: int | None = None,
    db: Session = Depends(get_db),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    return conversation_service.cleanup_sessions(db, retention_seconds=retention_seconds, batch_size=batch_size)
