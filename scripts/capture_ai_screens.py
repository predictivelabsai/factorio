"""Capture the two AI assistant screens (triage + reporting) for the user guide.

Drives a real demo conversation in each language so the screenshot shows an
actual exchange, then saves 1440x900 viewport frames into docs/img/ using the
guide's naming convention:

    docs/img/<lang>-13-ai-triage.png
    docs/img/<lang>-14-ai-assistant.png

Usage (server must be running):
    FF_URL=http://localhost:5077 FF_INVESTOR=<id> python -m scripts.capture_ai_screens
"""

from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img"
BASE_URL = os.environ.get("FF_URL", "http://localhost:5077")
INVESTOR = os.environ.get("FF_INVESTOR", "")
VIEWPORT = {"width": 1440, "height": 900}

# Per-language demo prompts so each screenshot reads naturally in its language.
DEMOS = {
    "en": {
        "triage": ("We invoiced Artel LLC for UZS 480,000,000, issued today, due in 60 days. "
                   "It's on SoliqOnline and buyer-confirmed. Seller is Silk Road Textiles LLC."),
        "assistant": "What's my net annual return and which sector am I most exposed to?",
    },
    "ru": {
        "triage": ("Мы выставили счёт Artel LLC на 480 000 000 сум, выписан сегодня, срок 60 дней. "
                   "Счёт в SoliqOnline и подтверждён покупателем. Продавец — Silk Road Textiles LLC."),
        "assistant": "Какова моя чистая годовая доходность и в какой отрасли у меня наибольшая доля?",
    },
}

PAGES = [
    ("triage", "/app/triage", "13-ai-triage"),
    ("assistant", "/app/assistant", "14-ai-assistant"),
]


def _prime_cookies(page, lang: str) -> None:
    page.goto(BASE_URL + "/app", wait_until="domcontentloaded", timeout=30_000)
    page.evaluate(f"document.cookie='lang={lang};path=/;max-age=31536000;samesite=lax'")
    if INVESTOR:
        page.evaluate(f"document.cookie='investor={INVESTOR};path=/;max-age=31536000;samesite=lax'")


def _run_chat(page, kind: str, path: str, message: str) -> None:
    page.goto(BASE_URL + path, wait_until="networkidle", timeout=30_000)
    page.fill("textarea[name='message']", message)
    page.click("button[type='submit']")
    # greeting bubble = 1; after a full exchange = 3 (greeting, user, assistant)
    page.wait_for_function(
        "document.querySelectorAll('.whitespace-pre-wrap').length >= 3",
        timeout=90_000,
    )
    page.wait_for_timeout(800)  # let layout settle
    # bring the chat exchange (question + AI reply) into the frame, not the hero
    page.evaluate(
        "const el=document.querySelector('#chat-%s');"
        "if(el){const y=el.getBoundingClientRect().top+window.scrollY-96;"
        "window.scrollTo(0,y);}" % kind
    )
    page.wait_for_timeout(400)


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
        page = ctx.new_page()
        for lang in ("en", "ru"):
            _prime_cookies(page, lang)
            for kind, path, slug in PAGES:
                print(f"[{lang}] {path}")
                _run_chat(page, kind, path, DEMOS[lang][kind])
                out = IMG / f"{lang}-{slug}.png"
                page.screenshot(path=str(out), full_page=False)
                print(f"  saved {out.relative_to(ROOT)}")
        browser.close()
    print("done")


if __name__ == "__main__":
    main()
