from app.providers.video.base import BaseVideoProvider, VideoGenerationRequest, VideoGenerationResult


class DreaminaCliVideoProvider(BaseVideoProvider):
    def __init__(
        self,
        client,
        backend_name="dreamina_video_cli",
        duration=5,
        ratio="16:9",
        video_resolution="720p",
        model_version="seedance2.0",
    ):
        self.client = client
        self.backend_name = backend_name
        self.duration = int(duration)
        self.ratio = ratio
        self.video_resolution = video_resolution
        self.model_version = model_version

    def generate_video(self, prompt, duration=None, ratio=None, video_resolution=None, model_version=None):
        if isinstance(prompt, VideoGenerationRequest):
            request = prompt
            resolved_prompt = request.prompt
            resolved_mode = request.mode
            resolved_duration = int(request.duration or duration or self.duration)
            resolved_ratio = request.ratio or ratio or self.ratio
            resolved_video_resolution = request.video_resolution or video_resolution or self.video_resolution
            resolved_model_version = request.model_version or model_version or self.model_version
            image_paths = request.image_paths()
            reference_image_usages = request.reference_image_usages or []
        else:
            resolved_prompt = prompt
            resolved_mode = "text2video"
            resolved_duration = int(duration or self.duration)
            resolved_ratio = ratio or self.ratio
            resolved_video_resolution = video_resolution or self.video_resolution
            resolved_model_version = model_version or self.model_version
            image_paths = []
            reference_image_usages = []
        generated_path, metadata = self.client.generate_video_file(
            prompt=resolved_prompt,
            duration=resolved_duration,
            ratio=resolved_ratio,
            video_resolution=resolved_video_resolution,
            model_version=resolved_model_version,
            mode=resolved_mode,
            image_paths=image_paths,
        )
        submit_id = metadata.get("submit_id")
        return VideoGenerationResult(
            provider_name=self.backend_name,
            remote_job_id=submit_id,
            video_bytes=generated_path.read_bytes(),
            file_name="dreamina-video-cli",
            file_extension=generated_path.suffix or ".mp4",
            metadata={
                "provider_name": self.backend_name,
                "mode": resolved_mode,
                "submit_id": submit_id,
                "gen_status": metadata.get("gen_status"),
                "generated_path": str(generated_path),
                "request_prompt": resolved_prompt,
                "model_version": resolved_model_version,
                "duration": resolved_duration,
                "ratio": resolved_ratio,
                "video_resolution": resolved_video_resolution,
                "reference_images": image_paths,
                "reference_image_usages": reference_image_usages,
                "client_metadata": metadata,
            },
            duration=resolved_duration,
            ratio=resolved_ratio,
            video_resolution=resolved_video_resolution,
        )
