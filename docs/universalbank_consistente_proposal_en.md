# Factorio for Universalbank
## AI-native invoice financing · an international-investor SPV · UAE entry

Prepared by Consistente Ltd · Tallinn · info@consistente.tech · consistente.tech

A proposal by **Consistente Ltd** to build and operate a next-generation, white-label invoice-financing platform for Universalbank — more efficient than the incumbent, priced on volume alone, with an AI core, an international-investor SPV, and a route into the UAE.

---

<p class="eyebrow">Executive summary</p>

## Three moves, one platform

- **The gap.** Every Uzbek bank *rents* its factoring product from OzPlanet or FinMakon — Universalbank included (OzPlanet cooperation agreement, Sept 2024). None *owns* the product, the customer relationship or the data.
- **1 · Own the platform.** A white-label, AI-native platform Universalbank runs under its own brand — the bank owns the product, customers and data — priced on **financed volume only**.
- **2 · International capital.** An SPV module lets global — and specifically Gulf — investors fund Uzbek receivables. OzPlanet and FinMakon take **no foreign or retail money**, so this is a clean, uncontested differentiator.
- **3 · UAE entry.** A **DIFC SPV** and a phased Shariah programme (Murabaha → Wakala → Sukuk) to reach Dubai / DIFC Islamic capital.
- **Decomposable & live today.** Deploy origination first, add the investor / SPV layer later — and the chat-based loan triage and investor reporting are **already running** in the app.

---

<p class="eyebrow">The opportunity</p>

## Uzbekistan built the perfect rails for invoice finance

- **SoliqOnline** — the State Tax Committee's platform — has validated, timestamped and archived every B2B e-invoice in the country since **January 2020**.
- **Didox** connects **350,000+ organisations** to it and integrates with 1C — a ready-made supplier base that already exchanges invoices electronically.
- Every invoice is government-verified and buyer-confirmed on official record — **fraud and debtor-confirmation, factoring's hardest problems, are solved at source.**
- The market is scaling fast: the **CBU reports ~10.6 trillion soums (~$835M) factored in Jan–Sep 2025**, about **half of it digital** — against a **~$2bn** addressable market that is still lightly penetrated.

---

<p class="eyebrow">Why now</p>

## The regulatory window is open

- **Presidential Decree No. 106 (Aug 2024)** mandated banks to offer factoring.
- **ZRU-1058 (Apr 2025)** amended the Civil Code to give factoring full legal force, and mandates automated API registration of the bank's collateral priority in the **CBU registry** — within about an hour of approval.
- **No new licence** is required: Universalbank's existing CBU licence covers this; Factorio operates as white-label technology under the bank's umbrella.
- **No Uzbek bank has yet built a production-grade SoliqOnline factoring stack with an AI core** — the first mover captures structural advantage.

---

<p class="eyebrow">The incumbents</p>

## OzPlanet & FinMakon own the market — as aggregators

| Dimension | OzPlanet | FinMakon | Factorio (Consistente) |
| --- | --- | --- | --- |
| Model | Aggregator; bank-set rates | Aggregator (Didox-backed) | **White-label marketplace** — bank owns it |
| Digital share (Q3 2025) | 56% of digital volume | 44% of digital volume | New entrant — builds share |
| Funding sources | Banks / MFOs only | Banks / factoring cos | **Banks + investors + retail + SPV** |
| Foreign / retail capital | **No** | **No** | **Yes** — SPV + marketplace |
| Bank owns product & data | No — OzPlanet does | No — FinMakon does | **Yes** — fully the bank's |
| AI core | Rule-based; nascent | Nascent | **Grok chat triage + reporting**, doc intelligence |
| Pricing to bank | Per-transaction commission | Per-transaction commission | **Volume-only bps** (no SaaS licence) |

> Universalbank already signed a cooperation agreement with OzPlanet (Sept 2024) — so it knows the model. The point of this proposal is not to rent a better aggregator, but to own the product outright. (Market data: CBU, Q3 2025.)

