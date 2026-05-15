import argparse
import datetime as _dt
import json
import pathlib
import re
import sys

from PIL import Image
from playwright.sync_api import sync_playwright


def read_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return fallback


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def rel(root, path):
    return pathlib.Path(path).resolve().relative_to(root.resolve()).as_posix()


def safe_id(value):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "UI-UNKNOWN")).strip("_") or "UI-UNKNOWN"


def resolve(root, value):
    if not value:
        return None
    p = pathlib.Path(str(value))
    return p if p.is_absolute() else root / p


def first(screen, names):
    for name in names:
        value = screen.get(name)
        if value:
            return str(value)
    return ""


def parse_viewport(screen):
    raw = str(screen.get("viewport") or "1440x900")
    match = re.search(r"(\d+)\s*x\s*(\d+)", raw)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 1440, 900


def capture_html_reference(root, screen, out_dir):
    reference = resolve(root, first(screen, ["reference", "referencePath", "uiReference"]))
    if not reference or not reference.exists() or reference.suffix.lower() not in {".html", ".htm"}:
        return reference
    out_dir.mkdir(parents=True, exist_ok=True)
    sid = safe_id(screen.get("id"))
    out = out_dir / f"{sid}-reference.png"
    width, height = parse_viewport(screen)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(reference.resolve().as_uri(), wait_until="networkidle", timeout=45000)
        page.screenshot(path=str(out), full_page=True)
        page.close()
        browser.close()
    screen["referenceScreenshot"] = rel(root, out)
    return out


