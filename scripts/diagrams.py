"""Shared, bilingual Mermaid diagrams for the proposal and the user guide.

These are the money-flow and user-journey diagrams the two document sets share.
They are authored in English and Russian and rendered to PNG via kroki.io so
both WeasyPrint (PDF) and python-pptx (PPTX) can embed them, and both the
proposal and the guide can reference the same files:

    docs/img/<lang>-<key>.png     e.g. docs/img/en-15-money-flow.png

Run render_bilingual() before building either document set (both build scripts
call it; kroki rendering is idempotent).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img"

_INIT = "%%{init: {'theme':'neutral'}}%%\n"

# key -> {en, ru} Mermaid source. Keys are numbered to sit after the guide's
# AI slides (13, 14) and to keep docs/img tidy.
BILINGUAL = {
    # ── Money & payments — the box diagram, with the payer (debtor) ─────────
    "15-money-flow": {
        "en": _INIT + """flowchart LR
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
""",
        "ru": _INIT + """flowchart LR
    SELLER["Продавец (МСБ)<br/>поставщик"]
    PAYER["Плательщик / дебитор<br/>покупатель-должник"]
    CAP["Источник капитала<br/>баланс банка ·<br/>инвесторы · SPV в DIFC"]
    subgraph PLAT["Платформа Factorio — под брендом Universalbank"]
        ADV["Аванс и<br/>уступка счёта"]
        COL["Сбор платежей<br/>и расчёт"]
        FEE["Комиссия платформы<br/>(б.п. от объёма)"]
    end
    SELLER -->|"1 · товар + э-счёт"| PAYER
    SELLER -->|"2 · уступает счёт"| ADV
    CAP -->|"3 · финансирует аванс"| ADV
    ADV -->|"4 · аванс ~85% сейчас"| SELLER
    PAYER -->|"5 · платит 100% в срок"| COL
    COL -->|"6 · остаток (~15% − комиссия)"| SELLER
    COL -->|"7 · основная сумма + доход"| CAP
    COL -->|"8 · комиссия платформы"| FEE
    style CAP fill:#C8A24B,color:#14231B
    style PAYER fill:#2563EB,color:#fff
    style PLAT fill:#DCF3E8
""",
    },

    # ── Borrower / origination journey ──────────────────────────────────────
    "16-origination-journey": {
        "en": _INIT + """flowchart LR
    O1["Seller signs up<br/>bank KYC"] --> O2["Invoice imported<br/>from SoliqOnline"]
    O2 --> O3["Requests financing<br/>AI triage (chat)"]
    O3 --> O4["Debtor scoring +<br/>indicative terms"]
    O4 --> O5["Bank one-click<br/>approval"]
    O5 --> O6["Collateral registered<br/>CBU · &lt; 60 min"]
    O6 --> O7["Advance received<br/>24–48 h"]
    style O3 fill:#DCF3E8
    style O7 fill:#C8A24B,color:#14231B
""",
        "ru": _INIT + """flowchart LR
    O1["Продавец регистрируется<br/>KYC банка"] --> O2["Счёт импортирован<br/>из SoliqOnline"]
    O2 --> O3["Запрос финансирования<br/>AI-триаж (чат)"]
    O3 --> O4["Скоринг дебитора +<br/>индикативные условия"]
    O4 --> O5["Одобрение банка<br/>в один клик"]
    O5 --> O6["Залог зарегистрирован<br/>ЦБ · &lt; 60 мин"]
    O6 --> O7["Аванс получен<br/>24–48 ч"]
    style O3 fill:#DCF3E8
    style O7 fill:#C8A24B,color:#14231B
""",
    },

    # ── Investor journey ────────────────────────────────────────────────────
    "17-investor-journey": {
        "en": _INIT + """flowchart LR
    V1["Investor onboards<br/>KYC / accreditation"] --> V2["Commits capital<br/>marketplace or SPV"]
    V2 --> V3["Auto-invest or<br/>pick invoices"]
    V3 --> V4["Position held<br/>AI reporting on demand"]
    V4 --> V5["Debtor pays<br/>at maturity"]
    V5 --> V6["Principal + return<br/>distributed"]
    style V4 fill:#DCF3E8
    style V6 fill:#C8A24B,color:#14231B
""",
        "ru": _INIT + """flowchart LR
    V1["Инвестор проходит<br/>KYC / аккредитацию"] --> V2["Вносит капитал<br/>маркетплейс или SPV"]
    V2 --> V3["Автоинвест или<br/>выбор счетов"]
    V3 --> V4["Позиция открыта<br/>AI-отчётность по запросу"]
    V4 --> V5["Дебитор платит<br/>в срок"]
    V5 --> V6["Основная сумма +<br/>доход распределены"]
    style V4 fill:#DCF3E8
    style V6 fill:#C8A24B,color:#14231B
""",
    },

    # ── Decomposition — origination first, investor/SPV later ───────────────
    "18-decomposition": {
        "en": _INIT + """flowchart LR
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
""",
        "ru": _INIT + """flowchart LR
    subgraph MA["Модуль A · Origination — запускаем первым"]
        A1["Онбординг + SoliqOnline"]
        A2["AI-триаж + скоринг"]
        A3["Одобрение банка + аванс"]
    end
    CAP{{"Слой капитала<br/>(подключаемый)"}}
    subgraph MB["Модуль B · Инвесторы и SPV — запускаем позже, отдельно"]
        B1["Маркетплейс инвесторов"]
        B2["SPV в DIFC · межд. капитал"]
        B3["Отчётность + расчёты"]
    end
    BANK["Баланс банка"] --> CAP
    MA -->|"профинансированные активы"| CAP
    CAP --> MB
    style MA fill:#DCF3E8
    style MB fill:#FCEFC8
    style CAP fill:#C8A24B,color:#14231B
""",
    },
}


def _render(src: str, out: Path) -> None:
    req = urllib.request.Request(
        "https://kroki.io/mermaid/png",
        data=src.encode("utf-8"),
        headers={"Content-Type": "text/plain",
                 "User-Agent": "Mozilla/5.0 (Factorio diagram builder)"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        out.write_bytes(resp.read())


def render_bilingual() -> None:
    """Render every bilingual diagram to docs/img/<lang>-<key>.png (best effort)."""
    IMG.mkdir(parents=True, exist_ok=True)
    for key, langs in BILINGUAL.items():
        for lang, src in langs.items():
            out = IMG / f"{lang}-{key}.png"
            try:
                _render(src, out)
                print(f"  diagram {out.relative_to(ROOT)}  ({out.stat().st_size/1024:.0f} KB)")
            except Exception as e:  # noqa: BLE001 - best effort
                print(f"  WARNING: could not render {lang}-{key}: {e}")


if __name__ == "__main__":
    render_bilingual()
