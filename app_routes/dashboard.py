"""Dashboard route: /app — overview for logged-in users."""

from __future__ import annotations

from fasthtml.common import Div, H1, H2, H3, P, Span, A, Article, Section, NotStr

from app import rt
from utils.i18n import t, get_lang
from landing.components import page, Eyebrow, Heading, Section_, Button_

try:
    from db import fetch_one
    _HAS_DB = True
except Exception:
    _HAS_DB = False


def _stat_card(label: str, value: str, sub: str = ""):
    return Article(
        P(label, cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
        P(value, cls="text-3xl md:text-4xl font-medium tracking-tighter text-ink mb-1"),
        P(sub, cls="text-ink-muted text-sm") if sub else None,
        cls="p-7 rounded-2xl bg-bg-elevated border border-line",
    )


def _load_stats() -> dict:
    if not _HAS_DB:
        return {}
    try:
        row = fetch_one("""
            SELECT
                COALESCE(SUM(f.amount_raised), 0) AS total_funded,
                COUNT(DISTINCT i.id) AS total_invoices,
                COUNT(DISTINCT CASE WHEN i.status = 'funding' THEN i.id END) AS active_invoices,
                COUNT(DISTINCT inv.investor_id) AS total_investors
            FROM factorfinance.invoices i
            LEFT JOIN factorfinance.invoice_funding f ON f.invoice_id = i.id
            LEFT JOIN factorfinance.investments inv ON inv.funding_id = f.id
        """)
        return row or {}
    except Exception:
        return {}


@rt("/app")
def dashboard(req):
    lang = get_lang(req)
    stats = _load_stats()
    total_funded = stats.get("total_funded", 0)
    total_invoices = stats.get("total_invoices", 0)
    active_invoices = stats.get("active_invoices", 0)
    total_investors = stats.get("total_investors", 0)

    return page(
        t("dash_eyebrow", lang),
        Section_(
            Eyebrow(t("dash_eyebrow", lang)),
            Heading(1, t("dash_h1", lang), cls="mt-4 max-w-4xl"),
            P(t("dash_lede", lang), cls="mt-4 text-ink-muted text-lg max-w-3xl leading-relaxed"),
            cls="border-t border-line",
        ),
        Section_(
            Div(
                _stat_card(t("dash_total_funded", lang), f"UZS {total_funded:,.0f}", t("dash_total_submitted", lang)),
                _stat_card(t("dash_invoices", lang), str(total_invoices), t("dash_total_submitted", lang)),
                _stat_card(t("dash_active", lang), str(active_invoices), t("dash_seeking", lang)),
                _stat_card(t("dash_investors", lang), str(total_investors), t("dash_active_platform", lang)),
                cls="grid md:grid-cols-2 lg:grid-cols-4 gap-4",
            ),
            cls="border-t border-line",
        ),
        Section_(
            Div(
                A(NotStr(t("dash_browse", lang) + " &rarr;"), href="/app/marketplace",
                  cls="inline-flex items-center gap-2 px-5 py-3 rounded-full text-sm font-medium bg-accent text-bg hover:bg-ink transition-all"),
                A(NotStr(t("dash_portfolio", lang) + " &rarr;"), href="/app/portfolio",
                  cls="inline-flex items-center gap-2 px-5 py-3 rounded-full text-sm font-medium bg-transparent text-ink border border-line-bright hover:border-accent hover:text-accent transition-all"),
                cls="flex items-center gap-3 flex-wrap",
            ),
            cls="border-t border-line",
        ),
        current_path="/app",
        lang=lang,
    )