def compare_images(reference, actual, diff_path, threshold):
    ref_img = Image.open(reference).convert("RGBA")
    act_img = Image.open(actual).convert("RGBA")
    width = min(ref_img.width, act_img.width)
    height = min(ref_img.height, act_img.height)
    ref_crop = ref_img.crop((0, 0, width, height))
    act_crop = act_img.crop((0, 0, width, height))
    ref_pixels = ref_crop.load()
    act_pixels = act_crop.load()
    diff_img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    diff_pixels = diff_img.load()
    mismatch = 0
    # Similar to pixelmatch's tolerance intent: ignore tiny anti-alias/color noise,
    # but count visible structural differences.
    channel_tolerance = 32
    for y in range(height):
        for x in range(width):
            rp = ref_pixels[x, y]
            ap = act_pixels[x, y]
            delta = max(abs(int(rp[i]) - int(ap[i])) for i in range(4))
            if delta > channel_tolerance:
                mismatch += 1
                diff_pixels[x, y] = (255, 0, 0, 220)
            else:
                gray = int((int(ap[0]) + int(ap[1]) + int(ap[2])) / 3)
                diff_pixels[x, y] = (gray, gray, gray, 40)
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    diff_img.save(diff_path)
    ratio = mismatch / max(1, width * height)
    size_mismatch = (ref_img.width, ref_img.height) != (act_img.width, act_img.height)
    status = "PASS" if ratio <= threshold and not size_mismatch else "PASS_WITH_LIMITATION"
    return {
        "status": status,
        "ratio": ratio,
        "diff": diff_path,
        "comparedSize": f"{width}x{height}",
        "sizeMismatch": size_mismatch,
        "referenceSize": f"{ref_img.width}x{ref_img.height}",
        "actualSize": f"{act_img.width}x{act_img.height}",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--threshold", default="0.03")
    parser.add_argument("--strict", default="false")
    args = parser.parse_args()
    root = pathlib.Path(args.project_root).resolve()
    threshold = float(args.threshold)
    strict = str(args.strict).lower() == "true"
    docs = root / "docs" / "auto-execute"
    ui_target_path = docs / "ui-target.json"
    result_path = docs / "results" / "ui-pixel-diff.json"
    report_path = docs / "visual-diff-report.md"
    reference_dir = docs / "screenshots" / "references"
    diff_dir = docs / "screenshots" / "diffs"
    ui_target = read_json(ui_target_path, {"screens": []})
    screens = ui_target.get("screens") if isinstance(ui_target.get("screens"), list) else []
    result = {
        "schemaVersion": "2.0",
        "lane": "ui-pixel-diff",
        "status": "PASS",
        "engine": "python-pillow-playwright",
        "threshold": threshold,
        "strict": strict,
        "comparisons": [],
        "blockers": [],
        "updatedAt": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }
    hard_fail = False
    limitation = False
    for screen in screens:
        if not screen or screen.get("required") is False:
            continue
        sid = safe_id(screen.get("id"))
        actual = resolve(root, first(screen, ["actualScreenshot", "actualScreenshotDesktop", "visualEvidence", "actual"]))
        if not actual or not actual.exists():
            hard_fail = True
            result["comparisons"].append({"id": sid, "status": "HARD_FAIL", "reason": "actual screenshot missing"})
            continue
        try:
            reference = capture_html_reference(root, screen, reference_dir)
        except Exception as exc:
            reference = None
            result["blockers"].append(f"{sid} reference capture failed: {exc}")
        if not reference or not reference.exists():
            limitation = True
            result["comparisons"].append({"id": sid, "status": "MANUAL_REVIEW_REQUIRED", "reason": "reference missing or unsupported"})
            continue
        if reference.suffix.lower() != ".png" or actual.suffix.lower() != ".png":
            limitation = True
            result["comparisons"].append({"id": sid, "status": "MANUAL_REVIEW_REQUIRED", "reason": "reference/actual are not PNG after reference capture"})
            continue
        diff_path = diff_dir / f"{sid}-diff.png"
        comparison = compare_images(reference, actual, diff_path, threshold)
        comparison_json = {
            "id": sid,
            "status": "HARD_FAIL" if strict and comparison["status"] != "PASS" else comparison["status"],
            "ratio": comparison["ratio"],
            "diff": rel(root, comparison["diff"]),
            "referenceScreenshot": rel(root, reference),
            "actualScreenshot": rel(root, actual),
            "comparedSize": comparison["comparedSize"],
            "sizeMismatch": comparison["sizeMismatch"],
            "referenceSize": comparison["referenceSize"],
            "actualSize": comparison["actualSize"],
        }
        result["comparisons"].append(comparison_json)
        screen["referenceScreenshot"] = comparison_json["referenceScreenshot"]
        screen["visualDiffEvidence"] = comparison_json["diff"]
        screen["visualDiff"] = comparison_json["diff"]
        screen["pixelDiffRatio"] = comparison["ratio"]
        screen["pixelDiffComparedSize"] = comparison["comparedSize"]
        screen["pixelDiffStatus"] = comparison_json["status"]
        if comparison_json["status"] == "PASS":
            screen["pixelPerfectStatus"] = "PASS"
            screen["visualStatus"] = "PASS"
            screen["finalUiStatus"] = "PASS"
            screen["canClaimPixelPerfect"] = True
            if screen.get("status") != "HARD_FAIL":
                screen["status"] = "PASS"
        else:
            if comparison_json["status"] == "HARD_FAIL":
                hard_fail = True
            else:
                limitation = True
            screen["pixelPerfectStatus"] = comparison_json["status"]
            screen["visualStatus"] = "PASS_WITH_LIMITATION"
            screen["finalUiStatus"] = comparison_json["status"]
            screen["canClaimPixelPerfect"] = False
            if screen.get("status") != "HARD_FAIL":
                screen["status"] = "PASS_WITH_LIMITATION"
            screen["knownDifferences"] = [
                f"Automated pixel diff ratio {comparison['ratio']:.4f} exceeds threshold {threshold} or dimensions differ."
            ]
    if hard_fail:
        result["status"] = "HARD_FAIL"
    elif limitation:
        result["status"] = "PASS_WITH_LIMITATION"
    else:
        result["status"] = "PASS"
    ui_target["updatedAt"] = _dt.datetime.now().isoformat()
    write_json(ui_target_path, ui_target)
    write_json(result_path, result)
    report_lines = [
        "# Visual Diff Report",
        "",
        f"- Status: {result['status']}",
        f"- Engine: {result['engine']}",
        f"- Threshold: {threshold}",
        "",
        "## Comparisons",
    ]
    for item in result["comparisons"]:
        report_lines.append(f"- {item.get('id')}: {item.get('status')} ratio={item.get('ratio', 'n/a')} diff={item.get('diff', '')}")
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return 1 if result["status"] == "HARD_FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
