import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_python_script(relative_path, extra_env=None):
    env = os.environ.copy()
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, str(ROOT / relative_path), "--check"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )


def test_run_feishu_long_connection_script_supports_check_mode():
    result = run_python_script(
        "scripts/run_feishu_long_connection.py",
        {
            "LLM_API_KEY": "placeholder-llm-api-key",
            "FEISHU_APP_ID": "cli_test",
            "FEISHU_APP_SECRET": "secret_test",
        },
    )

    assert result.returncode == 0
    assert "feishu long connection configuration ok" in result.stdout.lower()


def test_run_worker_script_supports_check_mode():
    result = run_python_script(
        "scripts/run_worker.py",
        {
            "LLM_API_KEY": "placeholder-llm-api-key",
        },
    )

    assert result.returncode == 0
    assert "worker entrypoint ok" in result.stdout.lower()


def test_demo_request_help_mentions_codex_cli_backend():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/demo_request.py"), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0
    assert "codex_cli" in result.stdout
    assert "chatgpt_web" in result.stdout


def test_run_chatgpt_web_login_script_supports_check_mode():
    result = run_python_script(
        "scripts/run_chatgpt_web_login.py",
        {
            "LLM_API_KEY": "placeholder-llm-api-key",
        },
    )

    assert result.returncode == 0
    assert "chatgpt_web login configuration ok" in result.stdout.lower()


def test_run_chatgpt_web_browser_script_supports_check_mode():
    result = run_python_script(
        "scripts/run_chatgpt_web_browser.py",
        {
            "LLM_API_KEY": "placeholder-llm-api-key",
            "CHATGPT_WEB_EXECUTABLE_PATH": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "CHATGPT_WEB_CDP_URL": "http://127.0.0.1:65530",
        },
    )

    assert result.returncode == 0
    assert "chatgpt_web browser configuration ok" in result.stdout.lower()
