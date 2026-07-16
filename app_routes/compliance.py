"""Compliance, legal & audit — production module (area 8).

A compliance posture screen: AML/KYC coverage, an action-audit summary (the audit
log is already persisted in factorio.audit_log), a **data-retention schedule**, and
a regulatory checklist (GDPR / AML / assignment registration). Audit is
exportable. Scoped to Compliance / Executive / Super.
"""

from __future__ import annotations

import csv
import io

from fasthtml.common import Div, P, Span, A, Table, Thead, Tbody, Tr, Th, Td
from starlette.responses import RedirectResponse, Response

from app import rt
from utils.i18n import get_lang
from landing.components import Eyebrow, Heading, Section_
from app_routes._shared import app_page, current_role, current_subrole

try:
    from db import fetch_all, fetch_one
    _HAS_DB = True
except Exception:  # pragma: no cover
    _HAS_DB = False

CAN_VIEW = {"compliance", "exec", "super"}

# entity -> retention period (regulatory data-retention schedule)
RETENTION = [
    ("KYC / onboarding records", "7 years after relationship ends", "AML Regs"),
    ("Invoice & assignment records", "6 years", "Commercial law"),
    ("Ledger / accounting entries", "7 years", "Tax / audit"),
    ("Audit log", "10 years (immutable)", "Internal control"),
    ("Collections / dunning history", "6 years", "Commercial law"),
    ("Personal data (contacts)", "Until consent withdrawn + 30 days", "GDPR"),
]
CHECKLIST = [
    ("AML / KYC screening on all clients & debtors", "kyc"),
    ("Sanctions / PEP screening", "static"),
    ("Assignment registered in collateral registry", "assign"),
    ("Immutable audit log of privileged actions", "audit"),
    ("Segregation of duties enforced (RBAC)", "static"),
    ("Data-retention schedule defined", "static"),
]


def _card(label, value, sub=""):
    return Div(P(label, cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
               P(value, cls="text-3xl font-medium tracking-tighter text-ink mb-1"),
               P(sub, cls="text-ink-muted text-sm") if sub else None,
               cls="p-7 rounded-2xl bg-bg-elevated border border-line")


_TH = "text-left text-[11px] font-mono tracking-widest uppercase text-ink-dim py-3 px-4"
_TD = "py-3 px-4 text-sm text-ink"


def _guard(req):
    if current_role(req) != "admin":
        return RedirectResponse("/app", status_code=303)
    return None


def _table(headers, rows):
    return Div(Table(Thead(Tr(*[Th(h, cls=_TH) for h in headers], cls="border-b border-line")),
                     Tbody(*rows), cls="w-full"),
               cls="rounded-2xl bg-bg-elevated border border-line overflow-hidden overflow-x-auto")


@rt("/app/admin/compliance")
def compliance(req):
    g = _guard(req)
    if g:
        return g
    lang = get_lang(req)
    if current_subrole(req) not in CAN_VIEW:
        return app_page("Compliance",
                        Section_(Eyebrow("Back office · Compliance"), Heading(1, "Compliance", cls="mt-4"),
                                 P("Restricted to Compliance / Executive / Super (segregation of duties).",
                                   cls="mt-3 text-red-700"), cls="border-t border-line"),
                        current_path="/app/admin/compliance", lang=lang, role="admin", subrole=current_subrole(req))
    kyc = _q("SELECT COUNT(*) n, COUNT(*) FILTER (WHERE status='approved') ok FROM factorio.kyc_cases", one=True) or {}
    kyc_pct = round(100 * float(kyc.get("ok") or 0) / (float(kyc.get("n") or 0) or 1))
    audit_n = (_q("SELECT COUNT(*) n FROM factorio.audit_log", one=True) or {}).get("n", 0)
    by_action = _q("SELECT action, COUNT(*) n FROM factorio.audit_log GROUP BY action ORDER BY n DESC LIMIT 10")

    kpis = Div(
        _card("KYC coverage", f"{kyc_pct}%", f"{kyc.get('ok',0)}/{kyc.get('n',0)} approved"),
        _card("Audited actions", str(audit_n), "immutable log"),
        _card("Retention policies", str(len(RETENTION)), "categories"),
        cls="grid md:grid-cols-3 gap-4 mb-8")

    def _status(key):
        if key == "kyc":
            return "✓" if kyc_pct >= 60 else "partial"
        if key == "audit":
            return "✓" if audit_n else "—"
        return "✓"
    check_rows = [Tr(Td(txt, cls=_TD),
                     Td(Span(_status(k), cls="text-green-700" if _status(k) == "✓" else "text-yellow-700"),
                        cls="py-3 px-4 text-center"),
                     cls="border-b border-line") for txt, k in CHECKLIST]
    ret_rows = [Tr(Td(e, cls=_TD), Td(p, cls=_TD), Td(b, cls=_TD + " text-ink-muted"), cls="border-b border-line")
                for e, p, b in RETENTION]
    act_rows = [Tr(Td(r["action"], cls=_TD + " font-mono text-xs"), Td(str(r["n"]), cls=_TD + " text-right"),
                   cls="border-b border-line") for r in by_action]

    return app_page("Compliance",
                    Section_(Eyebrow("Back office · Compliance & audit"),
                             Heading(1, "Compliance", cls="mt-4"),
                             P("Regulatory posture, audit summary and the data-retention schedule.",
                               cls="mt-3 text-ink-muted max-w-3xl"), cls="border-t border-line"),
                    Section_(
                        kpis,
                        Div(P("Regulatory checklist", cls="text-sm font-medium text-ink mb-3"),
                            _table(["Control", "Status"], check_rows), cls="mb-8 max-w-2xl"),
                        Div(P("Data-retention schedule", cls="text-sm font-medium text-ink mb-3"),
                            _table(["Record category", "Retention", "Basis"], ret_rows), cls="mb-8"),
                        Div(Div(P("Audit — actions by type", cls="text-sm font-medium text-ink"),
                                A("Export audit CSV →", href="/app/admin/compliance/export", cls="text-accent text-sm"),
                                cls="flex items-center justify-between mb-3"),
                            _table(["Action", "Count"], act_rows), cls="max-w-2xl"),
                        cls="border-t border-line"),
                    current_path="/app/admin/compliance", lang=lang, role="admin", subrole=current_subrole(req))


@rt("/app/admin/compliance/export")
def compliance_export(req):
    g = _guard(req)
    if g:
        return g
    if current_subrole(req) not in CAN_VIEW or not _HAS_DB:
        return RedirectResponse("/app/admin/compliance", status_code=303)
    rows = fetch_all("SELECT created_at, actor, role, action, entity, detail FROM factorio.audit_log ORDER BY created_at DESC")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["created_at", "actor", "role", "action", "entity", "detail"])
    for r in rows:
        w.writerow([r["created_at"], r["actor"], r["role"], r["action"], r["entity"], r["detail"]])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=audit_log.csv"})


def _q(sql, params=None, one=False):
    if not _HAS_DB:
        return None if one else []
    try:
        return (fetch_one if one else fetch_all)(sql, params or {})
    except Exception:
        return None if one else []
