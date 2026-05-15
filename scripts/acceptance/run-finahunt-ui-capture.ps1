param([string]$ProjectRoot = (Get-Location).Path, [int]$Port = 3000)
$ErrorActionPreference = 'Stop'
$web = Join-Path $ProjectRoot 'apps\web'
$docs = Join-Path $ProjectRoot 'docs\auto-execute'
$logs = Join-Path $docs 'logs'
$results = Join-Path $docs 'results'
$screenshots = Join-Path $docs 'screenshots'
New-Item -ItemType Directory -Force -Path $logs,$results,$screenshots | Out-Null
$base = "http://127.0.0.1:$Port"
$serverLog = Join-Path $logs 'ui-capture-next-start.log'
$proc = $null
try {
  $proc = Start-Process -FilePath 'npm.cmd' -ArgumentList @('run','start','--','-p',"$Port") -WorkingDirectory $web -RedirectStandardOutput $serverLog -RedirectStandardError (Join-Path $logs 'ui-capture-next-start.err.log') -PassThru -WindowStyle Hidden
  $ready = $false
  for ($i=0; $i -lt 45; $i++) {
    try { Invoke-WebRequest -Uri $base -UseBasicParsing -TimeoutSec 2 | Out-Null; $ready = $true; break } catch { Start-Sleep -Seconds 1 }
  }
  if (-not $ready) { throw "Next server did not become ready at $base" }
  $py = @"
import json, pathlib, sys, datetime
from playwright.sync_api import sync_playwright
root = pathlib.Path(sys.argv[1])
base = sys.argv[2].rstrip('/')
docs = root / 'docs' / 'auto-execute'
ui_target_path = docs / 'ui-target.json'
screenshot_dir = docs / 'screenshots'
result_path = docs / 'results' / 'ui-capture-python.json'
screenshot_dir.mkdir(parents=True, exist_ok=True)
target = json.loads(ui_target_path.read_text(encoding='utf-8-sig'))
screens = target.get('screens') or []
viewports = [('desktop', 1536, 900), ('mobile', 390, 844)]
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for screen in screens:
        route = screen.get('route') or '/'
        url = route if route.startswith('http') else base + route
        sid = ''.join(ch if ch.isalnum() or ch in '-_' else '_' for ch in str(screen.get('id') or 'screen'))
        ok = True
        for name, width, height in viewports:
            page = browser.new_page(viewport={'width': width, 'height': height})
            errors = []
            page.on('pageerror', lambda exc: errors.append(str(exc)))
            out = screenshot_dir / f'{sid}-{name}.png'
            try:
                page.goto(url, wait_until='networkidle', timeout=45000)
                text = page.locator('body').inner_text(timeout=5000)
                page.screenshot(path=str(out), full_page=True)
                passed = len(text.strip()) > 20 and not errors
            except Exception as exc:
                passed = False
                errors.append(str(exc))
            finally:
                page.close()
            rel = out.relative_to(root).as_posix()
            results.append({'id': screen.get('id'), 'route': route, 'viewport': name, 'screenshot': rel, 'status': 'PASS' if passed else 'HARD_FAIL', 'errors': errors[:5]})
            if passed:
                if name == 'desktop':
                    screen['actualScreenshot'] = rel
                    screen['actualScreenshotDesktop'] = rel
                    screen['visualEvidence'] = rel
                if name == 'mobile':
                    screen['actualScreenshotMobile'] = rel
            else:
                ok = False
        screen['structureStatus'] = 'PASS' if ok else 'HARD_FAIL'
        screen['screenshotStatus'] = 'PASS' if ok else 'HARD_FAIL'
        screen['visualStatus'] = 'PASS_WITH_LIMITATION' if ok else 'HARD_FAIL'
        screen['pixelPerfectStatus'] = 'MANUAL_REVIEW_REQUIRED'
        screen['canClaimPixelPerfect'] = False
        screen['status'] = 'PASS_WITH_LIMITATION' if ok else 'HARD_FAIL'
    browser.close()
target['updatedAt'] = datetime.datetime.now().isoformat()
ui_target_path.write_text(json.dumps(target, ensure_ascii=False, indent=2), encoding='utf-8')
status = 'PASS' if all(r['status'] == 'PASS' for r in results) else 'HARD_FAIL'
result_path.write_text(json.dumps({'lane':'ui-capture-python','status':status,'baseUrl':base,'screenshots':results}, ensure_ascii=False, indent=2), encoding='utf-8')
sys.exit(0 if status == 'PASS' else 1)
"@
  $tmp = Join-Path $env:TEMP 'finahunt_ui_capture.py'
  $py | Set-Content -Encoding UTF8 -LiteralPath $tmp
  python $tmp $ProjectRoot $base
  exit $LASTEXITCODE
} finally {
  if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}
