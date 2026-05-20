# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## What this is

FactorFinance — an invoice financing (factoring) platform. One FastHTML process hosting a marketing landing site and an HTMX-driven product app (dashboard, marketplace, portfolio). Backed by PostgreSQL (`factorfinance` schema). Adapted from the litfunder-backend data model; landing page design follows the pehero sister repo pattern; business positioning modelled on investly.co.

## Commands

All commands assume `source .venv/bin/activate` (or use `.venv/bin/python` directly).

```bash
# Setup
cp .env.example .env                             # fill DB_URL
pip install -r requirements.txt
python -m db.migrate                             # idempotent; creates factorfinance schema + tables
python -m db.migrate --drop                      # DESTRUCTIVE — drops schema and recreates

# Seed synthetic data (deterministic for a given seed)
python -m synthetic.generate --seed 42           # full seed
python -m synthetic.generate --seed 42 --fresh   # truncate then re-seed
python -m synthetic.generate --limit 5           # small subset for fast iteration

# Run
PORT=5055 python main.py                         # :5055 is the default

# Docker
docker compose up --build                        # local bring-up
```

## Architecture

### Routes (one FastHTML `app.py` mounts everything)

- `/` + `/for-sellers` + `/for-investors` + `/how-it-works` + `/pricing` + `/contact` → `landing/routes.py`
- `/app` → dashboard with platform stats. `app_routes/dashboard.py`
- `/app/marketplace` + `/app/marketplace/<funding_id>` → browse + detail for fundable invoices. `app_routes/marketplace.py`
- `/app/portfolio` → investor positions and returns table. `app_routes/portfolio.py`

### Data model (`db/schema.sql`)

All tables live in `factorfinance.*`:
`users, companies, invoices, invoice_funding, investments, invoice_updates, notifications, settlements, dividends, payments, secondary_market, auto_invest, faq`.

Adapted from litfunder-backend: LegalCase → invoices, CaseFunding → invoice_funding, CaseInvestment → investments, etc.

### Front-end

- Tailwind CSS via CDN + Inter / JetBrains Mono fonts
- Design: parchment background (#F7F6F1), deep-green accent (#1F5D43)
- Component primitives in `landing/components.py`: `page()`, `Hero()`, `Section_()`, `Eyebrow()`, `Heading()`, `Button_()`, `Pill()`, `CTASection()`, etc.
- `static/site.css` — minimal custom CSS (hero grid, selection color)
- No React/Vue/Svelte — pure server-rendered FastHTML + HTMX

### Synthetic data (`synthetic/generate.py`)

- Deterministic given `--seed` (uses `random.Random(seed)` + `Faker.seed(seed)`)
- Seeds: 32 users (admin/seller/investor), 15 companies, 30 invoices with funding + investments, 6 FAQs
- Idempotent via `ON CONFLICT ... DO UPDATE`

## Conventions

- Schemas always fully qualified (`factorfinance.*`) — never rely on `search_path`
- HTML entities must use `NotStr()` wrapper (FastHTML escapes strings by default)
- Synthetic data is deterministic given `--seed`
- Monetary figures in EUR by default
- When adding new routes, import them in `app.py` for side-effect registration
