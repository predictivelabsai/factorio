"""Back-office admin console + role-scoped pages (demo-grade RBAC).

Roles: investor / seller / payer / admin. Admin has sub-roles (ops, credit,
collections, finance, compliance, exec, super) that scope actions — e.g.
**segregation of duties**: only Finance / Super may release funding, and only
Credit / Compliance / Super may set limits.

Every state-changing action is written to an **audit log**
(`factorio.audit_log`, created lazily). This is a demo: actions log and confirm
rather than mutating synthetic data destructively.
"""

from __future__ import annotations

from datetime import date, datetime

from fasthtml.common import (
    Div, P, Span, A, Article, Table, Thead, Tbody, Tr, Th, Td, NotStr, Titled,
)
from starlette.responses import RedirectResponse

from app import rt
from utils.i18n import t, get_lang
from landing.components import Eyebrow, Heading, Section_
from app_routes._shared import (
    app_page, fmt_uzs, current_role, current_subrole, ADMIN_SUBROLES,
)

try:
    from db import fetch_all, fetch_one, execute
    _HAS_DB = True
except Exception:  # pragma: no cover
    _HAS_DB = False

# Which sub-roles may perform which sensitive actions (segregation of duties).
CAN_APPROVE_FUNDING = {"finance", "super"}
CAN_SET_LIMITS = {"credit", "compliance", "super"}


# ── Audit log ─────────────────────────────────────────────────────────────

