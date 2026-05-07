import hashlib
import hmac
import html
import time
import uuid
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes.jobs import get_job_dispatcher, get_notification_service, safe_enqueue
from app.core.config import load_settings
from app.core.enums import JobStatus
from app.db.models.asset import Asset
from app.db.models.job import Job
from app.db.models.review import Review


router = APIRouter(prefix="/mobile", tags=["mobile"])
MOBILE_SESSION_COOKIE = "mobile_session"


def _page(title: str, body: str) -> HTMLResponse:
    document = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{0}</title>
  <style>
    :root {{
      color-scheme: light;
      --card: #fffdfa;
      --text: #1f1a17;
      --muted: #74665d;
      --line: #dfd1c0;
      --accent: #8d4f2d;
      --accent-soft: #f0dfcf;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", sans-serif;
      background: linear-gradient(180deg, #f8f3eb 0%, #efe3d3 100%);
      color: var(--text);
    }}
    main {{
      max-width: 760px;
      margin: 0 auto;
      padding: 16px 14px 40px;
    }}
    h1, h2, h3, p {{ margin-top: 0; }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      margin-bottom: 14px;
      box-shadow: 0 10px 30px rgba(91, 59, 33, 0.08);
    }}
    .meta {{
      color: var(--muted);
      font-size: 14px;
    }}
    .row {{
      display: grid;
      gap: 10px;
      margin-bottom: 10px;
    }}
    label {{
      display: block;
      font-size: 14px;
      margin-bottom: 4px;
      color: var(--muted);
    }}
    input, select, button {{
      width: 100%;
      border-radius: 12px;
      border: 1px solid var(--line);
      padding: 12px;
      font-size: 16px;
      background: #fff;
    }}
    button {{
      background: var(--accent);
      color: #fff;
      border: none;
      font-weight: 600;
    }}
    .secondary {{
      background: var(--accent-soft);
      color: var(--accent);
    }}
    .pill {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 13px;
      margin-right: 6px;
      margin-bottom: 6px;
    }}
    .job-link {{
      display: block;
      color: inherit;
      text-decoration: none;
    }}
    .job-link strong {{
      display: block;
      margin-bottom: 6px;
      font-size: 17px;
    }}
    .actions {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }}
    .actions form {{
      margin: 0;
    }}
    ul {{
      padding-left: 18px;
      margin-bottom: 0;
    }}
    img.preview {{
      width: 100%;
      margin-top: 10px;
      border-radius: 12px;
      border: 1px solid var(--line);
      display: block;
      background: #fff;
    }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }}
    .topbar form {{
      margin: 0;
      width: 132px;
    }}
  </style>
</head>
<body>
  <main>{1}</main>
</body>
</html>""".format(html.escape(title), body)
    return HTMLResponse(document)


def _parse_form_body(raw_body: bytes) -> dict:
    return parse_qs(raw_body.decode("utf-8"))


def _job_summary(job: Job) -> str:
    return """
<a class="job-link" href="/mobile/jobs/{0}">
  <strong>{1}</strong>
  <span class="pill">{2}</span>
  <span class="pill">{3}</span>
  <div class="meta">#{0} · style={4} · backend={5}</div>
</a>""".format(
        job.id,
        html.escape(job.topic),
        html.escape(str(job.status)),
        html.escape(job.current_step),
        html.escape(job.style_preset),
        html.escape(job.image_backend),
    )


def _build_mobile_session_value(access_token: str, expires_at: int) -> str:
    signature = hmac.new(
        access_token.encode("utf-8"),
        str(expires_at).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return "{0}.{1}".format(expires_at, signature)


def _has_valid_mobile_session(request: Request, access_token: str) -> bool:
    cookie_value = request.cookies.get(MOBILE_SESSION_COOKIE, "").strip()
    if not cookie_value:
        return False
    try:
        expires_text, signature = cookie_value.split(".", 1)
        expires_at = int(expires_text)
    except ValueError:
        return False
    if expires_at <= int(time.time()):
        return False
    expected_value = _build_mobile_session_value(access_token, expires_at)
    return hmac.compare_digest("{0}.{1}".format(expires_at, signature), expected_value)


def _mobile_settings():
    return load_settings(allow_placeholder_llm_api_key=True)


def _mobile_auth_redirect(request: Request):
    settings = _mobile_settings()
    access_token = (settings.mobile_access_token or "").strip()
    if not access_token:
        return None
    if _has_valid_mobile_session(request, access_token):
        return None
    return RedirectResponse(url="/mobile/login", status_code=303)


def _logout_form() -> str:
    settings = _mobile_settings()
    if not (settings.mobile_access_token or "").strip():
        return ""
    return """
<form method="post" action="/mobile/logout">
  <button type="submit" class="secondary">退出登录</button>
