import hashlib

from app.db.models.step_run import StepRun


class OutlineService:
    def __init__(self, provider, prompt_service, cache_service):
        self.provider = provider
        self.prompt_service = prompt_service
        self.cache_service = cache_service

    def _cache_key(self, job, model_name):
        normalized_input = self.cache_service.normalize_input(
            "topic={0}|style={1}|shots={2}".format(
                job.topic, job.style_preset, job.target_shot_count
            )
        )
        cache_key = self.cache_service.build_cache_key(
            step_name="outline",
            normalized_input=normalized_input,
            model_name=model_name,
            prompt_version="v1",
            schema_version="text-v1",
        )
        return normalized_input, cache_key

    def generate_outline(self, session, job, model_name):
        normalized_input, cache_key = self._cache_key(job, model_name)
        cache = self.cache_service.get(session, cache_key)
        if cache is not None:
            step_run = StepRun(
                job_id=job.id,
                step_name="outline",
                attempt_no=1,
                status="completed",
                provider_name="cache",
                model_name=model_name,
                cache_hit=True,
                input_summary=normalized_input,
                output_summary=cache.response_payload["content"],
                input_tokens=0,
                output_tokens=0,
                cost=0,
                latency_ms=0,
            )
            session.add(step_run)
            session.commit()
            return cache.response_payload["content"]

        prompt = self.prompt_service.render(
            step_name="outline",
            version="v1",
            context={
                "topic": job.topic,
                "style_preset": job.style_preset,
                "target_shot_count": job.target_shot_count,
            },
        )
        result = self.provider.generate_text(prompt, model=model_name)
        step_run = StepRun(
            job_id=job.id,
            step_name="outline",
            attempt_no=1,
            status="completed",
            provider_name=self.provider.__class__.__name__,
            model_name=model_name,
            cache_hit=False,
            input_summary=normalized_input,
            output_summary=result.content,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost=result.cost,
            latency_ms=0,
        )
        session.add(step_run)
        self.cache_service.set(
            session=session,
            cache_key=cache_key,
            step_name="outline",
            model_name=model_name,
            prompt_version="v1",
            schema_version="text-v1",
            normalized_input_hash=hashlib.sha256(normalized_input.encode("utf-8")).hexdigest(),
            response_payload={"content": result.content},
        )
        session.commit()
        return result.content
