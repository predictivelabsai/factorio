"""Portfolio route: /app/portfolio — investor positions and returns."""

from __future__ import annotations

from fasthtml.common import Div, H3, P, Span, A, Article, Table, Thead, Tbody, Tr, Th, Td

from app import rt
from utils.i18n import t, get_lang
from landing.components import page, Eyebrow, Heading, Section_

try:
    from db import fetch_all
    _HAS_DB = True
except Exception:
    _HAS_DB = False


def _load_portfolio() -> list[dict]:
    if not _HAS_DB:
        return []
    try:
        return fetch_all("""
            SELECT
                inv.id AS investment_id,
                inv.investment_amount,
                inv.ownership_pct,
                inv.expected_return_amount,
                inv.status,
                inv.investment_date,
                i.invoice_number,
                i.debtor_name,
                i.sector,
                i.currency,
                i.due_date,
                i.risk_grade,
                c.name AS seller_company
            FROM factorfinance.investments inv
            JOIN factorfinance.invoice_funding f ON f.id = inv.funding_id
            JOIN factorfinance.invoices i ON i.id = f.invoice_id
            JOIN factorfinance.companies c ON c.id = i.company_id
            ORDER BY inv.investment_date DESC
        """)
    except Exception:
        return []


def _status_badge(status: str):
    colors = {
        "pending": "bg-yellow-100 text-yellow-800",
        "confirmed": "bg-green-100 text-green-800",
        "settled": "bg-blue-100 text-blue-800",
        "defaulted": "bg-red-100 text-red-800",
    }
    return Span(status.title(), cls=f"px-2 py-0.5 rounded-full text-xs font-medium {colors.get(status, 'bg-gray-100 text-gray-800')}")


@rt("/app/portfolio")
def portfolio(req):
    lang = get_lang(req)
    positions = _load_portfolio()
    total_invested = sum(float(p["investment_amount"]) for p in positions)
    total_expected = sum(float(p["expected_return_amount"]) for p in positions)
    active = [p for p in positions if p["status"] in ("pending", "confirmed")]

    stats = Div(
        Article(
            P(t("port_total_invested", lang), cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
            P(f"UZS {total_invested:,.0f}", cls="text-3xl font-medium tracking-tighter text-ink"),
            cls="p-7 rounded-2xl bg-bg-elevated border border-line",
        ),
        Article(
            P(t("port_expected", lang), cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
            P(f"UZS {total_expected:,.0f}", cls="text-3xl font-medium tracking-tighter text-accent"),
            cls="p-7 rounded-2xl bg-bg-elevated border border-line",
        ),
        Article(
            P(t("port_active", lang), cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
            P(str(len(active)), cls="text-3xl font-medium tracking-tighter text-ink"),
            cls="p-7 rounded-2xl bg-bg-elevated border border-line",
        ),
        Article(
            P(t("port_total", lang), cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
            P(str(len(positions)), cls="text-3xl font-medium tracking-tighter text-ink"),
            cls="p-7 rounded-2xl bg-bg-elevated border border-line",
        ),
        cls="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-10",
    )

    if not positions:
        empty = Div(
            P(t("port_empty", lang), cls="text-ink-muted text-lg"),
            P(A(t("footer_marketplace", lang), href="/app/marketplace", cls="text-accent underline"), cls="text-ink-muted mt-2"),
            cls="py-12 text-center",
        )
        return page(
            t("port_eyebrow", lang),
            Section_(Eyebrow(t("port_eyebrow", lang)), Heading(1, t("port_h1", lang), cls="mt-4 max-w-4xl"), cls="border-t border-line"),
            Section_(stats, empty, cls="border-t border-line"),
            current_path="/app/portfolio", lang=lang,
        )

    table = Div(
        Table(
            Thead(
                Tr(
                    Th(t("port_invoice", lang), cls="text-left text-[11px] font-mono tracking-widest uppercase text-ink-dim py-3 px-4"),
                    Th(t("port_debtor", lang), cls="text-left text-[11px] font-mono tracking-widest uppercase text-ink-dim py-3 px-4"),
                    Th(t("port_invested", lang), cls="text-right text-[11px] font-mono tracking-widest uppercase text-ink-dim py-3 px-4"),
                    Th(t("port_expected_col", lang), cls="text-right text-[11px] font-mono tracking-widest uppercase text-ink-dim py-3 px-4"),
                    Th(t("port_due", lang), cls="text-left text-[11px] font-mono tracking-widest uppercase text-ink-dim py-3 px-4"),
                    Th(t("port_grade", lang), cls="text-center text-[11px] font-mono tracking-widest uppercase text-ink-dim py-3 px-4"),
                    Th(t("port_status", lang), cls="text-center text-[11px] font-mono tracking-widest uppercase text-ink-dim py-3 px-4"),
                    cls="border-b border-line",
                ),
            ),
            Tbody(
                *[Tr(
                    Td(p["invoice_number"], cls="py-3 px-4 text-sm text-ink"),
                    Td(p["debtor_name"], cls="py-3 px-4 text-sm text-ink"),
                    Td(f"UZS {float(p['investment_amount']):,.0f}", cls="py-3 px-4 text-sm text-ink text-right"),
                    Td(f"UZS {float(p['expected_return_amount']):,.0f}", cls="py-3 px-4 text-sm text-accent text-right"),
                    Td(str(p["due_date"]), cls="py-3 px-4 text-sm text-ink-muted"),
                    Td(p["risk_grade"], cls="py-3 px-4 text-sm text-center font-medium"),
                    Td(_status_badge(p["status"]), cls="py-3 px-4 text-center"),
                    cls="border-b border-line hover:bg-bg-raised/50",
                ) for p in positions],
            ),
            cls="w-full",
        ),
        cls="rounded-2xl bg-bg-elevated border border-line overflow-hidden",
    )

    return page(
        t("port_eyebrow", lang),
        Section_(Eyebrow(t("port_eyebrow", lang)), Heading(1, t("port_h1", lang), cls="mt-4 max-w-4xl"), cls="border-t border-line"),
        Section_(stats, table, cls="border-t border-line"),
        current_path="/app/portfolio",
        lang=lang,
    )
