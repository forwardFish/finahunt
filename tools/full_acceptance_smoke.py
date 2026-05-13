from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WEB_SRC = ROOT / "apps" / "web" / "src"
EVIDENCE_ROOT = ROOT / "docs" / "qa" / "full-acceptance"
TEST_RESULTS = EVIDENCE_ROOT / "test-results"
SCREENSHOTS = EVIDENCE_ROOT / "screenshots"

BROKEN_VISIBLE_TEXT = "?" * 4

ROUTES = [
    {"path": "/", "name": "home", "must_contain": ["今日总览", "今日资讯", "热门题材"], "forbidden_text": [BROKEN_VISIBLE_TEXT, "\u951f"], "query": True},
    {"path": "/fermentation", "name": "fermentation", "must_contain": ["题材发现", "阶段分布", "主线发酵矩阵"], "query": True},
    {"path": "/research", "name": "research", "must_contain": ["样例列表", "验证分组", "代表性消息"], "query": True},
    {"path": "/workbench", "name": "workbench", "must_contain": ["主线总览", "事件与证据带", "低位题材矩阵"], "query": True},
    {"path": "/low-position", "name": "low-position", "must_contain": ["低位题材看板", "验证桶", "运行信息"], "query": True},
    {"path": "/sprint-2", "name": "sprint-2", "must_contain": ["Sprint 2 旧入口", "推荐验收路线"], "query": True},
]

SEARCH_CASE = {"path": "/workbench?q=%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD", "name": "workbench-search-q", "must_contain": ["搜索命中"], "expected_final_path": "/workbench", "query": False}
VISUAL_MAIN_ROUTES = {"/", "/fermentation", "/research", "/workbench"}

API_CASES = [
    {"name": "daily-snapshot-default", "method": "GET", "path": "/api/daily-snapshot", "body": None, "expect_json": True, "expect_statuses": [200], "required_keys": ["date", "stats", "runs", "themes", "events"]},
    {"name": "daily-snapshot-valid-date", "method": "GET", "path": "/api/daily-snapshot?date={latest_date}", "body": None, "expect_json": True, "expect_statuses": [200], "required_keys": ["date", "stats", "runs", "themes", "events"]},
    {"name": "daily-snapshot-empty-date", "method": "GET", "path": "/api/daily-snapshot?date=1900-01-01", "body": None, "expect_json": True, "expect_statuses": [200], "required_keys": ["date", "stats", "runs", "themes", "events"]},
    {"name": "daily-snapshot-invalid-date-fallback", "method": "GET", "path": "/api/daily-snapshot?date=bad-date", "body": None, "expect_json": True, "expect_statuses": [200], "required_keys": ["date", "stats", "runs", "themes", "events"]},
    {"name": "refresh-latest-post", "method": "POST", "path": "/api/refresh-latest", "body": b"{}", "expect_json": True, "expect_statuses": [200, 500], "required_keys_any": ["ok", "error", "run_id"]},
    {"name": "refresh-latest-method-guard", "method": "GET", "path": "/api/refresh-latest", "body": None, "expect_json": False, "expect_statuses": [404, 405]},
    {"name": "run-low-position-post", "method": "POST", "path": "/api/run-low-position", "body": b"{}", "expect_json": True, "expect_statuses": [200, 500], "required_keys_any": ["ok", "error", "run_id"]},
    {"name": "run-low-position-method-guard", "method": "GET", "path": "/api/run-low-position", "body": None, "expect_json": False, "expect_statuses": [404, 405]},
]

PYTHON_COMMANDS = [
    {"name": "latest-snapshot-command", "command": [sys.executable, "tools/run_latest_snapshot.py"], "expect_json": True, "timeout": 180},
    {"name": "low-position-command", "command": [sys.executable, "tools/run_low_position_workbench.py"], "expect_json": True, "timeout": 240},
    {"name": "live-event-cognition-command-help", "command": [sys.executable, "tools/run_live_event_cognition.py"], "expect_json": True, "timeout": 180},
]

MOJIBAKE_MARKERS = ["\u951f", "\ufffd", "\u9225", "\u95bf", "\u942e", "\u9359", "\u68f0", "\u6d63", "\u93c3", "\u8930", "\u7a0c", "\u93b6", "\u93b5", "\u93c8", "\u6d93", "\u695d", "\u7f01", "\u5bf0"]
NEXT_ERROR_MARKERS = ["Application error", "Internal Server Error", "NEXT_NOT_FOUND", "Unhandled Runtime Error"]

@dataclass
class CheckResult:
    name: str
    path: str
    status: str
    ok: bool
    duration_ms: int
    details: dict[str, Any]


