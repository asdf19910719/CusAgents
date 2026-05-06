from app.services.cache_service import CacheService


def test_cache_key_changes_with_template_version():
    service = CacheService()

    first_key = service.build_cache_key(
        step_name="outline",
        normalized_input="topic: revenge",
        model_name="gpt-4.1-mini",
        prompt_version="v1",
        schema_version="v1",
    )
    second_key = service.build_cache_key(
        step_name="outline",
        normalized_input="topic: revenge",
        model_name="gpt-4.1-mini",
        prompt_version="v2",
        schema_version="v1",
    )

    assert first_key != second_key
    assert first_key.startswith("outline:")
