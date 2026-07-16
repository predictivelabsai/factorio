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
VP = {"width": 1440, "height": 900}

# role -> cookies, [(name, path or None-for-detail)]
PLANS = {
    "investor": (
        {"role": "investor", "investor": INVESTOR},
        [("dashboard", "/app"), ("marketplace", "/app/marketplace"),
         ("detail", None), ("portfolio", "/app/portfolio"),
         ("statement", "/app/statement"), ("autoinvest", "/app/auto-invest"),
         ("reports", "/app/assistant")],
    ),
    "supplier": (
        {"role": "seller"},
        [("applications", "/app/seller"), ("triage", "/app/triage")],
    ),
    "payer": (
        {"role": "payer"},
        [("confirm", "/app/payer")],
    ),
    "admin": (
        {"role": "admin", "admin_role": "finance", "investor": INVESTOR},
        [("console", "/app/admin"), ("onboarding", "/app/admin/onboarding"),
         ("risk", "/app/admin/risk"), ("funding", "/app/admin/funding"),
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
            ctx.add_cookies([{"name": k, "value": v, "url": BASE} for k, v in cookies.items()])
            pg = ctx.new_page()
            for name, path in screens:
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
                out = IMG / f"role-{role}-{name}.png"
                pg.screenshot(path=str(out), full_page=False)
                print(f"[{role}] {out.relative_to(ROOT)}")
            ctx.close()
        br.close()
    print("done")


if __name__ == "__main__":
    main()
