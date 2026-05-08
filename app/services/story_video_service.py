import uuid
from pathlib import Path

from sqlalchemy import select

from app.db.models.story_pipeline_run import StoryPipelineRun
from app.db.models.story_project import StoryProject
from app.db.models.story_reference_asset import StoryReferenceAsset
from app.db.models.story_shot import StoryShot
from app.db.models.story_shot_image import StoryShotImage
from app.db.models.story_shot_video_job import StoryShotVideoJob
from app.db.models.video_job import VideoJob
from app.services.story_video_prompt import (
    StoryVideoReferenceImage,
    build_reference_manifest,
    build_story_video_prompt,
    select_video_mode,
)


class StoryVideoService:
    def __init__(self, dispatcher=None, max_reference_images=None):
        self.dispatcher = dispatcher
        self.max_reference_images = max_reference_images

    def create_project(self, session, payload):
        project = StoryProject(
            request_id=str(uuid.uuid4()),
            title=payload.title,
            source_type=payload.source_type,
            source_text=payload.source_text,
            style_prompt=payload.style_prompt,
            status="draft",
            current_stage="draft",
            notification_target_id=payload.notification_target_id,
        )
        session.add(project)
        session.flush()

        for item in payload.reference_assets:
            session.add(
                StoryReferenceAsset(
                    project_id=project.id,
                    asset_type=item.asset_type,
                    name=item.name,
                    description=item.description,
                    prompt=item.prompt,
                    image_asset_id=None,
                    file_path=item.file_path,
                    status="completed",
                    metadata_json=item.metadata_json or {},
                )
            )

        for item in payload.shots:
            shot = StoryShot(
                project_id=project.id,
                shot_index=item.shot_index,
                title=item.title,
                script_text=item.script_text,
                visual_description=item.visual_description,
                camera_motion=item.camera_motion,
                character_names=item.character_names,
                scene_names=item.scene_names,
                prop_names=item.prop_names,
                duration=item.duration,
                ratio=item.ratio,
                status="ready",
                metadata_json=item.metadata_json or {},
            )
            session.add(shot)
            session.flush()
            if item.shot_image_path:
                session.add(
                    StoryShotImage(
                        project_id=project.id,
                        shot_id=shot.id,
                        image_asset_id=None,
                        file_path=item.shot_image_path,
                        image_type="shot",
                        prompt=item.visual_description,
                        status="completed",
                        metadata_json={"source": "input"},
                    )
                )

        session.add(
            StoryPipelineRun(
                project_id=project.id,
                run_type="full_auto",
                status="created",
                checkpoint_json={"current_stage": "draft"},
                error_message=None,
            )
        )
        session.commit()
        session.refresh(project)
        return project

    def submit_next_shot_video(self, session, project_id):
        project = session.get(StoryProject, project_id)
        if project is None:
            raise ValueError("story project not found")
        shot = self._find_next_video_shot(session, project_id)
        if shot is None:
            project.status = "completed"
            project.current_stage = "completed"
            session.commit()
            return None

        reference_images = self._collect_reference_images(project, shot)
        manifest = build_reference_manifest(reference_images, max_images=self.max_reference_images)
        selected_images = [
            StoryVideoReferenceImage(
                item["file_path"],
                item["file_name"],
                item["usage"],
                item["role"],
            )
            for item in manifest["images"]
        ]
        mode = select_video_mode(selected_images, keyframe_sequence=False)
        prompt = build_story_video_prompt(
            shot_index=shot.shot_index,
            script_text=shot.script_text,
            visual_description=shot.visual_description,
            camera_motion=shot.camera_motion,
            reference_images=selected_images,
        )
        video_job = VideoJob(
            request_id=str(uuid.uuid4()),
            topic=project.title,
            prompt=prompt,
            backend="dreamina_video_cli",
            mode=mode,
            status="pending",
            current_step="submit",
            duration=shot.duration,
            ratio=shot.ratio,
            video_resolution="720p",
            model_version="seedance2.0",
            notification_target_id=project.notification_target_id,
            reference_manifest_json=manifest,
        )
        session.add(video_job)
        session.flush()
        story_video_job = StoryShotVideoJob(
            project_id=project.id,
            shot_id=shot.id,
            video_job_id=video_job.id,
            mode=mode,
            submit_id=None,
            status="queued",
            reference_manifest_json=manifest,
            prompt=prompt,
            metadata_json={"dispatch": "pending"},
        )
        shot.status = "video_queued"
        project.status = "generating_videos"
        project.current_stage = "video"
        session.add(story_video_job)
        session.commit()
        session.refresh(story_video_job)
        self._enqueue(video_job.id)
        return story_video_job

    def mark_shot_video_completed_and_continue(self, session, video_job_id):
        story_video_job = session.execute(
            select(StoryShotVideoJob).where(StoryShotVideoJob.video_job_id == video_job_id)
        ).scalars().first()
        if story_video_job is None:
            return None
        story_video_job.status = "completed"
        story_video_job.shot.status = "video_completed"
        session.commit()
        return self.submit_next_shot_video(session, story_video_job.project_id)

    def _find_next_video_shot(self, session, project_id):
        return session.execute(
            select(StoryShot)
            .where(StoryShot.project_id == project_id)
            .where(StoryShot.status.in_(("ready", "image_completed")))
            .order_by(StoryShot.shot_index)
        ).scalars().first()

    def _collect_reference_images(self, project, shot):
        images = []
        for image in shot.images:
            if image.status == "completed" and image.file_path:
                images.append(
                    StoryVideoReferenceImage(
                        file_path=image.file_path,
                        file_name=Path(image.file_path).name,
                        usage="当前分镜图，作为本镜头构图、角色站位、动作起点",
                        role="shot",
                    )
                )
        name_filters = set(shot.character_names + shot.scene_names + shot.prop_names)
        for asset in project.reference_assets:
            if asset.status != "completed" or not asset.file_path:
                continue
            if asset.name not in name_filters:
                continue
            images.append(
                StoryVideoReferenceImage(
                    file_path=asset.file_path,
                    file_name=Path(asset.file_path).name,
                    usage=self._reference_usage(asset),
                    role=self._reference_role(asset.asset_type),
                )
            )
        return images

    def _reference_usage(self, asset):
        if asset.asset_type in ("character", "character_turnaround"):
            return "{0}，保持脸型、发型、服装和体型一致".format(asset.description)
        if asset.asset_type == "scene":
            return "{0}，保持空间结构、光线和材质".format(asset.description)
        if asset.asset_type == "prop":
            return "{0}，保持外观一致".format(asset.description)
        return asset.description

    def _reference_role(self, asset_type):
        if asset_type == "character_turnaround":
            return "character"
        return asset_type

    def _enqueue(self, video_job_id):
        if self.dispatcher is None:
            return None
        return self.dispatcher.enqueue_video_job(video_job_id)
