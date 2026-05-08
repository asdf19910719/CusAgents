def build_video_completion_message(video_job, asset=None, file_path=None, refreshed=False):
    lines = []
    lines.append("视频任务已完成" + ("（刷新恢复）" if refreshed else ""))
    lines.append("video_id={0}".format(getattr(video_job, "id", None)))
    submit_id = getattr(video_job, "submit_id", None)
    if submit_id:
        lines.append("submit_id={0}".format(submit_id))
    if asset is not None:
        lines.append("asset_id={0}".format(getattr(asset, "id", None)))
    if file_path:
        lines.append("file_path={0}".format(file_path))
    if refreshed:
        lines.append("refresh=/videos/{0}/refresh".format(getattr(video_job, "id", None)))
    return "\n".join(lines)


def build_video_failure_message(video_job, fail_reason, refreshed=False):
    lines = []
    lines.append("视频任务失败" + ("（刷新恢复）" if refreshed else ""))
    lines.append("video_id={0}".format(getattr(video_job, "id", None)))
    submit_id = getattr(video_job, "submit_id", None)
    if submit_id:
        lines.append("submit_id={0}".format(submit_id))
    lines.append("fail_reason={0}".format(fail_reason or "unknown"))
    if refreshed:
        lines.append("refresh=/videos/{0}/refresh".format(getattr(video_job, "id", None)))
    return "\n".join(lines)
