from app.providers.image.comfyui_provider import ComfyUIImageProvider
from app.providers.image.comfyui_client import ComfyUIClient
from app.providers.image.codex_cli_provider import CodexCliClient, CodexCliImageProvider
from app.providers.image.third_party_client import ThirdPartyImageClient
from app.providers.image.third_party_provider import ThirdPartyImageProvider
from app.providers.image.workflow_builder import WorkflowBuilder
from app.providers.llm.factory import create_llm_provider
from app.services.cache_service import CacheService
from app.services.image_service import ImageGenerationService
from app.services.notification_service import FeishuAppMessageNotifier, FeishuWebhookNotifier, NotificationService
from app.services.orchestration_service import OrchestrationService
from app.services.outline_service import OutlineService
from app.services.prompt_service import PromptAssemblyService, PromptTemplateService
from app.services.quality_service import QualityService
from app.services.storyboard_service import StoryboardService


def build_image_providers(settings):
    providers = {
        "comfyui_remote": ComfyUIImageProvider(
            client=ComfyUIClient(base_url=settings.comfyui_base_url),
            workflow_builder=WorkflowBuilder(),
            backend_name="comfyui_remote",
        ),
        "codex_cli": CodexCliImageProvider(
            client=CodexCliClient(
                command_name=settings.codex_cli_command,
                model_name=settings.codex_cli_model,
                timeout_seconds=settings.codex_cli_timeout_seconds,
            ),
            backend_name="codex_cli",
        ),
    }
    if settings.third_party_image_base_url:
        providers["third_party"] = ThirdPartyImageProvider(
            client=ThirdPartyImageClient(
                base_url=settings.third_party_image_base_url,
                api_key=settings.third_party_image_api_key,
                model_name=settings.third_party_image_model,
                api_path=settings.third_party_image_api_path,
                timeout_seconds=settings.third_party_image_timeout_seconds,
                retry_attempts=settings.third_party_image_retry_attempts,
            ),
            backend_name="third_party",
        )
    else:
        providers["third_party"] = ThirdPartyImageProvider(
            client=ThirdPartyImageClient(
                base_url="https://placeholder.invalid",
                api_key="placeholder",
                model_name="placeholder-model",
                api_path=settings.third_party_image_api_path,
                timeout_seconds=settings.third_party_image_timeout_seconds,
                retry_attempts=settings.third_party_image_retry_attempts,
            ),
            backend_name="third_party",
        )
    return providers


def build_notification_service(settings):
    notifier = None
    if settings.feishu_app_id and settings.feishu_app_secret:
        notifier = FeishuAppMessageNotifier(
            app_id=settings.feishu_app_id,
            app_secret=settings.feishu_app_secret,
            open_base_url=settings.feishu_open_base_url,
        )
    elif settings.feishu_notify_webhook_url:
        notifier = FeishuWebhookNotifier(webhook_url=settings.feishu_notify_webhook_url)
    return NotificationService(notifier=notifier)


def build_orchestration_service(settings):
    llm_provider = create_llm_provider(settings)
    prompt_service = PromptTemplateService(template_root="app/templates")
    cache_service = CacheService()
    outline_service = OutlineService(llm_provider, prompt_service, cache_service)
    storyboard_service = StoryboardService(llm_provider, prompt_service, cache_service)
    prompt_assembly_service = PromptAssemblyService(prompt_service)
    notification_service = build_notification_service(settings)
    image_service = ImageGenerationService(
        providers=build_image_providers(settings),
        default_backend=settings.image_backend,
        output_dir=settings.output_dir,
    )
    quality_service = QualityService()
    return OrchestrationService(
        outline_service=outline_service,
        storyboard_service=storyboard_service,
        prompt_service=prompt_assembly_service,
        image_service=image_service,
        quality_service=quality_service,
        notification_service=notification_service,
    )
