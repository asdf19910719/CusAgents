import base64
import binascii
import time
from pathlib import Path

from app.providers.image.browser_profile_manager import BrowserProfileManager


class ChatgptWebClient:
    def __init__(
        self,
        base_url,
        profile_dir,
        headless=True,
        timeout_seconds=180,
        browser_channel="",
        executable_path="",
        cdp_url="",
        image_prompt_suffix="",
        browser_runner=None,
    ):
        self.base_url = base_url
        self.profile_manager = BrowserProfileManager(profile_dir)
        self.headless = headless
        self.timeout_seconds = timeout_seconds
        self.browser_channel = browser_channel
        self.executable_path = executable_path
        self.cdp_url = cdp_url
        self.image_prompt_suffix = image_prompt_suffix
        self.browser_runner = browser_runner or self._run_browser_flow

    def generate_image_file(self, prompt, shot_index):
        profile_dir = self.profile_manager.ensure_profile_dir()
        download_dir = self.profile_manager.get_download_dir()
        resolved_prompt = (prompt or "").strip()
        if self.image_prompt_suffix:
            resolved_prompt = "{0}\n\n{1}".format(resolved_prompt, self.image_prompt_suffix.strip()).strip()
        generated_path, metadata = self.browser_runner(
            prompt=resolved_prompt,
            shot_index=shot_index,
            base_url=self.base_url,
            profile_dir=str(profile_dir),
            download_dir=str(download_dir),
            headless=self.headless,
            timeout_seconds=self.timeout_seconds,
            browser_channel=self.browser_channel,
            executable_path=self.executable_path,
            cdp_url=self.cdp_url,
        )
        generated_path = Path(generated_path)
        if not generated_path.is_absolute():
            generated_path = generated_path.resolve()
        if not generated_path.exists():
            raise RuntimeError("chatgpt_web browser flow did not produce expected file: " + str(generated_path))
        combined_metadata = {
            "base_url": self.base_url,
            "profile_dir": str(profile_dir),
            "download_dir": str(download_dir),
            "headless": self.headless,
            "timeout_seconds": self.timeout_seconds,
            "browser_channel": self.browser_channel,
            "executable_path": self.executable_path,
            "cdp_url": self.cdp_url,
            "prompt": resolved_prompt,
        }
        if metadata:
            combined_metadata.update(metadata)
        return generated_path, combined_metadata

    def _run_browser_flow(
        self,
        prompt,
        shot_index,
        base_url,
        profile_dir,
        download_dir,
        headless,
        timeout_seconds,
        browser_channel,
        executable_path,
        cdp_url,
    ):
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "playwright is not installed. Run `python -m pip install -r requirements.txt` and `playwright install chromium`."
            ) from exc

        target_path = Path(download_dir) / ("chatgpt-web-shot-{0}.png".format(shot_index))
        with sync_playwright() as playwright:
            browser = None
            if cdp_url:
                browser = playwright.chromium.connect_over_cdp(cdp_url)
                context = browser.contexts[0] if browser.contexts else browser.new_context(accept_downloads=True)
            else:
                launch_kwargs = {"headless": headless, "accept_downloads": True}
                if executable_path:
                    launch_kwargs["executable_path"] = executable_path
                elif browser_channel:
                    launch_kwargs["channel"] = browser_channel
                context = playwright.chromium.launch_persistent_context(profile_dir, **launch_kwargs)
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.set_default_timeout(int(timeout_seconds * 1000))
                page.goto(base_url, wait_until="domcontentloaded")
                composer = self._resolve_composer(page)
                if composer is None:
                    raise RuntimeError(
                        "chatgpt_web profile is not ready or not logged in. Run the browser login script first."
                    )
                self._start_new_chat(page)
                composer = self._resolve_composer(page)
                if composer is None:
                    raise RuntimeError("chatgpt_web composer is not available after starting a new chat")
                composer.click()
                self._clear_composer(composer)
                try:
                    composer.fill(prompt)
                except Exception:
                    composer.type(prompt)
                self._submit_prompt(page, composer)
                saved_path, flow_metadata = self._wait_for_generated_image(
                    page=page,
                    target_path=target_path,
                    timeout_seconds=timeout_seconds,
                    playwright_timeout_error=PlaywrightTimeoutError,
                )
                return saved_path, flow_metadata
            finally:
                if cdp_url and browser is not None:
                    browser.close()
                else:
                    context.close()

    def _resolve_composer(self, page):
        selectors = (
            "#prompt-textarea",
            "[data-testid='composer-text-input']",
            "[contenteditable='true'][data-placeholder]",
            "[contenteditable='true']",
            "textarea",
        )
        for selector in selectors:
            locator = page.locator(selector)
            try:
                count = locator.count()
            except Exception:
                continue
            for index in range(count):
                item = locator.nth(index)
                try:
                    if item.is_visible():
                        return item
                except Exception:
                    continue
        return None

    def _start_new_chat(self, page):
        text_labels = ("New chat", "新聊天")
        for label in text_labels:
            try:
                item = page.get_by_text(label, exact=True)
                if item.count() > 0 and item.first.is_visible():
                    item.first.click()
                    page.wait_for_timeout(1000)
                    return
            except Exception:
                continue
        selectors = (
            "a[aria-label='New chat']",
            "button[aria-label='New chat']",
            "a[aria-label='新聊天']",
            "button[aria-label='新聊天']",
        )
        for selector in selectors:
            item = page.locator(selector)
            try:
                if item.count() > 0 and item.first.is_visible():
                    item.first.click()
                    page.wait_for_timeout(1000)
                    return
            except Exception:
                continue

    def _clear_composer(self, composer):
        try:
            composer.press("Control+A")
            composer.press("Backspace")
        except Exception:
            pass

    def _submit_prompt(self, page, composer):
        send_selectors = (
            "button[data-testid='send-button']",
            "button[aria-label='Send prompt']",
            "button[aria-label='Send message']",
            "button[aria-label='发送提示']",
            "button[aria-label='发送消息']",
            "button[aria-label='发送']",
        )
        deadline = time.time() + 8
        while time.time() < deadline:
            for selector in send_selectors:
                button = page.locator(selector)
                try:
                    if button.count() > 0 and button.first.is_enabled():
                        button.first.click()
                        return
                except Exception:
                    continue
            page.wait_for_timeout(250)
        composer.press("Enter")

    def _wait_for_generated_image(self, page, target_path, timeout_seconds, playwright_timeout_error):
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            saved_path = self._try_download_button(page, target_path, playwright_timeout_error)
            if saved_path is not None:
                return saved_path, {"capture_method": "download_button"}
            saved_path = self._try_capture_latest_image(page, target_path)
            if saved_path is not None:
                return saved_path, {"capture_method": "image_src"}
            page.wait_for_timeout(2000)
        raise RuntimeError("chatgpt_web image generation timed out after {0} seconds".format(timeout_seconds))

    def _try_download_button(self, page, target_path, playwright_timeout_error):
        selectors = (
            "button[aria-label*='Download']",
            "button[data-testid*='download']",
            "a[download]",
        )
        for selector in selectors:
            button = page.locator(selector)
            try:
                if button.count() == 0:
                    continue
                with page.expect_download(timeout=1500) as download_info:
                    button.first.click()
                download = download_info.value
                download.save_as(str(target_path))
                return target_path
            except playwright_timeout_error:
                continue
            except Exception:
                continue
        return None

    def _try_capture_latest_image(self, page, target_path):
        data_url = page.evaluate(
            """() => {
                const minWidth = 256;
                const minHeight = 256;
                const images = Array.from(document.querySelectorAll('img'));
                let candidate = null;
                for (const image of images) {
                    const width = image.naturalWidth || image.width || 0;
                    const height = image.naturalHeight || image.height || 0;
                    if (width < minWidth || height < minHeight) {
                        continue;
                    }
                    const src = image.currentSrc || image.src || '';
                    if (!src) {
                        continue;
                    }
                    if (src.startsWith('blob:') || src.startsWith('data:image/') || src.startsWith('http')) {
                        candidate = src;
                    }
                }
                return candidate;
            }"""
        )
        if not data_url:
            return None
        if data_url.startswith("data:image/"):
            encoded = data_url.split(",", 1)[1]
            try:
                target_path.write_bytes(base64.b64decode(encoded))
            except (ValueError, binascii.Error):
                return None
            return target_path
        if data_url.startswith("blob:") or data_url.startswith("http"):
            image_bytes = page.evaluate(
                """async (src) => {
                    const response = await fetch(src);
                    const buffer = await response.arrayBuffer();
                    return Array.from(new Uint8Array(buffer));
                }""",
                data_url,
            )
            if not image_bytes:
                return None
            target_path.write_bytes(bytes(image_bytes))
            return target_path
        return None
