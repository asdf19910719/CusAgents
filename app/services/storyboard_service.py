import hashlib

from app.db.models.step_run import StepRun
from app.schemas.storyboard import StoryboardShotList


PROMPT_VERSION = "v2"


class StoryboardService:
    def __init__(self, provider, prompt_service, cache_service):
        self.provider = provider
        self.prompt_service = prompt_service
        self.cache_service = cache_service

    def _cache_key(self, job, outline_text, model_name):
        normalized_input = self.cache_service.normalize_input(
            "topic={0}|style={1}|shots={2}|outline={3}".format(
                job.topic, job.style_preset, job.target_shot_count, outline_text
            )
        )
        cache_key = self.cache_service.build_cache_key(
            step_name="storyboard",
            normalized_input=normalized_input,
            model_name=model_name,
            prompt_version=PROMPT_VERSION,
            schema_version="storyboard-v1",
        )
        return normalized_input, cache_key

    def generate_storyboard(self, session, job, outline_text, model_name):
        normalized_input, cache_key = self._cache_key(job, outline_text, model_name)
        cache = self.cache_service.get(session, cache_key)
        if cache is not None:
            parsed = StoryboardShotList.model_validate(cache.response_payload)
            step_run = StepRun(
                job_id=job.id,
                step_name="storyboard",
                attempt_no=1,
                status="completed",
                provider_name="cache",
                model_name=model_name,
                cache_hit=True,
                input_summary=normalized_input,
                output_summary="cache-hit",
                input_tokens=0,
                output_tokens=0,
                cost=0,
                latency_ms=0,
            )
            session.add(step_run)
            session.commit()
            return parsed

        prompt = self.prompt_service.render(
            step_name="storyboard",
            version=PROMPT_VERSION,
            context={
                "topic": job.topic,
                "style_preset": job.style_preset,
                "target_shot_count": job.target_shot_count,
                "outline_text": outline_text,
            },
        )
        try:
            result = self.provider.generate_structured(prompt, StoryboardShotList, model=model_name)
        except Exception as exc:
            step_run = StepRun(
                job_id=job.id,
                step_name="storyboard",
                attempt_no=1,
                status="failed",
                provider_name=self.provider.__class__.__name__,
                model_name=model_name,
                cache_hit=False,
                input_summary=normalized_input,
                output_summary="",
                input_tokens=0,
                output_tokens=0,
                cost=0,
                latency_ms=0,
                error_message=str(exc),
            )
            session.add(step_run)
            session.commit()
            raise

        step_run = StepRun(
            job_id=job.id,
            step_name="storyboard",
            attempt_no=1,
            status="completed",
            provider_name=self.provider.__class__.__name__,
            model_name=model_name,
            cache_hit=False,
            input_summary=normalized_input,
            output_summary="shots={0}".format(len(result.parsed.shots)),
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost=result.cost,
            latency_ms=0,
        )
        session.add(step_run)
        self.cache_service.set(
            session=session,
            cache_key=cache_key,
            step_name="storyboard",
            model_name=model_name,
            prompt_version=PROMPT_VERSION,
            schema_version="storyboard-v1",
            normalized_input_hash=hashlib.sha256(normalized_input.encode("utf-8")).hexdigest(),
            response_payload=result.parsed.model_dump(),
        )
        session.commit()
        return result.parsed
