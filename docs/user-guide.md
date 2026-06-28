# FactorFinance User Guide

**Invoice financing for growing businesses.**

FactorFinance connects businesses that need working capital with investors seeking short-term, asset-backed returns. Sellers submit unpaid invoices; investors fund them at a discount; everyone benefits when the debtor pays.

---

## Landing Pages

### Homepage (`/`)

The homepage introduces FactorFinance with key stats and a clear value proposition.

![Homepage](../screenshots/01-home-en.png)

**Key elements:**
- Hero section: "Turn unpaid invoices into working capital"
- Stats strip: 85% advance rate, 1–3 day turnaround, 5 sectors supported, 3 languages (fully localizable)
- Four-step process: Submit → Verify → Fund → Settle
- Sector cards: manufacturing, wholesale, construction, logistics, services
- Benefits strip with investor return targets (8–12% p.a.)
- Call-to-action sections for both sellers and investors

### For Sellers (`/for-sellers`)

Explains how invoice financing helps businesses grow faster.

![For Sellers](../screenshots/02-for-sellers-en.png)

**Highlights:**
- Three benefits: faster growth, better supplier terms, efficient payroll
- Eligibility criteria: 6+ months trading, 500M UZS minimum turnover, 15–180 day invoice terms
- Clear apply CTA with no-commitment messaging

### For Investors (`/for-investors`)

Details the investment opportunity in invoice-backed assets.

![For Investors](../screenshots/03-for-investors-en.png)

**Highlights:**
- Target returns of 8–12% annualised on short-duration assets
- Four advantages: short duration, asset-backed, transparent risk grading, diversification
- Step-by-step investing process: Browse → Invest → Track → Collect

### How It Works (`/how-it-works`)

The detailed four-step flow from invoice submission to settlement.

![How It Works](../screenshots/04-how-it-works-en.png)

**The four steps:**
1. **Submit** — Seller uploads an invoice with debtor details
2. **Verify** — FactorFinance checks the debtor and assigns a risk grade (A–D)
3. **Fund** — Investors browse the marketplace and fund the invoice
4. **Settle** — When the debtor pays, investors receive their returns

### Pricing (`/pricing`)

Transparent fee structure for all participants.

![Pricing](../screenshots/05-pricing-en.png)

**Three tiers:**
- **Sellers**: 1.5–3% fee per 30 days, 80–90% advance rate, no setup fees
- **Investors**: Free to invest, minimum 500,000 UZS per invoice, risk grades A–D
- **Enterprise**: Custom terms for businesses with 1B+ UZS monthly invoice volume

### Contact (`/contact`)

Simple contact form for inquiries.

![Contact](../screenshots/06-contact-en.png)

---

## App Pages

### Dashboard (`/app`)

The main overview after logging in. Shows platform-wide statistics.

![Dashboard](../screenshots/07-dashboard-en.png)

**Stats cards:**
- **Total Funded** — Aggregate UZS funded across all invoices
- **Invoices** — Total invoices submitted to the platform
- **Active Funding** — Invoices currently seeking investor funding
- **Investors** — Number of active investors on the platform

Quick-action buttons link to the Marketplace and Portfolio.

### Marketplace (`/app/marketplace`)

Browse all open invoice funding opportunities.

![Marketplace](../screenshots/08-marketplace-en.png)

**Each invoice card shows:**
- Debtor name and sector tag
- Risk grade (A–D) with color coding
- Seller company name
- Invoice amount in UZS
- Funding progress bar with percentage funded
- Key metrics: advance rate, fee per 30 days, estimated return
- Investment term in days
- "Invest" button linking to the detail page

### Invoice Detail (`/app/marketplace/{id}`)

Full details on a specific invoice funding opportunity.

![Invoice Detail](../screenshots/09-marketplace-detail-en.png)

**Information displayed:**
- Back navigation to marketplace
- Risk grade and sector prominently shown
- Debtor name as the page heading
- Invoice number and seller company with country
- Funding progress: amount raised vs goal with progress bar
- Four metric cards: invoice amount, advance rate, fee structure, estimated return
- Side panel: debtor details, seller info, risk grade, due date

### Portfolio (`/app/portfolio`)

View all investment positions and track returns.

![Portfolio](../screenshots/10-portfolio-en.png)

**Summary cards:**
- Total Invested (UZS)
- Expected Returns (UZS)
- Active Positions (count)
- Total Positions (count)

**Positions table columns:**
- Invoice number
- Debtor name
- Investment amount (UZS)
- Expected return (UZS)
- Due date
- Risk grade
- Status badge (pending / confirmed / settled / defaulted)

---

## Language Switching

FactorFinance supports three languages, switchable via flag icons in the navbar:

| Flag | Language | Code |
|------|----------|------|
| 🇬🇧 | English | `en` |
| 🇺🇿 | O'zbekcha (Uzbek) | `uz` |
| 🇷🇺 | Russian | `ru` |

Click any flag to instantly switch the entire interface. Your preference is saved in a cookie and persists across sessions.

**Uzbek homepage:**

![Uzbek Homepage](../screenshots/11-home-uz.png)

**Russian homepage:**

![Russian Homepage](../screenshots/13-home-ru.png)

---

## Technical Details

- **Stack**: FastHTML (Python) + HTMX + Tailwind CSS
- **Database**: PostgreSQL (`factorfinance` schema)
- **Currency**: Uzbek Som (UZS)
- **Debtors**: Real Uzbek companies (Navoi Mining, UzAuto Motors, Artel, etc.)
- **Deployment**: Docker with auto-migration on startup