def request_text(url: str, method: str = "GET", body: bytes | None = None, timeout: int = 120) -> tuple[int | None, str, dict[str, str], str]:
    headers = {"User-Agent": "finahunt-full-acceptance-smoke/2.0"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            text = resp.read().decode(charset, errors="replace")
            return resp.status, text, dict(resp.headers.items()), resp.geturl()
    except urllib.error.HTTPError as error:
        charset = error.headers.get_content_charset() or "utf-8"
        text = error.read().decode(charset, errors="replace")
        final_url = getattr(error, "url", url) or url
        return error.code, text, dict(error.headers.items()), final_url
    except Exception as error:  # noqa: BLE001 - evidence capture should not mask failures
        return None, str(error), {}, url


def summarize_json_shape(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except Exception as error:  # noqa: BLE001
        return {"json": False, "error": str(error), "preview": text[:500]}
    if isinstance(payload, dict):
        return {
            "json": True,
            "type": "object",
            "keys": sorted(payload.keys())[:50],
            "ok": payload.get("ok"),
            "date": payload.get("date") or payload.get("latestDate"),
            "stats_keys": sorted(payload.get("stats", {}).keys()) if isinstance(payload.get("stats"), dict) else [],
            "error": payload.get("error"),
        }
    if isinstance(payload, list):
        return {"json": True, "type": "array", "length": len(payload)}
    return {"json": True, "type": type(payload).__name__}


def discover_latest_date(base_url: str) -> str:
    status, text, _headers, _final_url = request_text(base_url.rstrip("/") + "/api/daily-snapshot", timeout=45)
    if status and 200 <= status < 300:
        try:
            payload = json.loads(text)
            date = payload.get("date")
            if isinstance(date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                return date
        except Exception:
            pass
    return time.strftime("%Y-%m-%d")


def path_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path or "/"
    return path.rstrip("/") or "/"


def extract_h1(text: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    value = re.sub(r"<[^>]+>", "", match.group(1))
    return html.unescape(value).strip()


def route_cases(latest_date: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for route in ROUTES:
        cases.append({**route, "case_name": route["name"], "url_path": route["path"]})
        if route.get("query"):
            sep = "&" if "?" in route["path"] else "?"
            cases.append({**route, "case_name": f"{route['name']}-date-query", "url_path": f"{route['path']}{sep}date={latest_date}"})
    cases.append({**SEARCH_CASE, "case_name": SEARCH_CASE["name"], "url_path": SEARCH_CASE["path"]})
    return cases


def run_route_smoke(base_url: str, latest_date: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    redirect_results: list[dict[str, Any]] = []
    search_results: list[dict[str, Any]] = []
    for route in route_cases(latest_date):
        start = time.perf_counter()
        initial_url = base_url.rstrip("/") + route["url_path"]
        status_code, text, headers, final_url = request_text(initial_url, timeout=45)
        duration_ms = int((time.perf_counter() - start) * 1000)
        missing = [needle for needle in route["must_contain"] if needle not in text]
        forbidden = [needle for needle in route.get("forbidden_text", []) if needle in text]
        mojibake = [marker for marker in MOJIBAKE_MARKERS if marker in text]
        next_error = [marker for marker in NEXT_ERROR_MARKERS if marker in text]
        expected_final_path = route.get("expected_final_path", route.get("path"))
        final_path = path_from_url(final_url)
        final_url_ok = expected_final_path is None or final_path == expected_final_path
        ok = status_code is not None and 200 <= status_code < 400 and final_url_ok and not missing and not forbidden and not next_error and not mojibake
        details = {
            "initial_url": initial_url,
            "final_url": final_url,
            "expected_final_path": expected_final_path,
            "final_url_ok": final_url_ok,
            "h1_or_identity_text": extract_h1(text),
            "screenshot_path_desktop": str((SCREENSHOTS / f"desktop-{route['name']}.png").relative_to(ROOT)),
            "screenshot_path_mobile": str((SCREENSHOTS / f"mobile-{route['name']}.png").relative_to(ROOT)),
            "route": route.get("path"),
            "missing_text": missing,
            "forbidden_text_present": forbidden,
            "mojibake_markers": mojibake,
            "next_error_markers": next_error,
            "content_type": headers.get("content-type", ""),
            "html_bytes": len(text.encode("utf-8", errors="replace")),
        }
        result = CheckResult(
            name=route["case_name"],
            path=route["url_path"],
            status=str(status_code) if status_code is not None else "request_error",
            ok=ok,
            duration_ms=duration_ms,
            details=details,
        )
        results.append(result)
        if route.get("expected_final_path"):
            redirect_results.append(asdict(result))
        if route["case_name"] == SEARCH_CASE["name"]:
            search_results.append(asdict(result))
    write_json(TEST_RESULTS / "redirect-final-url.json", redirect_results)
    write_json(TEST_RESULTS / "workbench-search-smoke.json", search_results)
    return results


def format_case_path(path_template: str, latest_date: str) -> str:
    return path_template.format(latest_date=urllib.parse.quote(latest_date))


def run_api_smoke(base_url: str, api_timeout: int, latest_date: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    for api in API_CASES:
        path = format_case_path(api["path"], latest_date)
        start = time.perf_counter()
        status_code, text, headers, final_url = request_text(base_url.rstrip("/") + path, method=api["method"], body=api["body"], timeout=api_timeout)
        duration_ms = int((time.perf_counter() - start) * 1000)
        shape = summarize_json_shape(text)
        required_keys = api.get("required_keys", [])
        required_keys_any = api.get("required_keys_any", [])
        keys = set(shape.get("keys") or [])
        missing_required = [key for key in required_keys if key not in keys]
        has_any = True if not required_keys_any else any(key in keys for key in required_keys_any)
        status_ok = status_code in api["expect_statuses"]
        json_ok = (shape.get("json") is True) if api.get("expect_json") else True
        ok = status_ok and json_ok and not missing_required and has_any
        results.append(CheckResult(
            name=f"{api['method']} {path} ({api['name']})",
            path=path,
            status=str(status_code) if status_code is not None else "request_error",
            ok=ok,
            duration_ms=duration_ms,
            details={
                "api_route": api["path"].split("?")[0],
                "case": api["name"],
                "expected_statuses": api["expect_statuses"],
                "shape": shape,
                "missing_required_keys": missing_required,
                "required_keys_any_met": has_any,
                "content_type": headers.get("content-type", ""),
            },
        ))
    return results


def discover_code_surfaces() -> dict[str, Any]:
    app_dir = WEB_SRC / "app"
    page_routes: list[str] = []
    api_routes: list[dict[str, Any]] = []
    if app_dir.exists():
        for file in app_dir.rglob("page.tsx"):
            rel = file.parent.relative_to(app_dir).as_posix()
            page_routes.append("/" if rel == "." else f"/{rel}")
        for file in app_dir.rglob("route.ts"):
            rel = file.parent.relative_to(app_dir).as_posix()
            text = file.read_text(encoding="utf-8")
            methods = re.findall(r"export\s+async\s+function\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\b", text)
            api_routes.append({"path": f"/{rel}", "methods": methods, "file": str(file.relative_to(ROOT))})
    source_texts = []
    for file in WEB_SRC.rglob("*.ts*"):
        source_texts.append((file, file.read_text(encoding="utf-8")))
    fetch_targets = sorted({match.group(1) for _file, text in source_texts for match in re.finditer(r"fetch\(\s*[\"']([^\"']+)[\"']", text)})
    href_targets = sorted({match.group(1) for _file, text in source_texts for match in re.finditer(r"href=\{?\s*[\"']([^\"']+)[\"']", text) if match.group(1).startswith("/")})
    form_targets = sorted({match.group(1) for _file, text in source_texts for match in re.finditer(r"action=\{?\s*[\"']([^\"']+)[\"']", text) if match.group(1).startswith("/")})
    return {
        "page_routes": sorted(page_routes),
        "api_routes": sorted(api_routes, key=lambda item: item["path"]),
        "client_fetch_targets": fetch_targets,
        "static_href_targets": href_targets,
        "form_targets": form_targets,
        "python_commands": [" ".join(item["command"]) for item in PYTHON_COMMANDS],
    }


def run_integration_smoke(base_url: str, latest_date: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    inventory = discover_code_surfaces()
    write_json(TEST_RESULTS / "surface-inventory.json", inventory)

    api_paths = {item["path"] for item in inventory["api_routes"]}
    for target in inventory["client_fetch_targets"]:
        start = time.perf_counter()
        ok = target in api_paths
        results.append(CheckResult(
            name=f"client-fetch-target {target}",
            path=target,
            status="matched" if ok else "missing-api-route",
            ok=ok,
            duration_ms=int((time.perf_counter() - start) * 1000),
            details={"known_api_routes": sorted(api_paths)},
        ))

    targets = sorted(set(inventory["page_routes"] + inventory["static_href_targets"] + inventory["form_targets"]))
    for target in targets:
        if target.startswith("/api/"):
            continue
        start = time.perf_counter()
        suffix = "" if "?" in target else f"?date={urllib.parse.quote(latest_date)}"
        status_code, text, _headers, final_url = request_text(base_url.rstrip("/") + target + suffix, timeout=45)
        mojibake = [marker for marker in MOJIBAKE_MARKERS if marker in text]
        next_error = [marker for marker in NEXT_ERROR_MARKERS if marker in text]
        ok = status_code is not None and 200 <= status_code < 400 and not mojibake and not next_error
        results.append(CheckResult(
            name=f"internal-navigation-target {target}",
            path=target,
            status=str(status_code) if status_code is not None else "request_error",
            ok=ok,
            duration_ms=int((time.perf_counter() - start) * 1000),
            details={"mojibake_markers": mojibake, "next_error_markers": next_error},
        ))
    return results


def run_python_command_smoke() -> list[CheckResult]:
    results: list[CheckResult] = []
    for item in PYTHON_COMMANDS:
        start = time.perf_counter()
        try:
            proc = subprocess.run(item["command"], cwd=ROOT, capture_output=True, text=True, timeout=item["timeout"], check=False)
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            json_shape = summarize_json_shape(stdout) if item.get("expect_json") else {"json": None}
            ok = proc.returncode == 0 and (json_shape.get("json") is True if item.get("expect_json") else True)
            details = {
                "command": item["command"],
                "returncode": proc.returncode,
                "stdout_shape": json_shape,
                "stdout_preview": stdout[:1000],
                "stderr_preview": stderr[:1000],
            }
            results.append(CheckResult(item["name"], " ".join(item["command"]), str(proc.returncode), ok, int((time.perf_counter() - start) * 1000), details))
        except Exception as error:  # noqa: BLE001
            results.append(CheckResult(item["name"], " ".join(item["command"]), "command_error", False, int((time.perf_counter() - start) * 1000), {"error": str(error)}))
    return results


def capture_screenshots(base_url: str, latest_date: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    try:
        from playwright.sync_api import sync_playwright
    except Exception as error:  # noqa: BLE001
        return [CheckResult("playwright-import", "screenshots", "import_error", False, 0, {"error": str(error), "classification": "DOCUMENTED_BLOCKER"})]

    viewports = [
        ("desktop", {"width": 1448, "height": 1086}),
        ("mobile", {"width": 390, "height": 844}),
    ]
    visual_lines = ["# Visual Smoke", f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}", "", "Automated checks cover final URL, H1, required identity text, mojibake, Next error markers, and horizontal overflow. Editorial tone remains MANUAL_REVIEW_REQUIRED.", ""]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for viewport_name, viewport in viewports:
            page = browser.new_page(viewport=viewport, device_scale_factor=1)
            console_errors: list[str] = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            for route in ROUTES:
                start = time.perf_counter()
                file_path = SCREENSHOTS / f"{viewport_name}-{route['name']}.png"
                initial_url = base_url.rstrip("/") + route["path"] + f"?date={urllib.parse.quote(latest_date)}"
                try:
                    response = page.goto(initial_url, wait_until="networkidle", timeout=45_000)
                    page.screenshot(path=str(file_path), full_page=True)
                    status = response.status if response else None
                    final_url = page.url
                    try:
                        title = page.locator("h1").first.text_content(timeout=1_500) or ""
                    except Exception:
                        title = ""
                    try:
                        body_text = page.locator("body").inner_text(timeout=5_000)
                    except Exception:
                        body_text = ""
                    overflow = bool(page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 4"))
                    mojibake = [marker for marker in MOJIBAKE_MARKERS if marker in body_text]
                    missing = [needle for needle in route["must_contain"] if needle not in body_text]
                    forbidden = [needle for needle in route.get("forbidden_text", []) if needle in body_text]
                    next_error = [marker for marker in NEXT_ERROR_MARKERS if marker in body_text]
                    expected_final_path = route.get("expected_final_path", route.get("path"))
                    final_url_ok = path_from_url(final_url) == expected_final_path
                    visible_buttons = [text.strip() for text in page.locator("button").all_inner_texts()]
                    internal_links = sorted(set(page.locator('a[href^="/"]').evaluate_all("els => els.map(a => a.getAttribute('href'))")))
                    ok = status is not None and 200 <= status < 400 and final_url_ok and file_path.exists() and file_path.stat().st_size > 0 and bool(title.strip()) and not mojibake and not missing and not forbidden and not next_error and not overflow
                    details = {
                        "initial_url": initial_url,
                        "final_url": final_url,
                        "expected_final_path": expected_final_path,
                        "final_url_ok": final_url_ok,
                        "viewport": viewport_name,
                        "screenshot": str(file_path.relative_to(ROOT)),
                        "h1": title.strip(),
                        "h1_present": bool(title.strip()),
                        "missing_text": missing,
                        "forbidden_text_present": forbidden,
                        "mojibake_markers": mojibake,
                        "next_error_markers": next_error,
                        "horizontal_overflow": overflow,
                        "visible_buttons": visible_buttons,
                        "internal_links": internal_links,
                        "console_errors": console_errors[-10:],
                        "bytes": file_path.stat().st_size if file_path.exists() else 0,
                        "classification": "PASS" if ok else "HARD_FAIL",
                    }
                    results.append(CheckResult(f"{viewport_name}-{route['name']}", route["path"], str(status), ok, int((time.perf_counter() - start) * 1000), details))
                    if route["path"] in VISUAL_MAIN_ROUTES:
                        visual_lines.append(f"- {viewport_name} {route['path']} -> {'PASS' if ok else 'HARD_FAIL'} | final={final_url} | h1={title.strip()} | screenshot={details['screenshot']}")
                except Exception as error:  # noqa: BLE001
                    results.append(CheckResult(f"{viewport_name}-{route['name']}", route["path"], "screenshot_error", False, int((time.perf_counter() - start) * 1000), {"initial_url": initial_url, "error": str(error), "classification": "HARD_FAIL"}))
            page.close()
        browser.close()
    visual_lines.extend(["", "## Classification", "- Automated screenshot capture: PASS if all rows above are PASS.", "- Editorial visual tone and subtle overlap/aesthetic judgment: MANUAL_REVIEW_REQUIRED.", "- This manual review flag is not treated as an automated PASS claim.", ""])
    visual_summary = ROOT / "docs" / "auto-execute" / "summaries" / "visual-smoke.md"
    visual_summary.parent.mkdir(parents=True, exist_ok=True)
    visual_summary.write_text("\n".join(visual_lines), encoding="utf-8")
    return results


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:3021")
    parser.add_argument("--routes", action="store_true")
    parser.add_argument("--api", action="store_true")
    parser.add_argument("--screenshots", action="store_true")
    parser.add_argument("--integration", action="store_true")
    parser.add_argument("--python-commands", action="store_true")
    parser.add_argument("--api-timeout", type=int, default=180)
    args = parser.parse_args()

    if not (args.routes or args.api or args.screenshots or args.integration or args.python_commands):
        args.routes = args.api = args.screenshots = args.integration = args.python_commands = True

    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)

    exit_ok = True
    latest_date = discover_latest_date(args.base_url)
    summary: dict[str, Any] = {"base_url": args.base_url, "latest_date": latest_date, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}

    if args.routes:
        routes = run_route_smoke(args.base_url, latest_date)
        write_json(TEST_RESULTS / "route-smoke.json", [asdict(item) for item in routes])
        summary["routes"] = {"ok": all(item.ok for item in routes), "count": len(routes), "unique_routes": len(ROUTES)}
        exit_ok = exit_ok and all(item.ok for item in routes)

    if args.api:
        apis = run_api_smoke(args.base_url, args.api_timeout, latest_date)
        write_json(TEST_RESULTS / "api-smoke.json", [asdict(item) for item in apis])
        summary["apis"] = {"ok": all(item.ok for item in apis), "count": len(apis), "unique_api_routes": len({case["path"].split("?")[0] for case in API_CASES})}
        exit_ok = exit_ok and all(item.ok for item in apis)

    if args.integration:
        integration = run_integration_smoke(args.base_url, latest_date)
        write_json(TEST_RESULTS / "integration-smoke.json", [asdict(item) for item in integration])
        summary["integration"] = {"ok": all(item.ok for item in integration), "count": len(integration)}
        exit_ok = exit_ok and all(item.ok for item in integration)

    if args.python_commands:
        commands = run_python_command_smoke()
        write_json(TEST_RESULTS / "python-command-smoke.json", [asdict(item) for item in commands])
        summary["python_commands"] = {"ok": all(item.ok for item in commands), "count": len(commands)}
        exit_ok = exit_ok and all(item.ok for item in commands)

    if args.screenshots:
        screenshots = capture_screenshots(args.base_url, latest_date)
        write_json(TEST_RESULTS / "screenshot-capture.json", [asdict(item) for item in screenshots])
        summary["screenshots"] = {"ok": all(item.ok for item in screenshots), "count": len(screenshots)}
        exit_ok = exit_ok and all(item.ok for item in screenshots)

    write_json(TEST_RESULTS / "full-acceptance-smoke-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if exit_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
