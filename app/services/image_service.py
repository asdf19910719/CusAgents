from pathlib import Path

from app.db.models.asset import Asset


class ImageGenerationService:
    def __init__(self, providers, default_backend, output_dir):
        self.providers = providers
        self.default_backend = default_backend
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_assets(self, session, job, prompts, style_preset):
        assets = []
        backend = getattr(job, "image_backend", None) or self.default_backend
        provider = self.providers[backend]
        for prompt in prompts:
            seed = 1000 + prompt.shot_index
            try:
                result = provider.generate_image(
                    shot_index=prompt.shot_index,
                    positive_prompt=prompt.positive_prompt,
                    negative_prompt=prompt.negative_prompt,
                    style_preset=style_preset,
                    seed=seed,
                )
                file_path = self.output_dir / (result.file_name + result.file_extension)
                file_path.write_bytes(result.image_bytes)
                asset = Asset(
                    job_id=job.id,
                    shot_index=prompt.shot_index,
                    prompt_text=prompt.positive_prompt,
                    negative_prompt=prompt.negative_prompt,
                    seed=seed,
                    workflow_json=result.metadata,
                    file_path=str(file_path),
                    preview_path=str(file_path),
                    status="completed",
                )
            except Exception as exc:
                workflow_json = {"provider_name": backend}
                error_metadata = getattr(exc, "metadata", None)
                if isinstance(error_metadata, dict):
                    workflow_json.update(error_metadata)
                submit_id = getattr(exc, "submit_id", None)
                if submit_id:
                    workflow_json["submit_id"] = submit_id
                gen_status = getattr(exc, "gen_status", None)
                if gen_status:
                    workflow_json["gen_status"] = gen_status
                asset = Asset(
                    job_id=job.id,
                    shot_index=prompt.shot_index,
                    prompt_text=prompt.positive_prompt,
                    negative_prompt=prompt.negative_prompt,
                    seed=seed,
                    workflow_json=workflow_json,
                    file_path="",
                    preview_path=str(exc),
                    status="failed",
                )
            session.add(asset)
            session.commit()
            session.refresh(asset)
            assets.append(asset)
        return assets