---

<p class="eyebrow">The strategic gap</p>

## No Uzbek bank owns its factoring product

- Today a bank connecting to OzPlanet or FinMakon is a **funding partner on someone else's platform** — the aggregator owns the brand, the customer relationship and the data.
- That is a strategic dependency: the bank cannot differentiate, cannot cross-sell off its own data, and cannot switch without losing the clients.
- **Factorio flips this.** Universalbank runs the platform under its **own brand**, owns **all customer and transaction data**, and can export and move it — no platform lock-in.
- Same government rails (SoliqOnline, CBU registry), same speed — but the bank owns the asset instead of renting the rails. That ownership is the real product.

---

<p class="eyebrow">How it works</p>

## How the money moves — and who gets paid

```mermaid
%%{init: {'theme':'neutral'}}%%
flowchart LR
    SELLER["Seller (SME)<br/>supplier"]
    PAYER["Payer / debtor<br/>the buyer who owes"]
    CAP["Capital source<br/>bank balance sheet ·<br/>investors · DIFC SPV"]
    subgraph PLAT["Factorio platform — Universalbank-branded"]
        ADV["Advance &<br/>invoice assignment"]
        COL["Collections &<br/>settlement"]
        FEE["Platform fee<br/>(volume-based bps)"]
    end
    SELLER -->|"1 · goods + e-invoice"| PAYER
    SELLER -->|"2 · assigns invoice"| ADV
    CAP -->|"3 · funds the advance"| ADV
    ADV -->|"4 · advance ~85% now"| SELLER
    PAYER -->|"5 · pays 100% at maturity"| COL
    COL -->|"6 · net balance (~15% − fee)"| SELLER
    COL -->|"7 · principal + return"| CAP
    COL -->|"8 · platform fee"| FEE
    style CAP fill:#C8A24B,color:#14231B
    style PAYER fill:#2563EB,color:#fff
    style PLAT fill:#DCF3E8
```

*Money & payment flow — seller, payer (debtor), platform, capital*

- The **payer (debtor)** is the anchor: a specific, buyer-confirmed obligation on the SoliqOnline record.
- The platform advances ~85% now from the **capital source** (bank, investor or SPV); at maturity the payer settles 100% and the waterfall pays seller, capital and platform.
- Because the flow is identical regardless of who funds it, the **capital layer is pluggable** — bank first, investors/SPV later.

---

<p class="eyebrow">Pillar 1 · A better platform</p>

## AI at the core, not bolted on

- The same end-to-end factoring workflow — submit, verify, fund, settle — but with AI woven through triage, scoring, documents and reporting.
- Built on a lean, server-rendered stack (FastHTML + PostgreSQL) — fast to change, cheap to run, easy to white-label under the bank's brand.
- Trilingual by design (English · Oʻzbekcha · Russian); the AI answers in the user's language.
- The next three slides detail the AI, the credit-scoring engine, and the commercial model.

---

<p class="eyebrow">Journey · Borrower (origination)</p>

## The seller's journey — sign-up to cash in 24–48h

```mermaid
%%{init: {'theme':'neutral'}}%%
flowchart LR
    O1["Seller signs up<br/>bank KYC"] --> O2["Invoice imported<br/>from SoliqOnline"]
    O2 --> O3["Requests financing<br/>AI triage (chat)"]
    O3 --> O4["Debtor scoring +<br/>indicative terms"]
    O4 --> O5["Bank one-click<br/>approval"]
    O5 --> O6["Collateral registered<br/>CBU · &lt; 60 min"]
    O6 --> O7["Advance received<br/>24–48 h"]
    style O3 fill:#DCF3E8
    style O7 fill:#C8A24B,color:#14231B
```

*Origination: SoliqOnline import → AI triage → one-click approval → advance*

