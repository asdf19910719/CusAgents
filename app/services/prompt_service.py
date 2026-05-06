from pathlib import Path

from jinja2 import Environment, FileSystemLoader, meta

from app.schemas.prompt import PromptItem


class PromptTemplateService:
    def __init__(self, template_root="app/templates"):
        self.template_root = Path(template_root)
        self.environment = Environment(loader=FileSystemLoader(str(self.template_root)))

    def _template_name(self, step_name, version):
        return step_name + "/" + version + ".j2"

    def _required_fields(self, template_name):
        source, _, _ = self.environment.loader.get_source(self.environment, template_name)
        parsed = self.environment.parse(source)
        return sorted(meta.find_undeclared_variables(parsed))

    def render(self, step_name, version, context):
        template_name = self._template_name(step_name, version)
        required_fields = self._required_fields(template_name)
        missing_fields = [field for field in required_fields if field not in context]
        if missing_fields:
            raise ValueError("Missing template fields: " + ", ".join(missing_fields))
        template = self.environment.get_template(template_name)
        return template.render(**context)


class PromptAssemblyService:
    def __init__(self, template_service):
        self.template_service = template_service

    def build_prompts(self, storyboard, style_preset, version):
        prompts = []
        for shot in storyboard.shots:
            positive_prompt = self.template_service.render(
                step_name="prompt",
                version=version,
                context={
                    "shot_index": shot.shot_index,
                    "style_preset": style_preset,
                    "scene": shot.scene,
                    "subject": shot.subject,
                    "action": shot.action,
                    "camera": shot.camera,
                    "lighting": shot.lighting,
                    "emotion": shot.emotion,
                },
            )
            prompts.append(
                PromptItem(
                    shot_index=shot.shot_index,
                    positive_prompt=positive_prompt,
                    negative_prompt="blurry, low quality, distorted anatomy",
                    style_tags=[style_preset],
                )
            )
        return prompts
