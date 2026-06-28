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

### Entrypoint & route registration

`main.py` only calls `serve(port=settings().port)`; all wiring is in `app.py`. `app.py` builds the `fast_app(...)` instance, then imports each route module **for its side effect** — the `@rt(...)` decorators register against the shared app at import time. A new route module does nothing until it is imported at the bottom of `app.py`.

### Routes (one FastHTML `app.py` mounts everything)

- `/` + `/for-sellers` + `/for-investors` + `/how-it-works` + `/pricing` + `/contact` → `landing/routes.py`
- `/app` → dashboard with platform stats. `app_routes/dashboard.py`
- `/app/marketplace` + `/app/marketplace/<funding_id>` → browse + detail for fundable invoices. `app_routes/marketplace.py`
- `/app/portfolio` → investor positions and returns table. `app_routes/portfolio.py`
- `/set-lang?lang=` → sets the `lang` cookie and redirects back (i18n switcher)

### Internationalisation (trilingual: en / uz / ru)

The entire site is translated, not just the landing page. `utils/i18n.py` holds a flat `TRANSLATIONS` dict (`key → {en, uz, ru}`) plus `SUPPORTED_LANGS`/`DEFAULT_LANG="en"`.

- In a route: `lang = get_lang(req)` (reads the `lang` cookie, falls back to `en`), then `t("some_key", lang)`.
- Pass `lang` through to `page(title, *content, current_path=..., lang=lang)` so the nav/footer render in the right language.
- Adding user-facing copy means adding a key to `TRANSLATIONS` with **all three** languages — never hardcode display strings in routes.

### Configuration

`utils/config.py` exposes a cached `settings()` returning a pydantic-settings `Settings` (loads `.env`): `db_url` (`DB_URL`), `app_env` (`APP_ENV`), `app_secret` (`APP_SECRET`), `port` (`PORT`, default 5055). Always read config through `settings()`, not `os.environ`.

### Data model (`db/schema.sql`)

All tables live in `factorfinance.*`:
`users, companies, invoices, invoice_funding, investments, invoice_updates, notifications, settlements, dividends, payments, secondary_market, auto_invest, faq`.

Adapted from litfunder-backend: LegalCase → invoices, CaseFunding → invoice_funding, CaseInvestment → investments, etc.

### Front-end

- Tailwind CSS via CDN + Inter / JetBrains Mono fonts
- Design: parchment background (#F7F6F1), deep-green accent (#1F5D43)
- Component primitives in `landing/components.py`: `page()`, `Hero()`, `Section_()`, `Eyebrow()`, `Heading()`, `Button_()`, `Pill()`, `CTASection()`, etc. `page()` is the shell every full page returns (wraps content in nav + footer + Tailwind config).
- `static/site.css` — minimal custom CSS (hero grid, selection color)
- No React/Vue/Svelte — pure server-rendered FastHTML + HTMX
- `fasthtml-ctx.txt` (repo root) is a bundled FastHTML reference — consult it for framework API/idioms instead of guessing.

### Media / docs generation (`scripts/`)

`scripts/capture_screenshots.py` (Playwright) refreshes `screenshots/`, `scripts/make_gif.py` builds `docs/factorfinance.gif`, `scripts/make_pdf.py` builds the product-tour PDF. These drive a running server and are only needed when regenerating marketing/docs assets.

### Synthetic data (`synthetic/generate.py`)

- Deterministic given `--seed` (uses `random.Random(seed)` + `Faker.seed(seed)`)
- Seeds: 32 users (admin/seller/investor), 15 companies, 30 invoices with funding + investments, 6 FAQs
- Idempotent via `ON CONFLICT ... DO UPDATE`

## Conventions

- Schemas always fully qualified (`factorfinance.*`) — never rely on `search_path`
- HTML entities must use `NotStr()` wrapper (FastHTML escapes strings by default)
- Synthetic data is deterministic given `--seed`
- Money is currently **UZS** in practice — synthetic data hardcodes `UZS`, and dashboard/portfolio format `f"UZS {x:,.0f}"`. Only `marketplace.py` carries a multi-symbol map (EUR/USD/GBP/UZS). New monetary UI should go through a single formatter rather than hardcoding another currency string.
- User-facing strings go through `t(key, lang)` with all three languages defined — never hardcode display copy
- When adding new routes, import them at the bottom of `app.py` for side-effect registration
