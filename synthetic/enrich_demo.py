"""Make the demo data read realistically (no zeros everywhere).

Idempotent. Gives the demo investor (investor1) a realistic portfolio — a spread
of settled positions with paid dividends (realized returns + payment habits) on
top of their active positions — and repairs any implausibly small company
turnovers. Safe to run repeatedly.

    python -m synthetic.enrich_demo
"""

from __future__ import annotations

import random

from db import fetch_all, fetch_one, execute


def _demo_investor_id() -> int | None:
    row = fetch_one("SELECT id FROM factorio.users WHERE role='investor' ORDER BY id LIMIT 1")
    return row["id"] if row else None


def fix_turnovers() -> int:
    """Company annual turnover should read like a real SME (millions), not cents."""
    rng = random.Random(42)
    rows = fetch_all("SELECT id FROM factorio.companies WHERE annual_turnover IS NULL "
                     "OR annual_turnover < 30000000000 ORDER BY id")
    n = 0
    for r in rows:
        val = rng.randint(30_000_000_000, 500_000_000_000)  # UZS scale
        execute("UPDATE factorio.companies SET annual_turnover=%(v)s WHERE id=%(i)s",
                {"v": val, "i": r["id"]})
        n += 1
    return n


def enrich_investor() -> int:
    iid = _demo_investor_id()
    if not iid:
        return 0
    settled = fetch_all("""
        SELECT f.id AS funding_id, f.funding_goal, f.estimated_return_pct, f.created_at AS funding_date,
               s.settlement_date
        FROM factorio.invoice_funding f
        LEFT JOIN factorio.settlements s ON s.funding_id=f.id
        WHERE f.funding_status='settled' ORDER BY f.id
    """)
    n = 0
    for r in settled:
        amount = float(r["funding_goal"] or 0)
        if amount <= 0:
            continue
        ret_pct = float(r["estimated_return_pct"] or 12) / 100.0
        exp_return = round(amount * (1 + ret_pct), 2)
        interest = round(exp_return - amount, 2)
        sdate = r["settlement_date"] or r["funding_date"]
        execute("""INSERT INTO factorio.investments
                   (funding_id, investor_id, investment_amount, ownership_pct,
                    expected_return_amount, status, investment_date)
                   VALUES (%(f)s,%(i)s,%(amt)s,100,%(exp)s,'settled',%(d)s)
                   ON CONFLICT (funding_id, investor_id) DO UPDATE
                     SET investment_amount=EXCLUDED.investment_amount,
                         expected_return_amount=EXCLUDED.expected_return_amount,
                         status='settled', investment_date=EXCLUDED.investment_date""",
                {"f": r["funding_id"], "i": iid, "amt": amount, "exp": exp_return, "d": r["funding_date"]})
        # realized dividend (paid)
        has = fetch_one("SELECT id FROM factorio.dividends WHERE funding_id=%(f)s AND investor_id=%(i)s",
                        {"f": r["funding_id"], "i": iid})
        if has:
            execute("UPDATE factorio.dividends SET amount=%(a)s, invested_amount=%(inv)s, is_paid=TRUE, created_at=%(d)s "
                    "WHERE id=%(id)s", {"a": interest, "inv": amount, "d": sdate, "id": has["id"]})
        else:
            execute("""INSERT INTO factorio.dividends (investor_id, funding_id, amount, invested_amount, is_paid, created_at)
                       VALUES (%(i)s,%(f)s,%(a)s,%(inv)s,TRUE,%(d)s)""",
                    {"i": iid, "f": r["funding_id"], "a": interest, "inv": amount, "d": sdate})
        n += 1
    return n


def drop_junk_invoices() -> int:
    """Remove the tiny EXT-* webhook test invoices (unrealistic $4/$6 amounts)."""
    rows = fetch_all("SELECT id FROM factorio.invoices WHERE invoice_number LIKE %(p)s AND amount < 1000000",
                     {"p": "EXT-%"})
    n = 0
    for r in rows:
        execute("DELETE FROM factorio.invoices WHERE id=%(i)s", {"i": r["id"]})
        n += 1
    return n


def main() -> None:
    j = drop_junk_invoices()
    t = fix_turnovers()
    e = enrich_investor()
    print(f"dropped {j} junk invoices; repaired {t} turnovers; gave demo investor {e} settled positions")


if __name__ == "__main__":
    main()