- Manual bank involvement is a **single approval click** on a pre-populated screen; everything else is automated.
- The invoice is imported and verified from SoliqOnline; the debtor is scored; collateral is registered with the CBU in **under 60 minutes**.
- This is **Module A** — it stands alone and can go live first, funded entirely by the bank's balance sheet.

---

<p class="eyebrow">Pillar 1 · AI</p>

## Two conversational surfaces, one Grok core

```mermaid
%%{init: {'theme':'neutral'}}%%
flowchart LR
    S["Seller message<br/>(natural language)"] --> TRI["Triage assistant<br/>app_routes/assistant.py"]
    I["Investor question"] --> REP["Reporting assistant"]
    TRI --> TOOLS["Tools<br/>lookup_debtor · get_soliq_invoice<br/>indicative_terms"]
    REP --> CTX["Grounding<br/>investor's live positions"]
    TOOLS --> GROK[["Grok · x.ai"]]
    CTX --> GROK
    GROK --> OUT1["Indicative grade A–D<br/>advance rate · next documents"]
    GROK --> OUT2["Grounded portfolio answer<br/>(figures trace to real data)"]
    style GROK fill:#1F5D43,color:#fff
    style OUT1 fill:#DCF3E8
    style OUT2 fill:#DCF3E8
```

*Chat-based loan triage and chat-based investor reporting*

- **Triage** turns a seller's plain-language description into an indicative grade, advance rate and document list — in seconds.
- **Reporting** answers an investor's questions grounded in their own live positions — no invented figures.
- Grok scores and explains; a human always approves. Every AI decision is logged and auditable.

---

<p class="eyebrow">Pillar 1 · Credit scoring</p>

## Open-banking-style scoring, Uzbek edition

```mermaid
%%{init: {'theme':'neutral'}}%%
flowchart LR
    A["SoliqOnline<br/>invoice + tax history"] --> FE["Feature engineering"]
    B["Open banking<br/>cash-flow signals"] --> FE
    C["CRIF bureau<br/>obligations · defaults"] --> FE
    FE --> M["Scoring model<br/>gradient-boosted + rules"]
    M --> D["Risk grade A–D<br/>advance rate · price"]
    D --> L["Grok<br/>plain-language rationale<br/>+ adverse-action reasons"]
    D --> AUD[("Decision audit<br/>versioned · reproducible")]
    style M fill:#1F5D43,color:#fff
    style D fill:#C8A24B,color:#14231B
    style L fill:#DCF3E8
```

*Plaid-style data fusion adapted to Uzbekistan's rails*

- The Plaid model is *connect an account, read the cash flows, decide*. In Uzbekistan the richest feed is **SoliqOnline** — verified invoices and tax-declared turnover — plus **bank transaction data** and the **CRIF** bureau.
- A model produces the **grade, advance rate and price**; Grok writes the **plain-language rationale and adverse-action reasons**.
- Every decision is **versioned and reproducible** — Consistente's core methodology, and what a regulator will ask for.

---

<p class="eyebrow">Economics</p>

## What the bank earns on one invoice

| Cash flow · $10,000 invoice · 85% · 60d · 5% | Amount | Direction | Day |
| --- | --- | --- | --- |
| Advance to seller (85%) | $8,500 | Platform → seller | Day 1 |
| Payer (debtor) pays in full | $10,000 | Payer → collection | Day 60 |
| Net balance released to seller | $1,500 | Platform → seller | Day 60 |
| Discount income (gross) | $500 | Capital keeps | Day 60 |
| Platform fee (volume-based) | ≈ $13 | Bank → Consistente | Day 60 |
| **Net income on the invoice** | **≈ $487** | **Capital keeps** | **Day 60** |
| **Annualised return on capital** | **≈ 30% p.a.** | — | — |

> Illustrative, per the standard SoliqOnline-verified structure. ~30% annualised on deployed capital compares with 22–28% on unsecured SME lending — at lower risk: the invoice is government-verified, the payer has confirmed the obligation, and the bank holds a registered CBU priority claim. Bank stays profitable to a ~4% default rate.