</form>"""


def _render_asset_preview(asset: Asset) -> str:
    preview_url = "/mobile/assets/{0}/preview".format(asset.id)
    file_name = html.escape(Path(asset.file_path).name)
    return """
<li>
  <strong>镜头 {0}</strong> · {1}<br>
  <a href="{2}" target="_blank">预览图片</a><br>
  <span class="meta">{3}</span>
  <img class="preview" src="{2}" alt="asset-{0}">
</li>""".format(
        asset.shot_index,
        html.escape(asset.status),
        preview_url,
        file_name,
    )


@router.get("", response_class=HTMLResponse)
@router.get("/jobs", response_class=HTMLResponse)
def mobile_jobs_page(request: Request, db: Session = Depends(get_db)):
    redirect = _mobile_auth_redirect(request)
    if redirect is not None:
        return redirect

    jobs = db.execute(select(Job).order_by(Job.id.desc()).limit(20)).scalars().all()
    if jobs:
        jobs_html = "".join('<div class="card">{0}</div>'.format(_job_summary(job)) for job in jobs)
    else:
        jobs_html = '<div class="card"><p class="meta">当前还没有任务。</p></div>'

    body = """
<section class="card">
  <div class="topbar">
    <div>
      <h1>移动控制台</h1>
      <p class="meta">用于手机端快速创建任务、查看状态和触发审核动作。</p>
    </div>
    {1}
  </div>
</section>
<section class="card">
  <h2>创建任务</h2>
  <form method="post" action="/mobile/jobs">
    <div class="row">
      <div>
        <label for="topic">题材或主题</label>
        <input id="topic" name="topic" placeholder="例如：赛博武侠" required>
      </div>
      <div>
        <label for="style_preset">风格</label>
        <input id="style_preset" name="style_preset" value="cinematic" required>
      </div>
      <div>
        <label for="target_shot_count">镜头数量</label>
        <input id="target_shot_count" name="target_shot_count" type="number" min="1" value="4" required>
      </div>
      <div>
        <label for="image_backend">出图后端</label>
        <select id="image_backend" name="image_backend">
          <option value="third_party">third_party</option>
          <option value="comfyui_remote">comfyui_remote</option>
          <option value="codex_cli">codex_cli</option>
        </select>
      </div>
    </div>
    <button type="submit">创建任务</button>
  </form>
</section>
<section>
  <h2>最近任务</h2>
  {0}
</section>""".format(jobs_html, _logout_form())
    return _page("移动控制台", body)


@router.get("/login", response_class=HTMLResponse)
def mobile_login_page():
    body = """
<section class="card">
  <h1>手机控制登录</h1>
  <p class="meta">当前移动控制页已启用单用户访问令牌，请先登录。</p>
</section>
<section class="card">
  <h2>登录</h2>
  <form method="post" action="/mobile/login">
    <div class="row">
      <div>
        <label for="access_token">访问令牌</label>
        <input id="access_token" name="access_token" type="password" required>
      </div>
    </div>
    <button type="submit">登录</button>
  </form>
</section>"""
    return _page("手机控制登录", body)


@router.post("/login")
async def mobile_login(request: Request):
    settings = _mobile_settings()
    configured_token = (settings.mobile_access_token or "").strip()
    if not configured_token:
        return RedirectResponse(url="/mobile/jobs", status_code=303)

    payload = _parse_form_body(await request.body())
    submitted_token = payload.get("access_token", [""])[0].strip()
    if not submitted_token or not hmac.compare_digest(submitted_token, configured_token):
        raise HTTPException(status_code=403, detail="invalid mobile access token")

    expires_at = int(time.time()) + settings.mobile_session_max_age_seconds
    response = RedirectResponse(url="/mobile/jobs", status_code=303)
    response.set_cookie(
        MOBILE_SESSION_COOKIE,
        _build_mobile_session_value(configured_token, expires_at),
        max_age=settings.mobile_session_max_age_seconds,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/logout")
async def mobile_logout():
    response = RedirectResponse(url="/mobile/login", status_code=303)
    response.delete_cookie(MOBILE_SESSION_COOKIE)
    return response


@router.post("/jobs")
async def create_mobile_job(
    request: Request,
    db: Session = Depends(get_db),
    dispatcher=Depends(get_job_dispatcher),
    notification_service=Depends(get_notification_service),
):
    redirect = _mobile_auth_redirect(request)
    if redirect is not None:
        return redirect

    payload = _parse_form_body(await request.body())
    topic = payload.get("topic", [""])[0].strip()
    style_preset = payload.get("style_preset", [""])[0].strip()
    image_backend = payload.get("image_backend", ["third_party"])[0].strip()
    target_shot_count_raw = payload.get("target_shot_count", ["0"])[0].strip()
    if not topic or not style_preset:
        raise HTTPException(status_code=422, detail="topic and style_preset are required")
    try:
        target_shot_count = int(target_shot_count_raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="target_shot_count must be an integer") from exc
    if image_backend not in ("comfyui_remote", "third_party", "codex_cli"):
        raise HTTPException(status_code=422, detail="invalid image backend")
    if target_shot_count < 1:
        raise HTTPException(status_code=422, detail="target_shot_count must be positive")

    job = Job(
        request_id=str(uuid.uuid4()),
        topic=topic,
        style_preset=style_preset,
        target_shot_count=target_shot_count,
        image_backend=image_backend,
        status=JobStatus.PENDING,
        idempotency_key=str(uuid.uuid4()),
        current_step="outline",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    notification_service.notify_job_event(
        db,
        job,
        event_type="job_created",
        message="移动端创建任务，job_id={0}".format(job.id),
    )
    safe_enqueue(dispatcher, job.id)
    return RedirectResponse(url="/mobile/jobs/{0}".format(job.id), status_code=303)


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
def mobile_job_detail(job_id: int, request: Request, db: Session = Depends(get_db)):
    redirect = _mobile_auth_redirect(request)
    if redirect is not None:
        return redirect

    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")

    assets = db.execute(select(Asset).where(Asset.job_id == job_id).order_by(Asset.shot_index)).scalars().all()
    if assets:
        assets_html = "".join(_render_asset_preview(asset) for asset in assets)
        assets_section = "<ul>{0}</ul>".format(assets_html)
    else:
        assets_section = '<p class="meta">当前还没有生成素材。</p>'

    error_html = ""
    if job.error_message:
        error_html = '<div class="card"><h3>错误信息</h3><p>{0}</p></div>'.format(html.escape(job.error_message))

    body = """
