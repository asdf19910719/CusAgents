from sqlalchemy import select

from app.db.models.job import Job


class IdempotencyService:
    def find_existing_job(self, session, idempotency_key, skip_idempotency=False):
        if skip_idempotency:
            return None
        statement = select(Job).where(Job.idempotency_key == idempotency_key)
        return session.execute(statement).scalar_one_or_none()
