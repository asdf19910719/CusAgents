import argparse
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from _bootstrap import ensure_project_root_on_path


ensure_project_root_on_path()

from app.core.config import load_settings


def parse_args():
    parser = argparse.ArgumentParser(description="Launch ordinary Chrome for ChatGPT Web automation over CDP.")
    parser.add_argument("--profile-dir", default="", help="Override CHATGPT_WEB_PROFILE_DIR")
    parser.add_argument("--base-url", default="", help="Override CHATGPT_WEB_BASE_URL")
    parser.add_argument("--executable-path", default="", help="Override CHATGPT_WEB_EXECUTABLE_PATH")
    parser.add_argument("--cdp-url", default="", help="Override CHATGPT_WEB_CDP_URL")
    parser.add_argument("--check", action="store_true", help="Validate configuration and CDP status only")
    return parser.parse_args()


def is_cdp_ready(cdp_url):
    try:
        with urlopen(cdp_url.rstrip("/") + "/json/version", timeout=3) as response:
            return response.status == 200
    except Exception:
        return False


def main():
    args = parse_args()
    settings = load_settings(allow_placeholder_llm_api_key=True)
    profile_dir = Path(args.profile_dir or settings.chatgpt_web_profile_dir).resolve()
    base_url = args.base_url or settings.chatgpt_web_base_url
    executable_path = args.executable_path or settings.chatgpt_web_executable_path
    cdp_url = args.cdp_url or settings.chatgpt_web_cdp_url or "http://127.0.0.1:9222"
    port = urlparse(cdp_url).port or 9222

    if not executable_path:
        raise RuntimeError("CHATGPT_WEB_EXECUTABLE_PATH is required for CDP browser mode")

    profile_dir.mkdir(parents=True, exist_ok=True)
    ready = is_cdp_ready(cdp_url)
    if args.check:
        print("chatgpt_web browser configuration ok")
        print("profile_dir=" + str(profile_dir))
        print("base_url=" + base_url)
        print("executable_path=" + executable_path)
        print("cdp_url=" + cdp_url)
        print("cdp_ready=" + str(ready))
        return

    if ready:
        print("chatgpt_web CDP browser already running: " + cdp_url)
        return

    subprocess.Popen(
        [
            executable_path,
            "--remote-debugging-port={0}".format(port),
            "--user-data-dir={0}".format(profile_dir),
            "--new-window",
            base_url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)
    if not is_cdp_ready(cdp_url):
        raise RuntimeError("Chrome started but CDP endpoint is not reachable: " + cdp_url)
    print("chatgpt_web CDP browser started: " + cdp_url)


if __name__ == "__main__":
    main()
