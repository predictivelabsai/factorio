"""Single money formatter for the app (multi-currency, USD default).

Stored amounts are UZS-scale (the synthetic data is denominated in UZS). For a
realistic, meaningful demo we display them in a chosen currency — **USD by
default** (``DISPLAY_CURRENCY``) — converting via a fixed FX rate. So a
480,000,000-UZS invoice shows as ~$38,000 rather than an absurd $480M.

All monetary UI goes through ``fmt_money`` (and the ``fmt_uzs`` back-compat
alias in ``app_routes._shared``).
"""

from __future__ import annotations

from utils.config import settings

# UZS per 1 unit of the display currency (illustrative demo rates).
_FX_UZS_PER = {"USD": 12600.0, "EUR": 13700.0, "GBP": 16000.0, "UZS": 1.0}
_SYMBOL = {"USD": "$", "EUR": "€", "GBP": "£", "UZS": "UZS "}


def display_currency() -> str:
    c = (settings().display_currency or "USD").upper()
    return c if c in _FX_UZS_PER else "USD"


def fmt_money(amount_uzs, currency: str | None = None) -> str:
    """Format a UZS-scale stored amount in the display currency (default USD)."""
    cur = (currency or display_currency()).upper()
    rate = _FX_UZS_PER.get(cur, 1.0)
    try:
        v = float(amount_uzs or 0) / rate
    except (TypeError, ValueError):
        v = 0.0
    if cur == "UZS":
        return f"UZS {v:,.0f}"
    return f"{_SYMBOL.get(cur, '')}{v:,.0f}"
