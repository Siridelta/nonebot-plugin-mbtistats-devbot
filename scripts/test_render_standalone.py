"""
Standalone renderer for MBTI template debugging.

Why this script exists:
- It bypasses NoneBot lifecycle and plugin hooks entirely.
- It reproduces the same "HTML -> browser render -> screenshot" flow.
- It captures browser-side logs to help diagnose hangs in split modules.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import socket
import sys
import time
from dataclasses import dataclass
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import Any
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright


def _project_root() -> Path:
    # scripts/test_render_standalone.py -> project_root/scripts -> project_root
    return Path(__file__).resolve().parent.parent


def _template_root(project_root: Path) -> Path:
    return (
        project_root
        / "dev-plugins"
        / "mbtistats"
        / "src"
        / "nonebot_plugin_mbtistats"
        / "template"
    )


def _transform_module_path(project_root: Path) -> Path:
    return (
        project_root
        / "dev-plugins"
        / "mbtistats"
        / "src"
        / "nonebot_plugin_mbtistats"
        / "transform_render_data.py"
    )


def _load_transform_to_render_data(project_root: Path):
    """
    Load transform_to_render_data without importing plugin package entrypoints.
    This avoids triggering NoneBot initialization.
    """
    module_path = _transform_module_path(project_root)
    if not module_path.exists():
        raise FileNotFoundError(f"transform module not found: {module_path}")

    spec = importlib.util.spec_from_file_location("transform_render_data", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to create import spec for transform_render_data")
    module = importlib.util.module_from_spec(spec)
    sys.modules["transform_render_data"] = module
    spec.loader.exec_module(module)

    if not hasattr(module, "transform_to_render_data"):
        raise RuntimeError("transform_to_render_data() not found in module")
    return module.transform_to_render_data


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        return int(s.getsockname()[1])


class StaticTemplateHandler(SimpleHTTPRequestHandler):
    # Ensure .mjs is served as JavaScript module.
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".mjs": "application/javascript",
        ".js": "application/javascript",
    }

    def __init__(self, *args, root_dir: Path, **kwargs):
        self.root_dir = root_dir
        super().__init__(*args, **kwargs)

    def translate_path(self, path: str) -> str:
        return str(self.root_dir / path.lstrip("/"))

    def log_message(self, format: str, *args):
        # Keep terminal output clean; detailed logs are captured from browser events.
        return


@dataclass
class TempServer:
    root_dir: Path
    port: int
    server: HTTPServer | None = None
    thread: Thread | None = None

    def start(self) -> None:
        def run() -> None:
            def handler(*args, **kwargs):
                return StaticTemplateHandler(*args, root_dir=self.root_dir, **kwargs)

            self.server = HTTPServer(("127.0.0.1", self.port), handler)
            self.server.serve_forever()

        self.thread = Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()


def _load_backend_data(mock_path: Path) -> list[dict[str, Any]]:
    with open(mock_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, list):
        raise ValueError(f"mock data must be a list, got: {type(loaded)}")
    return loaded


def _render_html(template_root: Path, mode: str, data: dict[str, Any], html_path: Path) -> None:
    env = Environment(loader=FileSystemLoader(template_root))
    template = env.get_template(f"{mode}/index.html")
    html_content = template.render(**data)
    html_path.write_text(html_content, encoding="utf-8")


async def _screenshot_page(
    url: str,
    output_path: Path,
    log_path: Path,
    width: int,
    height: int,
    timeout_s: int,
    wait_until: str,
) -> None:
    log_lines: list[str] = []

    def _log(line: str) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{ts}] {line}"
        log_lines.append(message)
        print(message)

    _log(f"open url: {url}")
    _log(f"viewport: {width}x{height}, timeout={timeout_s}s, wait_until={wait_until}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=2,
            bypass_csp=True,
        )
        page = await context.new_page()

        page.on("console", lambda msg: _log(f"[console.{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: _log(f"[pageerror] {err}"))
        page.on("requestfailed", lambda req: _log(f"[requestfailed] {req.url} :: {req.failure}"))

        try:
            await page.goto(url, timeout=timeout_s * 1000, wait_until=wait_until)
            _log("goto done")

            # We wait for canvas because echarts should render at least one canvas.
            await page.wait_for_selector("canvas", timeout=min(timeout_s, 20) * 1000)
            _log("canvas detected")

            # Small buffer to let animations/layout settle.
            await page.wait_for_timeout(1000)

            container = await page.query_selector(".container")
            if container is not None:
                await container.screenshot(type="png", path=str(output_path))
                _log(f"screenshot saved (container): {output_path}")
            else:
                await page.screenshot(type="png", full_page=True, path=str(output_path))
                _log(f"screenshot saved (full_page): {output_path}")
        finally:
            await page.close()
            await context.close()
            await browser.close()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("\n".join(log_lines), encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standalone Playwright renderer for MBTI template")
    parser.add_argument("--mode", default="mbti-stats", help="template mode directory name")
    parser.add_argument("--mock", default="", help="optional custom mock.json path")
    parser.add_argument("--output", default="", help="optional output png path")
    parser.add_argument("--log", default="", help="optional browser log path")
    parser.add_argument("--width", type=int, default=1050, help="viewport width")
    parser.add_argument("--height", type=int, default=1000, help="viewport height")
    parser.add_argument("--timeout", type=int, default=30, help="render timeout in seconds")
    parser.add_argument(
        "--wait-until",
        default="load",
        choices=["load", "domcontentloaded", "networkidle", "commit"],
        help="Playwright wait_until value for page.goto",
    )
    parser.add_argument(
        "--keep-html",
        action="store_true",
        help="keep temporary rendered html for manual browser inspection",
    )
    return parser


async def _main_async(args: argparse.Namespace) -> int:
    project_root = _project_root()
    template_root = _template_root(project_root)
    mode_dir = template_root / args.mode
    index_path = mode_dir / "index.html"
    if not index_path.exists():
        print(f"ERROR: index.html not found: {index_path}")
        return 2

    mock_path = Path(args.mock) if args.mock else (mode_dir / "mock.json")
    if not mock_path.exists():
        print(f"ERROR: mock.json not found: {mock_path}")
        return 2

    transform_to_render_data = _load_transform_to_render_data(project_root)
    backend_data = _load_backend_data(mock_path)
    render_data = transform_to_render_data(history_data=backend_data)

    now_ms = int(time.time() * 1000)
    html_path = mode_dir / f"render_standalone_{uuid4().hex}.html"

    default_output = project_root / "data" / "mbtistats" / "cache" / "standalone" / f"standalone-render-{now_ms}.png"
    output_path = Path(args.output) if args.output else default_output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    default_log = output_path.with_suffix(".log")
    log_path = Path(args.log) if args.log else default_log

    _render_html(template_root, args.mode, render_data, html_path)
    print(f"render html done: {html_path}")

    server = TempServer(root_dir=template_root, port=_find_free_port())
    server.start()
    await asyncio.sleep(0.3)

    url = f"http://127.0.0.1:{server.port}/{args.mode}/{html_path.name}"
    try:
        await _screenshot_page(
            url=url,
            output_path=output_path,
            log_path=log_path,
            width=args.width,
            height=args.height,
            timeout_s=args.timeout,
            wait_until=args.wait_until,
        )
    finally:
        server.stop()
        if args.keep_html:
            print(f"keep html: {html_path}")
        elif html_path.exists():
            html_path.unlink()

    print(f"done, image: {output_path}")
    print(f"done, log:   {log_path}")
    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return asyncio.run(_main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
