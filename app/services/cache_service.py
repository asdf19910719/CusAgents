import hashlib

from app.db.models.llm_cache import LlmCache


class CacheService:
    def normalize_input(self, value):
        return " ".join(value.strip().split())

    def build_cache_key(self, step_name, normalized_input, model_name, prompt_version, schema_version):
        digest_source = "|".join(
            [normalized_input, model_name, prompt_version, schema_version]
        )
        digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()
        return step_name + ":" + digest

    def get(self, session, cache_key):
        return session.get(LlmCache, cache_key)

    def set(
        self,
        session,
        cache_key,
        step_name,
        model_name,
        prompt_version,
        schema_version,
        normalized_input_hash,
        response_payload,
    ):
        cache = LlmCache(
            cache_key=cache_key,
            step_name=step_name,
            model_name=model_name,
            prompt_version=prompt_version,
            schema_version=schema_version,
            normalized_input_hash=normalized_input_hash,
            response_payload=response_payload,
        )
        cache = session.merge(cache)
        session.flush()
        return cache
