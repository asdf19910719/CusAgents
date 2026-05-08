import argparse
from pathlib import Path

from _bootstrap import ensure_project_root_on_path


ensure_project_root_on_path()

from app.core.config import load_settings


def parse_args():
    parser = argparse.ArgumentParser(description="Open ChatGPT Web with a persistent Playwright profile for login.")
    parser.add_argument("--profile-dir", default="", help="Override CHATGPT_WEB_PROFILE_DIR")
    parser.add_argument("--base-url", default="", help="Override CHATGPT_WEB_BASE_URL")
    parser.add_argument("--browser-channel", default="", help="Override CHATGPT_WEB_BROWSER_CHANNEL")
    parser.add_argument("--executable-path", default="", help="Use a specific Chrome or Edge executable")
    parser.add_argument("--check", action="store_true", help="Only validate configuration without opening a browser")
    return parser.parse_args()


def main():
    args = parse_args()
    settings = load_settings(allow_placeholder_llm_api_key=True)
    profile_dir = Path(args.profile_dir or settings.chatgpt_web_profile_dir).resolve()
    base_url = args.base_url or settings.chatgpt_web_base_url
    browser_channel = args.browser_channel or settings.chatgpt_web_browser_channel
    executable_path = args.executable_path or settings.chatgpt_web_executable_path

    if args.check:
        print("chatgpt_web login configuration ok")
        print("profile_dir=" + str(profile_dir))
        print("base_url=" + base_url)
        print("browser_channel=" + (browser_channel or "<default>"))
        print("executable_path=" + (executable_path or "<default>"))
        return

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "playwright is not installed. Run `python -m pip install -r requirements.txt` and `playwright install chromium`."
        ) from exc

    profile_dir.mkdir(parents=True, exist_ok=True)
    print("Opening ChatGPT Web login browser...")
    print("Profile dir:", str(profile_dir))
    print("Base URL:", base_url)
    print("After login is complete, return to this terminal and press Enter to close the browser.")

    launch_kwargs = {"headless": False}
    if executable_path:
        launch_kwargs["executable_path"] = executable_path
    elif browser_channel:
        launch_kwargs["channel"] = browser_channel

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(str(profile_dir), **launch_kwargs)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(base_url, wait_until="domcontentloaded")
        input()
        context.close()


if __name__ == "__main__":
    main()
