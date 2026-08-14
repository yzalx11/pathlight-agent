"""A narrowly scoped Chrome CDP reader for Pathlight's own recruiting session."""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException
from websockets.sync.client import connect

from app.config import settings
from app.schemas import BrowserJobPreviewPayload, BrowserSessionRead
from app.services.browser_bridge import is_supported_boss_job_url

_managed_chrome: subprocess.Popen[bytes] | None = None


def _devtools_base() -> str:
    return f"http://127.0.0.1:{settings.browser_debug_port}"


def _profile_dir() -> Path:
    return settings.upload_dir.parent / "recruiting-browser-profile"


def _find_browser_executable() -> str | None:
    candidates = [
        os.environ.get("PATHLIGHT_CHROME_PATH", ""),
        shutil.which("chrome.exe") or "",
        shutil.which("msedge.exe") or "",
        str(Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe"),
        str(Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe"),
        str(Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft/Edge/Application/msedge.exe"),
    ]
    return next((candidate for candidate in candidates if candidate and Path(candidate).is_file()), None)


def _devtools_json(path: str) -> Any | None:
    try:
        response = httpx.get(f"{_devtools_base()}{path}", timeout=0.8)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError):
        return None


def browser_session_status() -> BrowserSessionRead:
    global _managed_chrome
    if _managed_chrome is not None and _managed_chrome.poll() is not None:
        _managed_chrome = None
    cdp_available = _devtools_json("/json/version") is not None
    return BrowserSessionRead(
        chrome_running=_managed_chrome is not None or cdp_available,
        cdp_available=cdp_available,
        observing=cdp_available,
        message=(
            "正在观察当前 BOSS 职位页。"
            if cdp_available
            else "启动专用招聘浏览器后，Pathlight 才会读取当前职位页。"
        ),
    )


def launch_recruiting_browser() -> BrowserSessionRead:
    global _managed_chrome
    if _devtools_json("/json/version") is not None:
        return browser_session_status()

    executable = _find_browser_executable()
    if executable is None:
        raise HTTPException(
            status_code=422,
            detail="Chrome or Edge was not found. Install a supported browser, or set PATHLIGHT_CHROME_PATH.",
        )

    profile_dir = _profile_dir()
    profile_dir.mkdir(parents=True, exist_ok=True)
    _managed_chrome = subprocess.Popen(
        [
            executable,
            f"--remote-debugging-port={settings.browser_debug_port}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "https://www.zhipin.com/",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(12):
        time.sleep(0.25)
        if _devtools_json("/json/version") is not None:
            return browser_session_status()
    raise HTTPException(status_code=503, detail="Recruiting browser started, but CDP is not ready yet. Try again shortly.")


def _read_visible_page(websocket_url: str) -> dict[str, str] | None:
    expression = """(() => {
      if (document.visibilityState !== 'visible') return null;
      const visibleText = (document.body?.innerText || '')
        .split('\\n').map((line) => line.trim()).filter(Boolean).join('\\n').slice(0, 30000);
      if (!visibleText) return null;
      return JSON.stringify({
        page_title: document.title.trim() || 'BOSS 职位页面',
        source_link: window.location.href,
        visible_text: visibleText,
      });
    })()"""
    try:
        with connect(websocket_url, open_timeout=1, close_timeout=1) as websocket:
            websocket.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": expression, "returnByValue": True}}))
            response = json.loads(websocket.recv(timeout=2))
    except Exception:
        return None
    value = response.get("result", {}).get("result", {}).get("value")
    return json.loads(value) if isinstance(value, str) else None


def capture_visible_boss_job() -> BrowserJobPreviewPayload | None:
    targets = _devtools_json("/json/list")
    if not isinstance(targets, list):
        return None
    for target in targets:
        source_link = target.get("url", "")
        if target.get("type") != "page" or not is_supported_boss_job_url(source_link):
            continue
        captured = _read_visible_page(target.get("webSocketDebuggerUrl", ""))
        if captured is None:
            continue
        try:
            return BrowserJobPreviewPayload(**captured)
        except ValueError:
            continue
    return None
