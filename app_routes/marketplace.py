"""Marketplace route: /app/marketplace — browse fundable invoices."""

from __future__ import annotations

from fasthtml.common import Div, H3, P, Span, A, Article, Ul, Li, Table, Thead, Tbody, Tr, Th, Td, NotStr

from app import rt
from utils.i18n import t, get_lang
from landing.components import page, Eyebrow, Heading, Section_, Pill

try:
    from db import fetch_all
    _HAS_DB = True
except Exception:
    _HAS_DB = False


def _load_marketplace() -> list[dict]:
    if not _HAS_DB:
        return []
    try:
        return fetch_all("""
            SELECT
                f.id AS funding_id,
                i.invoice_number,
                i.debtor_name,
                i.sector,
                i.amount AS invoice_amount,
                i.currency,
                i.due_date,
                i.risk_grade,
                f.funding_goal,
                f.amount_raised,
                f.advance_rate_pct,
                f.fee_pct_per_30d,
                f.estimated_return_pct,
                f.target_hold_days,
                c.name AS seller_company
            FROM factorfinance.invoice_funding f
            JOIN factorfinance.invoices i ON i.id = f.invoice_id
            JOIN factorfinance.companies c ON c.id = i.company_id
            WHERE f.funding_status = 'open' AND f.show_in_marketplace = TRUE
            ORDER BY f.created_at DESC
        """)
    except Exception:
        return []


def _risk_color(grade: str) -> str:
    return {"A": "text-green-700", "B": "text-accent", "C": "text-yellow-700", "D": "text-red-700"}.get(grade, "text-ink-muted")


def _progress_pct(raised: float, goal: float) -> int:
    if not goal:
        return 0
    return min(100, int((raised / goal) * 100))


def _cur(currency: str, amount: float) -> str:
    sym = {"EUR": "€", "UZS": "UZS ", "USD": "$", "GBP": "£"}.get(currency, currency + " ")
    return f"{sym}{amount:,.0f}"


def _invoice_card(row: dict, lang: str):
    pct = _progress_pct(float(row["amount_raised"]), float(row["funding_goal"]))
    cur = row["currency"]
    return Article(
        Div(
            Span(row["sector"].title(), cls="font-mono text-[11px] tracking-widest uppercase text-ink-dim"),
            Span(row["risk_grade"], cls=f"font-mono text-sm font-medium {_risk_color(row['risk_grade'])}"),
            cls="flex items-center justify-between mb-4",
        ),
        H3(row["debtor_name"], cls="text-ink text-lg font-medium mb-1"),
        P(f"{t('mkt_seller', lang)}: {row['seller_company']}", cls="text-ink-muted text-sm mb-4"),
        Div(
            Div(
                Span(_cur(cur, float(row["invoice_amount"])), cls="text-ink font-medium"),
                Span(f" {t('mkt_invoice', lang)}", cls="text-ink-muted text-sm"),
                cls="mb-2",
            ),
            Div(
                Div(cls="h-2 rounded-full bg-accent", style=f"width: {pct}%"),
                cls="h-2 rounded-full bg-line overflow-hidden mb-2",
            ),
            Div(
                Span(f"{pct}% {t('mkt_funded', lang)}", cls="text-ink-muted text-xs"),
                Span(f"{row['target_hold_days']}d {t('mkt_term', lang)}", cls="text-ink-muted text-xs"),
                cls="flex justify-between",
            ),
            cls="mb-4",
        ),
        Div(
            Div(
                P(t("mkt_advance", lang), cls="text-[10px] font-mono uppercase text-ink-dim"),
                P(f"{float(row['advance_rate_pct']):.0f}%", cls="text-ink font-medium"),
            ),
            Div(
                P(t("mkt_fee", lang), cls="text-[10px] font-mono uppercase text-ink-dim"),
                P(f"{float(row['fee_pct_per_30d']):.1f}%", cls="text-ink font-medium"),
            ),
            Div(
                P(t("mkt_est_return", lang), cls="text-[10px] font-mono uppercase text-ink-dim"),
                P(f"{float(row['estimated_return_pct']):.1f}%", cls="text-accent font-medium"),
            ),
            cls="grid grid-cols-3 gap-3 mb-5",
        ),
        A(NotStr(t("mkt_invest", lang) + " &rarr;"), href=f"/app/marketplace/{row['funding_id']}",
          cls="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium bg-accent text-bg hover:bg-ink transition-all"),
        cls="p-6 rounded-2xl bg-bg-elevated border border-line hover:border-accent/50 transition-colors",
    )


