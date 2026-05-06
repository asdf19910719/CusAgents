from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.job import Job
from app.services.idempotency_service import IdempotencyService


def test_idempotency_returns_existing_job_for_same_key():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = IdempotencyService()

    with Session(engine) as session:
        job = Job(
            request_id="req-1",
            topic="冷血剑客复仇",
            style_preset="cinematic",
            target_shot_count=8,
            status="pending",
            idempotency_key="same-key",
            current_step="outline",
        )
        session.add(job)
        session.commit()

        existing = service.find_existing_job(session, "same-key")

        assert existing is not None
        assert existing.id == job.id


def test_idempotency_can_be_bypassed():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = IdempotencyService()

    with Session(engine) as session:
        job = Job(
            request_id="req-1",
            topic="冷血剑客复仇",
            style_preset="cinematic",
            target_shot_count=8,
            status="pending",
            idempotency_key="same-key",
            current_step="outline",
        )
        session.add(job)
        session.commit()

        existing = service.find_existing_job(session, "same-key", skip_idempotency=True)

        assert existing is None