<section class="card">
  <div class="topbar">
    <div>
      <h1>{0}</h1>
      <div class="pill">{1}</div>
      <div class="pill">{2}</div>
      <div class="meta">job_id={3} · style={4} · 镜头={5} · backend={6}</div>
    </div>
    {9}
  </div>
</section>
<section class="card">
  <h2>任务动作</h2>
  <div class="actions">
    <form method="post" action="/mobile/jobs/{3}/action">
      <input type="hidden" name="action" value="approve">
      <button type="submit">通过</button>
    </form>
    <form method="post" action="/mobile/jobs/{3}/action">
      <input type="hidden" name="action" value="retry">
      <button type="submit" class="secondary">重试</button>
    </form>
    <form method="post" action="/mobile/jobs/{3}/action">
      <input type="hidden" name="action" value="cancel">
      <button type="submit" class="secondary">取消</button>
    </form>
  </div>
</section>
<section class="card">
  <h2>素材</h2>
  {7}
</section>
{8}
<section class="card">
  <a href="/mobile/jobs">返回任务列表</a>
</section>""".format(
        html.escape(job.topic),
        html.escape(str(job.status)),
        html.escape(job.current_step),
        job.id,
        html.escape(job.style_preset),
        job.target_shot_count,
        html.escape(job.image_backend),
        assets_section,
        error_html,
        _logout_form(),
    )
    return _page("任务详情", body)


@router.post("/jobs/{job_id}/action")
async def mobile_job_action(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db),
    dispatcher=Depends(get_job_dispatcher),
):
    redirect = _mobile_auth_redirect(request)
    if redirect is not None:
        return redirect

    payload = _parse_form_body(await request.body())
    action = payload.get("action", [""])[0].strip()
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")

    if action == "approve":
        job.status = JobStatus.COMPLETED
        db.add(
            Review(
                job_id=job.id,
                review_type="manual",
                result="approved",
                score=1,
                notes="approved via mobile",
                reviewed_by="mobile",
            )
        )
        db.commit()
    elif action == "retry":
        job.status = JobStatus.PENDING
        db.commit()
        safe_enqueue(dispatcher, job.id)
    elif action == "cancel":
        job.status = JobStatus.CANCELLED
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="unsupported action")
    return RedirectResponse(url="/mobile/jobs/{0}".format(job.id), status_code=303)


@router.get("/assets/{asset_id}/preview")
def mobile_asset_preview(asset_id: int, request: Request, db: Session = Depends(get_db)):
    redirect = _mobile_auth_redirect(request)
    if redirect is not None:
        return redirect

    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="asset not found")
    preview_path = Path(asset.preview_path or asset.file_path)
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail="asset preview file not found")
    media_type = None
    if preview_path.suffix.lower() == ".png":
        media_type = "image/png"
    elif preview_path.suffix.lower() in (".jpg", ".jpeg"):
        media_type = "image/jpeg"
    elif preview_path.suffix.lower() == ".webp":
        media_type = "image/webp"
    return FileResponse(str(preview_path), media_type=media_type)
