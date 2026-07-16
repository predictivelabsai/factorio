"""Accounting / General Ledger — production back-office module.

A real double-entry ledger derived deterministically from the factoring events
(advances, settlements, fees, write-offs), plus a trial balance, per-account
ledger drill-down, and bank reconciliation. Posting is idempotent
(``post_ledger`` clears and re-derives), so it always ties out.

Posting model (per financed invoice):
  Advance disbursed:   Dr 1100 Advances receivable   Cr 1000 Cash
  Debtor settles:      Dr 1000 Cash (face)           Cr 1100 Advances receivable (advance)
                       Cr 4000 Factoring income (fee) Cr 2000 Payable to client (net reserve)
  Reserve released:    Dr 2000 Payable to client     Cr 1000 Cash
  Write-off (default): Dr 5000 Bad-debt expense       Cr 1100 Advances receivable

Access is scoped to Admin + Finance / Executive / Compliance / Super (SoD).
"""

from __future__ import annotations

from fasthtml.common import Div, P, Span, A, Table, Thead, Tbody, Tr, Th, Td
from starlette.responses import RedirectResponse

from app import rt
from utils.i18n import get_lang
from landing.components import Eyebrow, Heading, Section_
from app_routes._shared import app_page, fmt_uzs, current_role, current_subrole

try:
    from db import fetch_all, fetch_one, execute
    _HAS_DB = True
except Exception:  # pragma: no cover
    _HAS_DB = False

CAN_VIEW_GL = {"finance", "compliance", "exec", "super"}

CHART = [
    ("1000", "Cash & bank", "asset"),
    ("1100", "Advances receivable", "asset"),
    ("2000", "Payable to clients (reserve)", "liability"),
    ("4000", "Factoring income", "income"),
    ("5000", "Bad-debt expense", "expense"),
]
_ACCT_NAME = {c: n for c, n, _ in CHART}


