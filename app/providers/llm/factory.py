from app.providers.llm.openai_compatible import OpenAICompatibleProvider


def create_llm_provider(settings):
    return OpenAICompatibleProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        default_model=settings.llm_default_model,
    )