@rt("/app/marketplace")
def marketplace(req):
    lang = get_lang(req)
    listings = _load_marketplace()

    empty = Div(
        P(t("mkt_empty", lang), cls="text-ink-muted text-lg"),
        cls="py-12 text-center",
    ) if not listings else None

    grid = Div(
        *[_invoice_card(r, lang) for r in listings],
        cls="grid sm:grid-cols-2 lg:grid-cols-3 gap-4",
    ) if listings else None

    return page(
        t("mkt_eyebrow", lang),
        Section_(
            Eyebrow(t("mkt_eyebrow", lang)),
            Heading(1, t("mkt_h1", lang), cls="mt-4 max-w-4xl"),
            P(f"{len(listings)} {t('mkt_count', lang)}.",
              cls="mt-4 text-ink-muted text-lg"),
            cls="border-t border-line",
        ),
        Section_(grid or empty, cls="border-t border-line"),
        current_path="/app/marketplace",
        lang=lang,
    )


@rt("/app/marketplace/{funding_id}")
def marketplace_detail(req, funding_id: int):
    lang = get_lang(req)
    if not _HAS_DB:
        return page("Not found", Section_(P("Database not configured.")), current_path="/app/marketplace", lang=lang)

    try:
        row = fetch_all("""
            SELECT
                f.*, i.invoice_number, i.debtor_name, i.debtor_registration,
                i.description, i.sector, i.amount AS invoice_amount, i.currency,
                i.issue_date, i.due_date, i.payment_terms_days, i.risk_grade,
                c.name AS seller_company, c.registration_number AS seller_reg,
                c.sector AS seller_sector, c.country AS seller_country
            FROM factorfinance.invoice_funding f
            JOIN factorfinance.invoices i ON i.id = f.invoice_id
            JOIN factorfinance.companies c ON c.id = i.company_id
            WHERE f.id = %s
        """, (funding_id,))
    except Exception:
        row = []

    if not row:
        return page("Not found", Section_(
            Heading(1, "Invoice not found.", cls="mt-4"),
        ), current_path="/app/marketplace", lang=lang)

    r = row[0]
    pct = _progress_pct(float(r["amount_raised"]), float(r["funding_goal"]))
    cur = r["currency"]

    def _detail(label, value):
        return Div(
            P(label, cls="text-[10px] font-mono uppercase tracking-widest text-ink-dim mb-1"),
            P(str(value), cls="text-ink font-medium"),
        )

    return page(
        f"{r['debtor_name']}",
        Section_(
            A(NotStr("&larr; " + t("mkt_back", lang)), href="/app/marketplace", cls="text-ink-dim text-xs hover:text-accent mb-6 inline-block"),
            Div(
                Span(r["risk_grade"], cls=f"text-2xl font-medium {_risk_color(r['risk_grade'])} mr-3"),
                Span(r["sector"].title(), cls="font-mono text-[11px] tracking-widest uppercase text-ink-dim"),
                cls="flex items-center mb-4",
            ),
            Heading(1, r["debtor_name"], cls="max-w-4xl"),
            P(f"Invoice #{r['invoice_number']} · {t('mkt_seller', lang)}: {r['seller_company']} ({r['seller_country']})",
              cls="mt-3 text-ink-muted text-lg"),
            cls="border-t border-line",
        ),
        Section_(
            Div(
                Div(
                    Div(
                        Div(cls="h-3 rounded-full bg-accent", style=f"width: {pct}%"),
                        cls="h-3 rounded-full bg-line overflow-hidden mb-3",
                    ),
                    Div(
                        Span(f"{_cur(cur, float(r['amount_raised']))} raised", cls="text-ink font-medium"),
                        Span(f"of {_cur(cur, float(r['funding_goal']))} goal", cls="text-ink-muted text-sm ml-2"),
                        cls="mb-8",
                    ),
                    Div(
                        _detail(t("mkt_invoice", lang).title(), _cur(cur, float(r["invoice_amount"]))),
                        _detail(t("mkt_advance", lang), f"{float(r['advance_rate_pct']):.0f}%"),
                        _detail(t("mkt_fee", lang), f"{float(r['fee_pct_per_30d']):.1f}%"),
                        _detail(t("mkt_est_return", lang), f"{float(r['estimated_return_pct']):.1f}%"),
                        cls="grid grid-cols-2 md:grid-cols-4 gap-6",
                    ),
                    cls="md:col-span-2",
                ),
                Div(
                    Div(
                        _detail(t("port_debtor", lang), r["debtor_name"]),
                        _detail(t("mkt_seller", lang), r["seller_company"]),
                        _detail(t("port_grade", lang), r["risk_grade"]),
                        _detail(t("port_due", lang), str(r["due_date"])),
                        cls="grid grid-cols-2 gap-4",
                    ),
                    cls="p-6 rounded-2xl bg-bg-elevated border border-line",
                ),
                cls="grid md:grid-cols-3 gap-8",
            ),
            cls="border-t border-line",
        ),
        current_path="/app/marketplace",
        lang=lang,
    )