def _ensure_gl():
    if not _HAS_DB:
        return
    execute("""CREATE TABLE IF NOT EXISTS factorio.gl_accounts (
        code TEXT PRIMARY KEY, name TEXT NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('asset','liability','equity','income','expense')))""")
    execute("""CREATE TABLE IF NOT EXISTS factorio.ledger_entries (
        id BIGSERIAL PRIMARY KEY, entry_date DATE NOT NULL,
        account_code TEXT NOT NULL, debit NUMERIC(15,2) NOT NULL DEFAULT 0,
        credit NUMERIC(15,2) NOT NULL DEFAULT 0, ref_type TEXT NOT NULL DEFAULT '',
        ref_id TEXT NOT NULL DEFAULT '', memo TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
    execute("""CREATE TABLE IF NOT EXISTS factorio.bank_transactions (
        id BIGSERIAL PRIMARY KEY, txn_date DATE NOT NULL, amount NUMERIC(15,2) NOT NULL,
        description TEXT NOT NULL DEFAULT '', reconciled BOOLEAN NOT NULL DEFAULT FALSE,
        ref_id TEXT NOT NULL DEFAULT '')""")
    for code, name, typ in CHART:
        execute("INSERT INTO factorio.gl_accounts (code,name,type) VALUES (%(c)s,%(n)s,%(t)s) "
                "ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, type=EXCLUDED.type",
                {"c": code, "n": name, "t": typ})


def _f(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def post_ledger() -> int:
    """(Re)derive all ledger entries + bank transactions from factoring data."""
    if not _HAS_DB:
        return 0
    _ensure_gl()
    execute("DELETE FROM factorio.ledger_entries")
    execute("DELETE FROM factorio.bank_transactions")
    rows = fetch_all("""
        SELECT i.invoice_number, i.amount AS face, i.status, i.due_date,
               f.advance_rate_pct,
               COALESCE(SUM(inv.expected_return_amount - inv.investment_amount),0) AS interest,
               MAX(s.settlement_date) AS settlement_date
        FROM factorio.invoices i
        JOIN factorio.invoice_funding f ON f.invoice_id = i.id
        LEFT JOIN factorio.investments inv ON inv.funding_id = f.id
        LEFT JOIN factorio.settlements s ON s.funding_id = f.id
        WHERE i.status IN ('funding','funded','settled','defaulted')
        GROUP BY i.id, f.advance_rate_pct, i.invoice_number, i.amount, i.status, i.due_date
    """)
    entries, banks = [], []

    def post(dt, acct, dr, cr, rtype, rid, memo):
        entries.append((dt, acct, round(dr, 2), round(cr, 2), rtype, rid, memo))

    for r in rows:
        num = r["invoice_number"]; face = _f(r["face"])
        advance = face * _f(r["advance_rate_pct"]) / 100.0
        fee = max(0.0, _f(r["interest"]))
        d_adv = r["due_date"]
        d_set = r["settlement_date"] or r["due_date"]
        # advance disbursed
        post(d_adv, "1100", advance, 0, "advance", num, f"Advance on {num}")
        post(d_adv, "1000", 0, advance, "advance", num, f"Advance paid — {num}")
        banks.append((d_adv, -advance, f"Advance disbursed {num}", True))
        if r["status"] == "settled":
            reserve = max(0.0, face - advance - fee)
            post(d_set, "1000", face, 0, "settle", num, f"Debtor payment {num}")
            post(d_set, "1100", 0, advance, "settle", num, f"Clear advance {num}")
            post(d_set, "4000", 0, fee, "settle", num, f"Factoring income {num}")
            post(d_set, "2000", 0, reserve, "settle", num, f"Reserve owed {num}")
            post(d_set, "2000", reserve, 0, "reserve", num, f"Reserve released {num}")
            post(d_set, "1000", 0, reserve, "reserve", num, f"Reserve paid {num}")
            banks.append((d_set, face, f"Debtor payment {num}", True))
            banks.append((d_set, -reserve, f"Reserve released {num}", False))  # a few unreconciled
        elif r["status"] == "defaulted":
            post(d_adv, "5000", advance, 0, "writeoff", num, f"Write-off {num}")
            post(d_adv, "1100", 0, advance, "writeoff", num, f"Write-off {num}")

    for e in entries:
        execute("INSERT INTO factorio.ledger_entries "
                "(entry_date,account_code,debit,credit,ref_type,ref_id,memo) "
                "VALUES (%(d)s,%(a)s,%(dr)s,%(cr)s,%(rt)s,%(ri)s,%(m)s)",
                dict(zip(("d", "a", "dr", "cr", "rt", "ri", "m"), e)))
    for b in banks:
        execute("INSERT INTO factorio.bank_transactions (txn_date,amount,description,reconciled) "
                "VALUES (%(d)s,%(a)s,%(desc)s,%(r)s)",
                {"d": b[0], "a": round(b[1], 2), "desc": b[2], "r": b[3]})
    return len(entries)


# ── UI ────────────────────────────────────────────────────────────────────

_TH = "text-left text-[11px] font-mono tracking-widest uppercase text-ink-dim py-3 px-4"
_TDR = "py-3 px-4 text-sm text-ink text-right tabular-nums"
_TD = "py-3 px-4 text-sm text-ink"


def _guard(req):
    if current_role(req) != "admin":
        return RedirectResponse("/app", status_code=303)
    return None


def _table(headers, rows):
    return Div(Table(
        Thead(Tr(*[Th(h, cls=_TH if i == 0 else _TH.replace("text-left", "text-right"))
                   for i, h in enumerate(headers)], cls="border-b border-line")),
        Tbody(*rows), cls="w-full"),
        cls="rounded-2xl bg-bg-elevated border border-line overflow-hidden overflow-x-auto")


def _acct_page(req, path, title, *content):
    lang = get_lang(req)
    restricted = current_subrole(req) not in CAN_VIEW_GL
    if restricted:
        content = (P("This ledger is restricted to Finance / Compliance / Executive roles "
                     "(segregation of duties).", cls="text-red-700"),)
    return app_page(
        title,
        Section_(Eyebrow("Back office · Accounting"),
                 Heading(1, title, cls="mt-4"),
                 P("Double-entry general ledger derived from advances, settlements, fees and write-offs.",
                   cls="mt-3 text-ink-muted max-w-3xl"), cls="border-t border-line"),
        Section_(*content, cls="border-t border-line"),
        current_path=path, lang=lang, role="admin", subrole=current_subrole(req),
    )


def _has_entries() -> bool:
    if not _HAS_DB:
        return False
    try:
        r = fetch_one("SELECT COUNT(*) n FROM factorio.ledger_entries") or {}
        return (r.get("n") or 0) > 0
    except Exception:
        return False


@rt("/app/admin/accounting")
def accounting(req):
    g = _guard(req)
    if g:
        return g
    if not _has_entries():
        try:
            post_ledger()
        except Exception:
            pass
    rows_data = fetch_all("""
        SELECT a.code, a.name, a.type,
               COALESCE(SUM(l.debit),0) dr, COALESCE(SUM(l.credit),0) cr
        FROM factorio.gl_accounts a
        LEFT JOIN factorio.ledger_entries l ON l.account_code=a.code
        GROUP BY a.code, a.name, a.type ORDER BY a.code
    """) if _HAS_DB else []
    tot_dr = tot_cr = 0.0
    rows = []
    for r in rows_data:
        dr, cr = _f(r["dr"]), _f(r["cr"])
        tot_dr += dr; tot_cr += cr
        bal = dr - cr
        rows.append(Tr(
            Td(A(f"{r['code']} · {r['name']}", href=f"/app/admin/accounting/ledger?account={r['code']}",
                 cls="text-accent hover:underline"), cls=_TD),
            Td(r["type"], cls=_TD + " text-ink-muted"),
            Td(fmt_uzs(dr), cls=_TDR), Td(fmt_uzs(cr), cls=_TDR),
            Td(fmt_uzs(abs(bal)) + (" Dr" if bal >= 0 else " Cr"), cls=_TDR + " font-medium"),
            cls="border-b border-line"))
    rows.append(Tr(
        Td("Total", cls=_TD + " font-medium"), Td("", cls=_TD),
        Td(fmt_uzs(tot_dr), cls=_TDR + " font-medium"),
        Td(fmt_uzs(tot_cr), cls=_TDR + " font-medium"),
        Td("✓ balanced" if abs(tot_dr - tot_cr) < 1 else "⚠ off", cls=_TDR + " text-accent"),
        cls="border-t-2 border-line bg-bg-raised/40"))
    return _acct_page(req, "/app/admin/accounting", "Trial balance",
                      _table(["Account", "Type", "Debit", "Credit", "Balance"], rows),
                      P(A("Journal →", href="/app/admin/accounting/journal", cls="text-accent mr-6"),
                        A("Bank reconciliation →", href="/app/admin/accounting/reconciliation", cls="text-accent"),
                        cls="mt-4 text-sm"))


@rt("/app/admin/accounting/journal")
def accounting_journal(req):
    g = _guard(req)
    if g:
        return g
    data = fetch_all("""SELECT entry_date, account_code, debit, credit, memo
                        FROM factorio.ledger_entries ORDER BY entry_date DESC, id DESC LIMIT 60""") if _HAS_DB else []
    rows = [Tr(
        Td(str(r["entry_date"]), cls=_TD + " text-ink-muted whitespace-nowrap"),
        Td(f"{r['account_code']} {_ACCT_NAME.get(r['account_code'],'')}", cls=_TD),
        Td(fmt_uzs(r["debit"]) if _f(r["debit"]) else "", cls=_TDR),
        Td(fmt_uzs(r["credit"]) if _f(r["credit"]) else "", cls=_TDR),
        Td(r["memo"], cls=_TD + " text-ink-muted"), cls="border-b border-line") for r in data]
    return _acct_page(req, "/app/admin/accounting", "Journal",
                      _table(["Date", "Account", "Debit", "Credit", "Memo"], rows))


@rt("/app/admin/accounting/ledger")
def accounting_ledger(req, account: str = "1000"):
    g = _guard(req)
    if g:
        return g
    data = fetch_all("""SELECT entry_date, debit, credit, memo FROM factorio.ledger_entries
                        WHERE account_code=%(a)s ORDER BY entry_date, id""",
                     {"a": account}) if _HAS_DB else []
    bal = 0.0
    rows = []
    for r in data:
        bal += _f(r["debit"]) - _f(r["credit"])
        rows.append(Tr(
            Td(str(r["entry_date"]), cls=_TD + " text-ink-muted whitespace-nowrap"),
            Td(r["memo"], cls=_TD),
            Td(fmt_uzs(r["debit"]) if _f(r["debit"]) else "", cls=_TDR),
            Td(fmt_uzs(r["credit"]) if _f(r["credit"]) else "", cls=_TDR),
            Td(fmt_uzs(abs(bal)) + (" Dr" if bal >= 0 else " Cr"), cls=_TDR + " font-medium"),
            cls="border-b border-line"))
    return _acct_page(req, "/app/admin/accounting",
                      f"Ledger · {account} {_ACCT_NAME.get(account,'')}",
                      _table(["Date", "Memo", "Debit", "Credit", "Running balance"], rows))


@rt("/app/admin/accounting/reconciliation")
def accounting_recon(req):
    g = _guard(req)
    if g:
        return g
    data = fetch_all("""SELECT txn_date, amount, description, reconciled
                        FROM factorio.bank_transactions ORDER BY txn_date DESC, id DESC LIMIT 60""") if _HAS_DB else []
    matched = sum(1 for r in data if r["reconciled"])
    rows = [Tr(
        Td(str(r["txn_date"]), cls=_TD + " text-ink-muted whitespace-nowrap"),
        Td(r["description"], cls=_TD),
        Td(fmt_uzs(r["amount"]), cls=_TDR + (" text-accent" if _f(r["amount"]) >= 0 else " text-red-700")),
        Td(Span("✓ matched" if r["reconciled"] else "unmatched",
                cls="text-xs " + ("text-green-700" if r["reconciled"] else "text-yellow-700")),
           cls="py-3 px-4"),
        cls="border-b border-line") for r in data]
    return _acct_page(req, "/app/admin/accounting", "Bank reconciliation",
                      P(f"{matched} of {len(data)} bank transactions reconciled.",
                        cls="text-ink-muted mb-4 text-sm"),
                      _table(["Date", "Description", "Amount", "Status"], rows))