def _ensure_audit():
    if not _HAS_DB:
        return
    try:
        execute("""
            CREATE TABLE IF NOT EXISTS factorio.audit_log (
                id BIGSERIAL PRIMARY KEY,
                actor TEXT NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                entity TEXT NOT NULL DEFAULT '',
                detail TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
    except Exception:
        pass


def log_action(role: str, subrole: str, action: str, entity: str = "", detail: str = ""):
    _ensure_audit()
    if not _HAS_DB:
        return
    try:
        actor = f"admin:{subrole}" if role == "admin" else role
        execute("INSERT INTO factorio.audit_log (actor, role, action, entity, detail) "
                "VALUES (%(a)s, %(r)s, %(ac)s, %(e)s, %(d)s)",
                {"a": actor, "r": role, "ac": action, "e": entity, "d": detail})
    except Exception:
        pass


def _audit_rows(limit: int = 40) -> list[dict]:
    _ensure_audit()
    if not _HAS_DB:
        return []
    try:
        rows = fetch_all("SELECT actor, role, action, entity, detail, created_at "
                         "FROM factorio.audit_log ORDER BY created_at DESC LIMIT %(n)s", {"n": limit})
        if not rows:  # seed a few illustrative entries the first time
            for a, r, ac, e in [
                ("admin:credit", "admin", "score.assign", "invoice INV-20260012"),
                ("admin:finance", "admin", "funding.release", "funding #14"),
                ("admin:compliance", "admin", "kyc.approve", "company Artel LLC"),
                ("admin:collections", "admin", "dunning.send", "invoice INV-20260007"),
            ]:
                log_action("admin", a.split(":")[1], ac, e, "seed")
            rows = fetch_all("SELECT actor, role, action, entity, detail, created_at "
                             "FROM factorio.audit_log ORDER BY created_at DESC LIMIT %(n)s", {"n": limit})
        return rows
    except Exception:
        return []


# ── shared UI ───────────────────────────────────────────────────────────

_TH = "text-left text-[11px] font-mono tracking-widest uppercase text-ink-dim py-3 px-4"
_TD = "py-3 px-4 text-sm text-ink"
_TDR = _TD + " text-right"


def _guard(req):
    """Only the admin role reaches /app/admin/*; others get bounced to /app."""
    if current_role(req) != "admin":
        return RedirectResponse("/app", status_code=303)
    return None


def _card(label, value, sub=""):
    return Article(
        P(label, cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
        P(value, cls="text-3xl md:text-4xl font-medium tracking-tighter text-ink mb-1"),
        P(sub, cls="text-ink-muted text-sm") if sub else None,
        cls="p-7 rounded-2xl bg-bg-elevated border border-line",
    )


def _table(headers, rows):
    return Div(Table(
        Thead(Tr(*[Th(h, cls=_TH) for h in headers], cls="border-b border-line")),
        Tbody(*rows),
        cls="w-full",
    ), cls="rounded-2xl bg-bg-elevated border border-line overflow-hidden overflow-x-auto")


def _admin_page(req, current_path, title_key, *content):
    lang = get_lang(req)
    return app_page(
        t(title_key, lang),
        Section_(Eyebrow(t("admin_eyebrow", lang)),
                 Heading(1, t(title_key, lang), cls="mt-4 max-w-4xl"),
                 P(t("admin_lede", lang), cls="mt-4 text-ink-muted text-lg max-w-3xl leading-relaxed"),
                 cls="border-t border-line"),
        Section_(*content, cls="border-t border-line"),
        current_path=current_path, lang=lang,
        role="admin", subrole=current_subrole(req),
    )


def _q(sql, params=None, one=False):
    if not _HAS_DB:
        return None if one else []
    try:
        return (fetch_one if one else fetch_all)(sql, params or {})
    except Exception:
        return None if one else []


# ── Console ───────────────────────────────────────────────────────────────

@rt("/app/admin")
def admin_console(req):
    g = _guard(req)
    if g:
        return g
    lang = get_lang(req)
    stats = _q("""
        SELECT COUNT(DISTINCT c.id) AS clients,
               COUNT(DISTINCT i.id) AS invoices,
               COALESCE(SUM(f.amount_raised),0) AS funded,
               COUNT(DISTINCT CASE WHEN i.status='funding' THEN i.id END) AS active,
               COUNT(DISTINCT CASE WHEN i.status='defaulted' THEN i.id END) AS defaulted
        FROM factorio.companies c
        LEFT JOIN factorio.invoices i ON i.company_id = c.id
        LEFT JOIN factorio.invoice_funding f ON f.invoice_id = i.id
    """, one=True) or {}
    kpis = Div(
        _card(t("nav_admin_onboarding", lang), str(stats.get("clients", 0)), "clients & debtors"),
        _card("Invoices", str(stats.get("invoices", 0)), "in the book"),
        _card("Funded volume", fmt_uzs(stats.get("funded", 0)), "financed to date"),
        _card(t("nav_admin_risk", lang), str(stats.get("active", 0)), "active exposures"),
        cls="grid md:grid-cols-2 lg:grid-cols-4 gap-4",
    )
    mods = [
        ("nav_admin_onboarding", "/app/admin/onboarding", "Clients, debtors, KYC & facility limits"),
        ("nav_admin_risk", "/app/admin/risk", "Scoring, exposure, aging, fraud checks"),
        ("nav_admin_funding", "/app/admin/funding", "Approvals (SoD), disbursement, collections"),
        ("nav_admin_reports", "/app/admin/reports", "DSO, recovery, default, portfolio"),
        ("Accounting", "/app/admin/accounting", "Double-entry ledger, trial balance, reconciliation"),
        ("nav_admin_audit", "/app/admin/audit", "Every action, immutable"),
    ]
    cards = Div(*[
        A(Div(P(t(k, lang), cls="text-ink text-lg font-medium mb-1"),
              P(desc, cls="text-ink-muted text-sm")),
          href=href, cls="block p-6 rounded-2xl bg-bg-elevated border border-line hover:border-accent transition-colors")
        for k, href, desc in mods
    ], cls="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4")
    return _admin_page(req, "/app/admin", "admin_h1",
                       kpis, Div(cards, cls="mt-2"))


# ── Onboarding & limits ─────────────────────────────────────────────────

@rt("/app/admin/onboarding")
def admin_onboarding(req):
    g = _guard(req)
    if g:
        return g
    subrole = current_subrole(req)
    companies = _q("""
        SELECT c.name, c.sector, c.country, c.registration_number, c.annual_turnover,
               COUNT(i.id) AS n_invoices
        FROM factorio.companies c
        LEFT JOIN factorio.invoices i ON i.company_id = c.id
        GROUP BY c.id ORDER BY c.annual_turnover DESC LIMIT 40
    """)
    rows = []
    for idx, c in enumerate(companies):
        # demo KYC + facility limit derived from turnover
        kyc = "Approved" if idx % 5 else "Pending"
        limit = float(c["annual_turnover"] or 0) * 0.15
        badge = ("bg-green-100 text-green-800" if kyc == "Approved" else "bg-yellow-100 text-yellow-800")
        rows.append(Tr(
            Td(c["name"], cls=_TD),
            Td(c["sector"], cls=_TD),
            Td(c["country"], cls=_TD),
            Td(Span(kyc, cls=f"px-2 py-0.5 rounded-full text-xs font-medium {badge}"), cls="py-3 px-4"),
            Td(fmt_uzs(c["annual_turnover"]), cls=_TDR),
            Td(fmt_uzs(limit), cls=_TDR + " text-accent"),
            cls="border-b border-line",
        ))
    can_limits = subrole in CAN_SET_LIMITS
    note = P(("You may set facility limits (Credit / Compliance)." if can_limits
              else t("admin_restricted", get_lang(req))),
             cls="text-sm mt-4 " + ("text-ink-muted" if can_limits else "text-red-700"))
    return _admin_page(req, "/app/admin/onboarding", "nav_admin_onboarding",
                       _table(["Client / debtor", "Sector", "Country", "KYC", "Turnover", "Facility limit"], rows),
                       note)


# ── Risk & underwriting ─────────────────────────────────────────────────

@rt("/app/admin/risk")
def admin_risk(req):
    g = _guard(req)
    if g:
        return g
    by_sector = _q("""
        SELECT i.sector, COUNT(*) AS n, COALESCE(SUM(i.amount),0) AS exposure
        FROM factorio.invoices i WHERE i.status IN ('funding','funded')
        GROUP BY i.sector ORDER BY exposure DESC
    """)
    by_debtor = _q("""
        SELECT i.debtor_name, COUNT(*) AS n, COALESCE(SUM(i.amount),0) AS exposure
        FROM factorio.invoices i WHERE i.status IN ('funding','funded')
        GROUP BY i.debtor_name ORDER BY exposure DESC LIMIT 8
    """)
    grades = _q("SELECT risk_grade, COUNT(*) AS n FROM factorio.invoices GROUP BY risk_grade ORDER BY risk_grade")
    dupes = _q("""
        SELECT debtor_name, amount, COUNT(*) AS n FROM factorio.invoices
        GROUP BY debtor_name, amount HAVING COUNT(*) > 1 ORDER BY n DESC LIMIT 5
    """)
    sec_rows = [Tr(Td(r["sector"], cls=_TD), Td(str(r["n"]), cls=_TDR),
                   Td(fmt_uzs(r["exposure"]), cls=_TDR + " text-accent"), cls="border-b border-line")
                for r in by_sector]
    deb_rows = [Tr(Td(r["debtor_name"], cls=_TD), Td(str(r["n"]), cls=_TDR),
                   Td(fmt_uzs(r["exposure"]), cls=_TDR + " text-accent"), cls="border-b border-line")
                for r in by_debtor]
    grade_str = "  ·  ".join(f"{r['risk_grade']}: {r['n']}" for r in grades)
    fraud = (P("No duplicate-invoice signals in the current book.", cls="text-ink-muted text-sm")
             if not dupes else Div(*[
                 P(f"⚠ {r['n']}× {r['debtor_name']} @ {fmt_uzs(r['amount'])} — review for duplication",
                   cls="text-sm text-red-700") for r in dupes]))
    return _admin_page(req, "/app/admin/risk", "nav_admin_risk",
                       Div(P("Risk-grade distribution", cls="text-sm font-medium text-ink mb-2"),
                           P(grade_str, cls="text-ink-muted"), cls="mb-6"),
                       Div(P("Exposure by sector", cls="text-sm font-medium text-ink mb-3"),
                           _table(["Sector", "Invoices", "Exposure"], sec_rows), cls="mb-8"),
                       Div(P("Concentration — top debtors", cls="text-sm font-medium text-ink mb-3"),
                           _table(["Debtor", "Invoices", "Exposure"], deb_rows), cls="mb-8"),
                       Div(P("Fraud / duplicate-invoice check", cls="text-sm font-medium text-ink mb-3"), fraud))


# ── Funding + collections (with SoD) ────────────────────────────────────

@rt("/app/admin/funding")
def admin_funding(req):
    g = _guard(req)
    if g:
        return g
    lang = get_lang(req)
    subrole = current_subrole(req)
    pipeline = _q("""
        SELECT i.invoice_number, i.debtor_name, i.amount, i.risk_grade, i.status,
               f.advance_rate_pct, f.amount_raised, f.funding_goal
        FROM factorio.invoices i
        LEFT JOIN factorio.invoice_funding f ON f.invoice_id = i.id
        WHERE i.status IN ('verified','funding') ORDER BY i.amount DESC LIMIT 25
    """)
    can_approve = subrole in CAN_APPROVE_FUNDING
    rows = []
    for p in pipeline:
        adv = fmt_uzs(float(p["amount"] or 0) * float(p["advance_rate_pct"] or 85) / 100)
        action = (A("Approve & release", href=f"/app/admin/funding/approve?inv={p['invoice_number']}",
                    cls="text-xs px-3 py-1 rounded-full bg-accent text-bg hover:bg-ink")
                  if can_approve else Span("—", cls="text-ink-dim text-xs"))
        rows.append(Tr(
            Td(p["invoice_number"], cls=_TD), Td(p["debtor_name"], cls=_TD),
            Td(p["risk_grade"], cls="py-3 px-4 text-center text-sm"),
            Td(fmt_uzs(p["amount"]), cls=_TDR), Td(adv, cls=_TDR + " text-accent"),
            Td(p["status"], cls=_TD), Td(action, cls="py-3 px-4 text-right"),
            cls="border-b border-line"))
    overdue = _q("""
        SELECT invoice_number, debtor_name, amount, due_date
        FROM factorio.invoices WHERE status='funding' AND due_date < CURRENT_DATE
        ORDER BY due_date LIMIT 12
    """)
    coll_rows = [Tr(Td(r["invoice_number"], cls=_TD), Td(r["debtor_name"], cls=_TD),
                    Td(fmt_uzs(r["amount"]), cls=_TDR),
                    Td(str(r["due_date"]), cls=_TD + " text-red-700"),
                    Td(Span("Dunning · reminder 2", cls="text-xs text-ink-muted"), cls="py-3 px-4"),
                    cls="border-b border-line") for r in overdue]
    sod = P(("You may approve funding (Finance / Super)." if can_approve else t("admin_restricted", lang)),
            cls="text-sm mb-4 " + ("text-ink-muted" if can_approve else "text-red-700"))
    return _admin_page(req, "/app/admin/funding", "nav_admin_funding",
                       sod,
                       Div(P("Funding pipeline", cls="text-sm font-medium text-ink mb-3"),
                           _table(["Invoice", "Debtor", "Grade", "Amount", "Advance", "Status", "Action"], rows),
                           cls="mb-8"),
                       Div(P("Collections — overdue", cls="text-sm font-medium text-ink mb-3"),
                           _table(["Invoice", "Debtor", "Amount", "Due", "Stage"], coll_rows)))


@rt("/app/admin/funding/approve")
def admin_funding_approve(req, inv: str = ""):
    g = _guard(req)
    if g:
        return g
    lang = get_lang(req)
    subrole = current_subrole(req)
    if subrole not in CAN_APPROVE_FUNDING:
        msg = P(t("admin_restricted", lang), cls="text-red-700")
    else:
        log_action("admin", subrole, "funding.release", f"invoice {inv}", "approved via console")
        msg = P(NotStr(f"✔ Funding for <b>{inv}</b> approved and released. Action written to the audit log."),
                cls="text-ink")
    return _admin_page(req, "/app/admin/funding", "nav_admin_funding",
                       msg, P(A("← Back to funding", href="/app/admin/funding", cls="text-accent"), cls="mt-4"))


# ── Reports ─────────────────────────────────────────────────────────────

@rt("/app/admin/reports")
def admin_reports(req):
    g = _guard(req)
    if g:
        return g
    m = _q("""
        SELECT COUNT(*) FILTER (WHERE status='settled') AS settled,
               COUNT(*) FILTER (WHERE status='defaulted') AS defaulted,
               COUNT(*) AS total,
               COALESCE(AVG(CASE WHEN status='settled' THEN (settlement_date - investment_date) END),0) AS avg_hold
        FROM factorio.investments
    """, one=True) or {}
    total = float(m.get("total") or 0) or 1
    dr = 100 * float(m.get("defaulted") or 0) / total
    by_sector = _q("""
        SELECT i.sector, COALESCE(SUM(f.amount_raised),0) AS funded
        FROM factorio.invoices i JOIN factorio.invoice_funding f ON f.invoice_id=i.id
        GROUP BY i.sector ORDER BY funded DESC
    """)
    sec_rows = [Tr(Td(r["sector"], cls=_TD), Td(fmt_uzs(r["funded"]), cls=_TDR + " text-accent"),
                   cls="border-b border-line") for r in by_sector]
    kpis = Div(
        _card("DSO (avg hold)", f"{float(m.get('avg_hold') or 0):.0f} d", "settled positions"),
        _card("Default rate", f"{dr:.1f}%", "of positions"),
        _card("Settled", str(m.get("settled", 0)), "positions"),
        _card("Recovery", "—", "wire to settlements"),
        cls="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8",
    )
    return _admin_page(req, "/app/admin/reports", "nav_admin_reports",
                       kpis,
                       Div(P("Funded volume by sector", cls="text-sm font-medium text-ink mb-3"),
                           _table(["Sector", "Funded"], sec_rows)))


# ── Audit log ─────────────────────────────────────────────────────────────

@rt("/app/admin/audit")
def admin_audit(req):
    g = _guard(req)
    if g:
        return g
    rows = []
    for r in _audit_rows(50):
        when = r["created_at"]
        wstr = when.strftime("%Y-%m-%d %H:%M") if hasattr(when, "strftime") else str(when)
        rows.append(Tr(
            Td(wstr, cls=_TD + " text-ink-muted whitespace-nowrap"),
            Td(r["actor"], cls=_TD), Td(r["action"], cls=_TD + " font-mono text-xs"),
            Td(r["entity"], cls=_TD), Td(r["detail"], cls=_TD + " text-ink-muted"),
            cls="border-b border-line"))
    return _admin_page(req, "/app/admin/audit", "nav_admin_audit",
                       _table(["When", "Actor", "Action", "Entity", "Detail"], rows))


# ── Seller & payer landings (role-scoped) ───────────────────────────────

@rt("/app/seller")
def seller_home(req):
    lang = get_lang(req)
    apps = _q("""
        SELECT i.invoice_number, i.debtor_name, i.amount, i.risk_grade, i.status
        FROM factorio.invoices i ORDER BY i.id DESC LIMIT 12
    """)
    rows = [Tr(Td(a["invoice_number"], cls=_TD), Td(a["debtor_name"], cls=_TD),
               Td(fmt_uzs(a["amount"]), cls=_TDR), Td(a["risk_grade"], cls="py-3 px-4 text-center text-sm"),
               Td(a["status"], cls=_TD), cls="border-b border-line") for a in apps]
    return app_page(
        t("nav_seller", lang),
        Section_(Eyebrow(t("role_seller", lang)),
                 Heading(1, t("nav_seller", lang), cls="mt-4"),
                 P(NotStr(t("ai_triage_lede", lang) + ' &nbsp; '),
                   A(t("nav_triage", lang) + " →", href="/app/triage", cls="text-accent"),
                   cls="mt-4 text-ink-muted text-lg max-w-3xl"),
                 cls="border-t border-line"),
        Section_(_table(["Invoice", "Debtor", "Amount", "Grade", "Status"], rows), cls="border-t border-line"),
        current_path="/app/seller", lang=lang, role="seller",
    )


@rt("/app/payer")
def payer_home(req):
    lang = get_lang(req)
    top = _q("SELECT debtor_name, COUNT(*) n FROM factorio.invoices GROUP BY debtor_name ORDER BY n DESC LIMIT 1", one=True)
    debtor = (top or {}).get("debtor_name", "")
    invs = _q("""
        SELECT invoice_number, amount, due_date, status FROM factorio.invoices
        WHERE debtor_name = %(d)s ORDER BY due_date LIMIT 15
    """, {"d": debtor})
    rows = []
    for i in invs:
        act = (Span("Confirmed", cls="text-xs text-green-700") if i["status"] != "submitted"
               else Span("Confirm / dispute", cls="text-xs px-3 py-1 rounded-full bg-accent text-bg"))
        rows.append(Tr(Td(i["invoice_number"], cls=_TD), Td(fmt_uzs(i["amount"]), cls=_TDR),
                       Td(str(i["due_date"]), cls=_TD), Td(i["status"], cls=_TD),
                       Td(act, cls="py-3 px-4 text-right"), cls="border-b border-line"))
    return app_page(
        t("nav_payer", lang),
        Section_(Eyebrow(t("role_payer", lang)),
                 Heading(1, t("nav_payer", lang), cls="mt-4"),
                 P(NotStr(f"Invoices where <b>{debtor}</b> is the debtor. Confirm the obligation so suppliers can be financed."),
                   cls="mt-4 text-ink-muted text-lg max-w-3xl"),
                 cls="border-t border-line"),
        Section_(_table(["Invoice", "Amount", "Due", "Status", ""], rows), cls="border-t border-line"),
        current_path="/app/payer", lang=lang, role="payer",
    )
