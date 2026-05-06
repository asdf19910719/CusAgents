from app.providers.image.base import BaseImageProvider, ImageGenerationResult


class ComfyUIImageProvider(BaseImageProvider):
    def __init__(self, client, workflow_builder, backend_name="comfyui_remote"):
        self.client = client
        self.workflow_builder = workflow_builder
        self.backend_name = backend_name

    def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        class PromptItem:
            pass

        prompt_item = PromptItem()
        prompt_item.positive_prompt = positive_prompt
        prompt_item.negative_prompt = negative_prompt
        workflow = self.workflow_builder.build_workflow(prompt_item, style_preset, seed)
        prompt_id = self.client.submit_workflow(workflow)
        history = self.client.get_history(prompt_id)
        image_info = next(iter(history[prompt_id]["outputs"].values()))["images"][0]
        image_bytes = self.client.download_image(
            image_info["filename"],
            image_info["subfolder"],
            image_info["type"],
        )
        file_extension = "." + image_info["filename"].split(".")[-1]
        return ImageGenerationResult(
            provider_name=self.backend_name,
            remote_job_id=prompt_id,
            image_bytes=image_bytes,
            file_name=image_info["filename"].rsplit(".", 1)[0],
            file_extension=file_extension,
            metadata={
                "provider_name": self.backend_name,
                "workflow": workflow,
                "prompt_id": prompt_id,
                "image_info": image_info,
            },
        )
