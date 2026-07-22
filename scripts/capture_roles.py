"""Capture role-scoped screens (in the left-nav cockpit) for the 4 role guides.

Produces docs/img/role-<role>-<name>.png at 1440x900 for:
  investor · supplier · payer · admin (back office) + workspace modules.

    FF_URL=http://localhost:5082 FF_INVESTOR=30 python -m scripts.capture_roles
"""

from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img"
BASE = os.environ.get("FF_URL", "http://localhost:5082")
INVESTOR = os.environ.get("FF_INVESTOR", "30")
LANG = os.environ.get("FF_LANG", "en")  # set FF_LANG=ru for localized captures
VP = {"width": 1440, "height": 900}

# Output prefix: EN keeps the historical `role-<role>-<name>.png`; other langs
# get `role-<lang>-<role>-<name>.png` so both coexist.
_PREFIX = "role-" if LANG == "en" else f"role-{LANG}-"

# role -> cookies, [(name, path or None-for-detail)]
PLANS = {
    "investor": (
        {"role": "investor", "investor": INVESTOR},
        [("chat", "/app"), ("dashboard", "/app/dashboard"), ("marketplace", "/app/marketplace"),
         ("detail", None), ("portfolio", "/app/portfolio"),
         ("statement", "/app/statement"), ("autoinvest", "/app/auto-invest"),
         ("reports", "/app/assistant")],
    ),
    "supplier": (
        {"role": "supplier"},
        [("applications", "/app/supplier"), ("triage", "/app/triage"),
         ("pdf", "/app/supplier", "a.pdf-view-btn")],
    ),
    "payer": (
        {"role": "payer"},
        [("confirm", "/app/payer"), ("pdf", "/app/payer", "a.pdf-view-btn")],
    ),
    "admin": (
        {"role": "admin", "admin_role": "super", "investor": INVESTOR},
        [("chat", "/app"), ("console", "/app/admin"), ("onboarding", "/app/admin/onboarding"),
         ("risk", "/app/admin/risk"),
         ("scoring", "/app/admin/scoring"),
         ("calibration", "/app/admin/scoring/calibration"), ("funding", "/app/admin/funding"),
         ("accounting", "/app/admin/accounting"),
         ("journal", "/app/admin/accounting/journal"),
         ("reconciliation", "/app/admin/accounting/reconciliation"),
         ("reports", "/app/admin/reports"), ("audit", "/app/admin/audit"),
         ("crm", "/app/crm"), ("drive", "/app/drive"),
         ("docs", "/app/docs"), ("mail", "/app/mail")],
    ),
}


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        for role, (cookies, screens) in PLANS.items():
            ctx = br.new_context(viewport=VP, device_scale_factor=1)
            cookie_map = {**cookies, "lang": LANG}
            ctx.add_cookies([{"name": k, "value": v, "url": BASE} for k, v in cookie_map.items()])
            pg = ctx.new_page()
            for screen in screens:
                name, path = screen[0], screen[1]
                click_sel = screen[2] if len(screen) > 2 else None
                if path is None:
                    pg.goto(BASE + "/app/marketplace", wait_until="networkidle", timeout=30_000)
                    href = pg.evaluate("() => { const a=document.querySelector('a[href*=\"/app/marketplace/\"]'); return a?a.getAttribute('href'):null; }")
                    if not href:
                        continue
                    path = href
                try:
                    pg.goto(BASE + path, wait_until="networkidle", timeout=30_000)
                except Exception:
                    pg.goto(BASE + path, wait_until="load", timeout=30_000)
                pg.wait_for_timeout(400)
                if click_sel:
                    try:
                        pg.click(click_sel, timeout=5_000)
                        pg.wait_for_timeout(3500)  # let pdf.js render + highlight
                    except Exception as e:
                        print(f"  click {click_sel} failed: {e}")
                out = IMG / f"{_PREFIX}{role}-{name}.png"
                pg.screenshot(path=str(out), full_page=False)
                print(f"[{LANG}·{role}] {out.relative_to(ROOT)}")
            ctx.close()
        br.close()
    print("done")


if __name__ == "__main__":
    main()