---

<p class="eyebrow">Pillar 1 · Commercial model</p>

## Volume-only pricing — aligned with the bank

| Monthly financed volume | Platform fee (bps of financed volume) |
| --- | --- |
| Up to UZS 50 bn | 120 bps |
| UZS 50–200 bn | 90 bps |
| UZS 200–500 bn | 70 bps |
| Over UZS 500 bn | 55 bps |

> Illustrative. No SaaS licence, no per-seat, no setup fee — Consistente is paid only when the bank finances an invoice. Options on the table: a revenue-share alternative (a small % of the bank's discount income instead of bps), 12-month bank exclusivity in Uzbekistan, and a Year-3 deferred-equity option structured as new shares (non-dilutive, no board/veto rights). International SPV module: ~60 bps p.a. on invested AUM + a performance share above a hurdle. Final figures to be set with Universalbank.

---

<p class="eyebrow">Pillar 2 · International capital</p>

## An SPV that opens Uzbek receivables to the world

```mermaid
%%{init: {'theme':'neutral'}}%%
flowchart TB
    POOL[("Uzbek invoice pool<br/>SoliqOnline-verified · buyer-confirmed")]
    FACT["Factorio platform<br/>Universalbank — originator & servicer"]
    SPV["DIFC SPV<br/>(bankruptcy-remote)"]
    subgraph INV["International investors"]
        CONV["Conventional<br/>note / participation"]
        ISL["Shariah tracks<br/>Murabaha → Wakala → Sukuk"]
    end
    POOL --> FACT --> SPV
    SPV --> CONV
    SPV --> ISL
    CONV -->|USD capital| SPV
    ISL -->|USD capital| SPV
    SPV -->|funding| FACT
    FACT -->|collections| SPV
    SPV -->|profit distribution| INV
    style SPV fill:#1F5D43,color:#fff
    style ISL fill:#C8A24B,color:#14231B
    style POOL fill:#2563EB,color:#fff
```

*Invoice pool → Factorio → DIFC SPV → international investors*

- Universalbank remains **originator and servicer**; a bankruptcy-remote **SPV** holds the investor-facing interest and channels foreign capital into the invoice pool.
- Two tracks off the **same asset base**: a **conventional** note/participation for institutional investors, and **Shariah** structures for Gulf capital.
- Investors get the same grounded, AI-assisted reporting — in their language — plus statements and a clean audit trail.

---

<p class="eyebrow">Journey · Investor</p>

## The investor's journey — onboarding to distribution

```mermaid
%%{init: {'theme':'neutral'}}%%
flowchart LR
    V1["Investor onboards<br/>KYC / accreditation"] --> V2["Commits capital<br/>marketplace or SPV"]
    V2 --> V3["Auto-invest or<br/>pick invoices"]
    V3 --> V4["Position held<br/>AI reporting on demand"]
    V4 --> V5["Debtor pays<br/>at maturity"]
    V5 --> V6["Principal + return<br/>distributed"]
    style V4 fill:#DCF3E8
    style V6 fill:#C8A24B,color:#14231B
```

*Investor: onboard → commit capital → hold with AI reporting → get paid*

- Retail, institutional and Gulf investors onboard once (KYC / accreditation), then fund via the **marketplace** or the **SPV**.
- They hold positions with **on-demand AI portfolio reporting**; at maturity, principal + return are distributed automatically.
- This is **Module B** — it plugs onto the same origination engine later, without changing anything a seller or the bank does.

---

<p class="eyebrow">Delivery · Decomposability</p>

## Two modules — buy one, or both, in sequence

```mermaid
%%{init: {'theme':'neutral'}}%%
flowchart LR
    subgraph MA["Module A · Origination — deploy first"]
        A1["Onboarding + SoliqOnline"]
        A2["AI triage + scoring"]
        A3["Bank approval + advance"]
    end
    CAP{{"Capital layer<br/>(pluggable)"}}
    subgraph MB["Module B · Investors &amp; SPV — deploy later, independently"]
        B1["Investor marketplace"]
        B2["DIFC SPV · international capital"]
        B3["Investor reporting + settlement"]
    end
    BANK["Bank balance sheet"] --> CAP
    MA -->|"funded assets"| CAP
    CAP --> MB
    style MA fill:#DCF3E8
    style MB fill:#FCEFC8
    style CAP fill:#C8A24B,color:#14231B
```

*Origination (Module A) and Investors/SPV (Module B) are independently deployable*

- **Module A — Origination** can be Universalbank's whole first phase: bank-funded factoring, live in weeks, immediately satisfying the Decree-106 mandate.
- **Module B — Investors & SPV** adds the marketplace and DIFC/international capital later, over the same engine, with no rework.
- The **capital layer is the seam**: swap or add funding sources without touching origination — de-risking the programme and the investment.

---

<p class="eyebrow">Pillar 3 · UAE entry</p>

## A phased Shariah programme for DIFC capital

| Criterion | Murabaha SCF | Wakala Fund | Sukuk | Musharaka |
| --- | --- | --- | --- | --- |
| Shariah purity | High | High | High | Highest |
| Complexity | Low | Low–Med | High | Medium |
| Time to market | Fastest | Fast | Slowest | Medium |
| Dubai investor appeal | Medium | High | Very high | High |
| Capital per deal | Small–Med | Medium | Large | Med–Large |
| Regulatory need | Fatwa only | Fatwa + fund | Fatwa + DFSA | Fatwa + fund |
| Best for | Pilot | Family offices | Institutional | Strategic partners |

> Recommended path: run them in sequence — Murabaha SCF pilot (M6–12) → Wakala fund → Sukuk. Each phase builds the track record that makes the next credible. All require an AAOIFI-accredited fatwa before deployment.

---

<p class="eyebrow">Pillar 3 · Why Dubai / DIFC</p>

## The yield spread is the story

- Uzbek factoring yields of **~20–30% p.a.** against Gulf Islamic money-market returns of **~4–6%** — an exceptional spread for the risk, given SoliqOnline's structural protections.
- **Short duration** (30–90-day rolling receivables) is rare and highly demanded by Gulf liquidity managers.
- Uzbek receivables are **uncorrelated** with Gulf real estate, regional equities or oil — genuine diversification.
- **DIFC (DFSA)** and **ADGM (FSRA)** both have mature Islamic-finance frameworks and recognise SPV/Sukuk structures; the UAE's Federal Decree-Law No. 50 of 2022 codifies the contracts.

---

<p class="eyebrow">Architecture</p>

## One process, AI-native, integration-ready

```mermaid
%%{init: {'theme':'neutral'}}%%
flowchart TB
    USER(["Sellers & Investors<br/>(browser · trilingual)"])
    subgraph APP["Factorio — one FastHTML process"]
        LAND["Landing site"]
        PROD["Investor app<br/>dashboard · marketplace · portfolio"]
        AITRI["AI triage<br/>/app/triage"]
        AIREP["AI reporting<br/>/app/assistant"]
        SCORE["Credit-scoring engine"]
        SPVM["SPV / investor module"]
    end
    subgraph DATA["PostgreSQL — factorio schema"]
        DB[("invoices · funding · investments<br/>companies · settlements<br/>ai_* · credit_*")]
    end
    subgraph EXT["External services"]
        XAI[["Grok LLM<br/>x.ai"]]
        SOLIQ[["SoliqOnline / Didox<br/>e-invoice API"]]
        OB[["Open banking<br/>bank transaction data"]]
        CRIF[["CRIF credit bureau"]]
        CBU[["CBU collateral registry"]]
        CUST[["DIFC SPV · custodian<br/>international investors"]]
    end
    USER --> LAND
    USER --> PROD
    USER --> AITRI
    USER --> AIREP
    AITRI --> XAI
    AIREP --> XAI
    PROD --> DB
    AITRI --> DB
    AIREP --> DB
    SCORE --> SOLIQ
    SCORE --> OB
    SCORE --> CRIF
    SCORE --> DB
    PROD --> CBU
    SPVM --> CUST
    SPVM --> DB
    style XAI fill:#1F5D43,color:#fff
    style SOLIQ fill:#2563EB,color:#fff
    style OB fill:#2563EB,color:#fff
    style CRIF fill:#2563EB,color:#fff
    style CUST fill:#C8A24B,color:#14231B
    style AITRI fill:#DCF3E8
    style AIREP fill:#DCF3E8
    style SCORE fill:#DCF3E8
```

*Target system architecture with AI components highlighted*

- A single FastHTML process serves the landing site, the investor app and the AI assistants; PostgreSQL holds the factoring and AI data.
- Clean integration seams to **SoliqOnline/Didox**, **open banking**, **CRIF**, the **CBU registry**, and the **DIFC SPV / custodian**.
- Grok (x.ai) is reached over an OpenAI-compatible interface — the model id is configuration, avoiding vendor lock-in.

---

<p class="eyebrow">Proof · Working today</p>

## The AI is not a slide — it's shipped

![Live chat-based invoice triage in the Factorio app screen](img/en-13-ai-triage.png)

<p class="caption">Live chat-based invoice triage in the Factorio app</p>

- A seller describes an invoice in a sentence; the assistant returns an indicative risk band, advance rate and next-document list.
- Built on Grok (x.ai), trilingual, with graceful fallback and full audit logging — the same pattern extends to scoring and reporting.

---

<p class="eyebrow">Delivery</p>

## From prototype to regional platform

```mermaid
%%{init: {'theme':'neutral'}}%%
flowchart LR
    P0["Phase 0 · now<br/>Working AI prototype<br/>triage + reporting shipped"] --> P1["Phase 1 · M1–3<br/>Platform GA + streaming<br/>SoliqOnline integration"]
    P1 --> P2["Phase 2 · M3–6<br/>Open-banking credit scoring<br/>volume pricing live"]
    P2 --> P3["Phase 3 · M6–12<br/>DIFC SPV · first int'l capital<br/>Murabaha pilot"]
    P3 --> P4["Phase 4 · Y2+<br/>Wakala fund → Sukuk<br/>regional scale"]
    style P0 fill:#DCF3E8
    style P2 fill:#1F5D43,color:#fff
    style P4 fill:#C8A24B,color:#14231B
```

*Phased rollout — each phase funds the next*

- **Phase 0 (now):** AI triage + reporting prototype live.
- **Phases 1–2 (M1–6):** platform GA, SoliqOnline integration, open-banking scoring, volume pricing.
- **Phases 3–4 (M6+):** DIFC SPV and first international capital, then the Wakala → Sukuk sequence and regional scale.

---

<p class="eyebrow">Why Consistente</p>

## Production AI, delivered consistently

- Consistente Ltd (Tallinn, EU) builds **production-grade AI for enterprises** — with reproducible pipelines, versioned models and inspectable prompts, not black boxes.
- Precedents across **financial services and regulated sectors**: LSEG, DBRS Morningstar, ARM, Microsoft.
- Core capabilities map directly onto this project: **document intelligence**, **applied forecasting/scoring**, and **agentic workflows** with human review.
- EU-based, audit-first — the right profile for a bank building AI a regulator will scrutinise.

---

<p class="eyebrow">Next steps</p>

## What we propose to do first

- **1.** Agree the white-label scope and the volume-based commercial terms.
- **2.** Stand up a pilot on live SoliqOnline data; ship the platform GA with the AI triage and scoring engine.
- **3.** In parallel, begin DIFC SPV and fatwa preparation so international capital can follow the operating book.
- **Contact:** Consistente Ltd · info@consistente.tech · consistente.tech
