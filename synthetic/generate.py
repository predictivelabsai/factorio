"""Deterministic synthetic data generator for FactorFinance.

Usage:
    python -m synthetic.generate                    # seed with default seed=42
    python -m synthetic.generate --seed 99          # custom seed
    python -m synthetic.generate --seed 42 --fresh  # truncate then re-seed
    python -m synthetic.generate --limit 5          # small subset
"""

from __future__ import annotations

import argparse
import random
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from faker import Faker

from db import connect

SECTORS = ["manufacturing", "wholesale", "construction", "logistics", "services",
           "mining", "energy", "agriculture", "telecom", "finance"]
RISK_GRADES = ["A", "B", "B", "C"]  # weighted toward B
CURRENCIES = ["UZS"]
COUNTRIES = ["UZ"]

COMPANY_TEMPLATES = [
    ("Toshkent Savdo Guruhi", "wholesale", "UZ"),
    ("Samarkand Qurilish", "construction", "UZ"),
    ("Farg'ona Logistika", "logistics", "UZ"),
    ("Buxoro Agro Export", "agriculture", "UZ"),
    ("Andijon Tekstil", "manufacturing", "UZ"),
    ("Navoiy Mashina Zavodi", "manufacturing", "UZ"),
    ("Nukus Transport Xizmatlari", "logistics", "UZ"),
    ("Qashqadaryo Energiya", "energy", "UZ"),
    ("Xorazm IT Solutions", "services", "UZ"),
    ("Jizzax Don Mahsulotlari", "agriculture", "UZ"),
    ("Surxondaryo Qurilish Materiallari", "construction", "UZ"),
    ("Namangan Yengil Sanoat", "manufacturing", "UZ"),
    ("Toshkent Biznes Konsalting", "services", "UZ"),
    ("Fergana Valley Trading", "wholesale", "UZ"),
    ("Chirchiq Kimyo Sanoat", "manufacturing", "UZ"),
]

DEBTOR_NAMES = [
    "Navoi Mining & Metallurgy Combinat", "UzAuto Motors", "Artel Electronics",
    "Enter Engineering", "Uzbekneftegaz", "Uztelecom", "Uzum Group",
    "AKFA Group", "Asaka Bank", "Ipoteka Bank", "Kapitalbank",
    "Hamkorbank", "Orient Finans Bank", "Almalyk Mining & Metallurgy Combinat",
    "Uzbekistan Airways", "Uzbekiston Temir Yo'llari", "Uzkimyosanoat",
    "Shurtan Gas Chemical Complex", "Uzbekenergo", "Uzneftmahsulot",
    "O'zbekiston Pochtasi", "SamAuto", "GM Uzbekistan",
    "Ravnaq Bank", "Mubarek Gas Processing Plant",
]


def _truncate(conn) -> None:
    tables = [
        "dividends", "settlements", "payments", "secondary_market",
        "auto_invest", "investments", "invoice_updates", "notifications",
        "invoice_funding", "invoices", "faq", "companies", "users",
    ]
    with conn.cursor() as cur:
        for t in tables:
            cur.execute(f"TRUNCATE factorfinance.{t} CASCADE")
    conn.commit()
    print("[synthetic] truncated all tables")


def _seed_users(conn, rng: random.Random, fake: Faker) -> dict[str, int]:
    users = []
    for role, count in [("admin", 2), ("seller", 10), ("investor", 20)]:
        for i in range(count):
            users.append({
                "email": f"{role}{i+1}@factorfinance.io",
                "username": f"{role}{i+1}",
                "role": role,
                "phone": fake.phone_number(),
                "is_verified": True,
            })

    id_map = {}
    with conn.cursor() as cur:
        for u in users:
            cur.execute("""
                INSERT INTO factorfinance.users (email, username, role, phone, is_verified)
                VALUES (%(email)s, %(username)s, %(role)s, %(phone)s, %(is_verified)s)
                ON CONFLICT (email) DO UPDATE SET username = EXCLUDED.username
                RETURNING id, email
            """, u)
            row = cur.fetchone()
            id_map[row[1]] = row[0]
    conn.commit()
    print(f"[synthetic] seeded {len(users)} users")
    return id_map


def _seed_companies(conn, rng: random.Random, fake: Faker) -> dict[str, int]:
    id_map = {}
    with conn.cursor() as cur:
        for name, sector, country in COMPANY_TEMPLATES:
            reg = f"{country}{rng.randint(10000000, 99999999)}"
            turnover = rng.randint(100_000, 5_000_000)
            cur.execute("""
                INSERT INTO factorfinance.companies (name, registration_number, sector, country, address, annual_turnover)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (registration_number) DO UPDATE SET name = EXCLUDED.name
                RETURNING id, name
            """, (name, reg, sector, country, fake.address().replace("\n", ", "), turnover))
            row = cur.fetchone()
            id_map[row[1]] = row[0]
    conn.commit()
    print(f"[synthetic] seeded {len(COMPANY_TEMPLATES)} companies")
    return id_map


