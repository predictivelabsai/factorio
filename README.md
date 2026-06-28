# Factorio

**Invoice financing (factoring) platform.** Factorio connects businesses that need
cash flow now with investors seeking short-term, asset-backed returns: sellers upload
unpaid invoices, investors fund them on a marketplace, and returns settle when the
invoice is paid.

One FastHTML process serves both a marketing landing site and an HTMX-driven product
app (dashboard, marketplace, portfolio), backed by PostgreSQL. The UI is trilingual
(English / Uzbek / Russian).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env                  # set DB_URL (PostgreSQL)
python -m db.migrate                  # create the factorfinance schema + tables
python -m synthetic.generate --seed 42  # seed deterministic demo data

PORT=5055 python main.py              # http://localhost:5055
```

Or with Docker:

```bash
docker compose up --build
```

## What's inside

| Path | Purpose |
|------|---------|
| `app.py` / `main.py` | FastHTML app + entrypoint (all routes register here) |
| `landing/` | Marketing site + shared UI component primitives |
| `app_routes/` | Product app: dashboard, marketplace, portfolio |
| `db/` | `schema.sql` (all tables in the `factorfinance` schema) + migration runner |
| `synthetic/` | Deterministic synthetic-data generator |
| `utils/` | Config (`settings()`) and i18n (`t()`, en/uz/ru) |
| `scripts/` | Screenshot / GIF / PDF media generation |

See [CLAUDE.md](CLAUDE.md) for architecture details and conventions.

## Tech

FastHTML + HTMX (server-rendered, no JS framework) · PostgreSQL (psycopg 3) ·
Tailwind (CDN) · pydantic-settings.
