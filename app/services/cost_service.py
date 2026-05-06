from decimal import Decimal

from sqlalchemy import func, select

from app.db.models.job import Job
from app.db.models.step_run import StepRun


class CostService:
    def summarize_job_cost(self, session, job_id):
        statement = select(
            func.coalesce(func.sum(StepRun.input_tokens), 0),
            func.coalesce(func.sum(StepRun.output_tokens), 0),
            func.coalesce(func.sum(StepRun.cost), 0),
        ).where(StepRun.job_id == job_id)
        input_tokens, output_tokens, total_cost = session.execute(statement).one()
        return {
            "job_id": job_id,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_cost": str(total_cost if isinstance(total_cost, Decimal) else Decimal(total_cost)),
        }

    def overall_stats(self, session):
        total_jobs = session.execute(select(func.count()).select_from(Job)).scalar_one()
        total_step_cost = session.execute(select(func.coalesce(func.sum(StepRun.cost), 0))).scalar_one()
        return {
            "total_jobs": total_jobs,
            "total_cost": str(total_step_cost if isinstance(total_step_cost, Decimal) else Decimal(total_step_cost)),
        }