def _seed_invoices_and_funding(
    conn, rng: random.Random, fake: Faker,
    user_ids: dict[str, int], company_ids: dict[str, int],
    limit: int | None = None,
) -> None:
    seller_emails = [e for e in user_ids if e.startswith("seller")]
    investor_emails = [e for e in user_ids if e.startswith("investor")]
    company_names = list(company_ids.keys())
    today = date.today()

    invoice_count = limit or 30
    invoices_created = 0
    funding_created = 0
    investments_created = 0

    with conn.cursor() as cur:
        for i in range(invoice_count):
            seller_email = rng.choice(seller_emails)
            seller_id = user_ids[seller_email]
            company_name = rng.choice(company_names)
            company_id = company_ids[company_name]
            debtor = rng.choice(DEBTOR_NAMES)
            sector = rng.choice(SECTORS)
            amount = round(rng.uniform(50_000_000, 3_000_000_000), 2)
            terms = rng.choice([15, 30, 45, 60, 90, 120, 180])
            issue_date = today - timedelta(days=rng.randint(5, 60))
            due_date = issue_date + timedelta(days=terms)
            risk = rng.choice(RISK_GRADES)
            status = rng.choice(["verified", "funding", "funding", "funded", "settled"])
            inv_num = f"INV-{2026}{i+1:04d}"

            cur.execute("""
                INSERT INTO factorfinance.invoices
                    (invoice_number, seller_id, company_id, debtor_name,
                     debtor_registration, description, sector, amount, currency,
                     issue_date, due_date, payment_terms_days, status, risk_grade)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (invoice_number) DO UPDATE SET status = EXCLUDED.status
                RETURNING id
            """, (inv_num, seller_id, company_id, debtor,
                  f"REG{rng.randint(10000,99999)}", fake.sentence(),
                  sector, amount, "UZS", issue_date, due_date, terms, status, risk))
            invoice_id = cur.fetchone()[0]
            invoices_created += 1

            if status in ("funding", "funded", "settled"):
                advance_rate = round(rng.uniform(80, 92), 2)
                fee = round(rng.uniform(1.0, 3.5), 2)
                goal = round(amount * advance_rate / 100, 2)
                raised = goal if status in ("funded", "settled") else round(goal * rng.uniform(0.1, 0.9), 2)
                est_return = round(fee * terms / 30, 2)
                f_status = {"funding": "open", "funded": "funded", "settled": "settled"}[status]

                cur.execute("""
                    INSERT INTO factorfinance.invoice_funding
                        (invoice_id, name, description, funding_goal, amount_raised,
                         minimum_investment, advance_rate_pct, fee_pct_per_30d,
                         estimated_return_pct, risk_grade, funding_status,
                         target_hold_days, show_in_marketplace)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                """, (invoice_id, f"{debtor} — {inv_num}", fake.sentence(),
                      goal, raised, 500_000, advance_rate, fee, est_return, risk,
                      f_status, terms, f_status == "open"))
                funding_id = cur.fetchone()[0]
                funding_created += 1

                num_investors = rng.randint(1, 5)
                chosen = rng.sample(investor_emails, min(num_investors, len(investor_emails)))
                for inv_email in chosen:
                    inv_amount = round(raised / len(chosen), 2)
                    own_pct = round(inv_amount / goal * 100, 2) if goal else 0
                    exp_return = round(inv_amount * (1 + est_return / 100), 2)
                    inv_status = "settled" if status == "settled" else "confirmed"

                    cur.execute("""
                        INSERT INTO factorfinance.investments
                            (funding_id, investor_id, investment_amount, ownership_pct,
                             expected_return_amount, status)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (funding_id, investor_id) DO NOTHING
                    """, (funding_id, user_ids[inv_email], inv_amount, own_pct, exp_return, inv_status))
                    investments_created += 1

    conn.commit()
    print(f"[synthetic] seeded {invoices_created} invoices, {funding_created} fundings, {investments_created} investments")


def _seed_faq(conn) -> None:
    faqs = [
        ("What is invoice financing?", "Invoice financing (also called factoring) lets you sell your unpaid invoices to investors at a discount. You get cash immediately; investors earn a return when the debtor pays."),
        ("How quickly can I get funded?", "Once your invoice is verified (typically 24 hours), it's listed on our marketplace. Most invoices are fully funded within 1-3 business days."),
        ("What fees does FactorFinance charge?", "Sellers pay a fee of 1.5-3% per 30 days, depending on invoice size, debtor credit quality, and payment terms. There are no setup fees or monthly minimums."),
        ("What's the minimum investment?", "You can invest from 500,000 UZS per invoice, making it easy to diversify across multiple invoices, sectors, and risk grades."),
        ("How are invoices risk-graded?", "We assess each invoice on debtor creditworthiness, payment history, seller track record, and sector risk. Grades range from A (lowest risk) to D (highest risk)."),
        ("What happens if the debtor doesn't pay?", "We have a collections process in place. For defaulted invoices, we work with the seller and, if necessary, third-party collection agencies. Investors bear the risk of non-payment."),
    ]
    with conn.cursor() as cur:
        for i, (q, a) in enumerate(faqs):
            cur.execute("""
                INSERT INTO factorfinance.faq (question, answer, sort_order, is_active)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT DO NOTHING
            """, (q, a, i))
    conn.commit()
    print(f"[synthetic] seeded {len(faqs)} FAQs")


def run(seed: int = 42, fresh: bool = False, limit: int | None = None) -> None:
    rng = random.Random(seed)
    fake = Faker()
    Faker.seed(seed)

    with connect() as conn:
        if fresh:
            _truncate(conn)

        user_ids = _seed_users(conn, rng, fake)
        company_ids = _seed_companies(conn, rng, fake)
        _seed_invoices_and_funding(conn, rng, fake, user_ids, company_ids, limit=limit)
        _seed_faq(conn)

    print("[synthetic] done")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for FactorFinance")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fresh", action="store_true", help="Truncate before seeding")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of invoices")
    args = parser.parse_args()
    run(seed=args.seed, fresh=args.fresh, limit=args.limit)


if __name__ == "__main__":
    main()
