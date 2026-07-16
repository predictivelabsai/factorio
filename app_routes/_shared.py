"""Shared helpers for the /app/* investor product.

Investor identity (cookie-based switcher — no password, per product decision),
the app sub-navigation chrome, the UZS money formatter, and small reporting
helpers (days-late aging buckets) used across the cockpit, statement and
dashboard.
"""

from __future__ import annotations

from datetime import date

from fasthtml.common import Div, Span, A, Nav, Ul, Li, Select, Option
from starlette.responses import RedirectResponse

from app import rt
from utils.i18n import t, DEFAULT_LANG

try:
    from db import fetch_all
    _HAS_DB = True
except Exception:  # pragma: no cover - DB optional in some environments
    _HAS_DB = False


# ── Money ───────────────────────────────────────────────────────────────

from utils.money import fmt_money  # noqa: E402


def fmt_uzs(amount) -> str:
    """Back-compat name — formats a stored (UZS-scale) amount in the display
    currency (USD by default). See utils.money.fmt_money."""
    return fmt_money(amount)


# ── Investor identity (no-password switcher) ────────────────────────────

def list_investors() -> list[dict]:
    if not _HAS_DB:
        return []
    try:
        return fetch_all(
            "SELECT id, username, email FROM factorio.users "
            "WHERE role = 'investor' ORDER BY id"
        )
    except Exception:
        return []


def current_investor(req, investors: list[dict] | None = None) -> dict | None:
    """Resolve the 'logged-in' investor from the `investor` cookie.

    Falls back to the first investor so the app is never empty in a demo.
    """
    investors = investors if investors is not None else list_investors()
    if not investors:
        return None
    cookie = req.cookies.get("investor") if req is not None else None
    if cookie:
        for inv in investors:
            if str(inv["id"]) == str(cookie):
                return inv
    return investors[0]


@rt("/app/set-investor")
def set_investor(req, investor_id: int = 0):
    referer = req.headers.get("referer", "/app")
    resp = RedirectResponse(referer, status_code=303)
    resp.set_cookie("investor", str(investor_id),
                    max_age=365 * 24 * 3600, httponly=False, samesite="lax")
    return resp


# ── Roles / RBAC (demo-grade: cookie-based role switcher, no password) ─────

ROLES = ("investor", "seller", "payer", "admin")
ADMIN_SUBROLES = ("ops", "credit", "collections", "finance", "compliance", "exec", "super")


def current_role(req) -> str:
    # A real logged-in session wins; otherwise fall back to the demo cookie switcher.
    s = getattr(req, "session", None) if req is not None else None
    if s and s.get("role"):
        return s["role"] if s["role"] in ROLES else "investor"
    r = req.cookies.get("role", "investor") if req is not None else "investor"
    return r if r in ROLES else "investor"


def current_subrole(req) -> str:
    s = getattr(req, "session", None) if req is not None else None
    if s and s.get("uid") and s.get("subrole"):
        return s["subrole"] if s["subrole"] in ADMIN_SUBROLES else "ops"
    r = req.cookies.get("admin_role", "ops") if req is not None else "ops"
    return r if r in ADMIN_SUBROLES else "ops"


@rt("/app/set-role")
def set_role(req, role: str = "investor", admin_role: str = ""):
    referer = req.headers.get("referer", "/app")
    resp = RedirectResponse(referer, status_code=303)
    if role in ROLES:
        resp.set_cookie("role", role, max_age=365 * 24 * 3600, httponly=False, samesite="lax")
    if admin_role in ADMIN_SUBROLES:
        resp.set_cookie("admin_role", admin_role, max_age=365 * 24 * 3600, httponly=False, samesite="lax")
    return resp


# ── Aging buckets (days past due) ───────────────────────────────────────

# (key, lower_inclusive, upper_inclusive) — upper None means open-ended.
AGING_BUCKETS = [
    ("bkt_in_payment", None, 0),     # due in the future / today → still in payment
    ("bkt_late_1_14", 1, 14),
    ("bkt_late_15_30", 15, 30),
    ("bkt_late_31_60", 31, 60),
    ("bkt_late_61_120", 61, 120),
    ("bkt_late_120", 121, None),
]


def aging_bucket_key(days_late: int) -> str:
    """Map days-past-due (negative = not yet due) to an aging-bucket key."""
    if days_late <= 0:
        return "bkt_in_payment"
    for key, lo, hi in AGING_BUCKETS[1:]:
        if hi is None:
            return key
        if lo <= days_late <= hi:
            return key
    return "bkt_late_120"


def days_late(due, today: date | None = None) -> int:
    """Positive when overdue, negative/zero when not yet due."""
    today = today or date.today()
    d = due.date() if hasattr(due, "date") else due
    return (today - d).days


# ── App chrome ──────────────────────────────────────────────────────────

# Role-scoped navigation. (i18n key, href) per role.
_NAV_BY_ROLE = {
    "investor": [
        ("nav_dashboard", "/app"),
        ("mkt_eyebrow", "/app/marketplace"),
        ("port_eyebrow", "/app/portfolio"),
        ("nav_statement", "/app/statement"),
        ("nav_autoinvest", "/app/auto-invest"),
        ("nav_triage", "/app/triage"),
        ("nav_assistant", "/app/assistant"),
    ],
    "seller": [
        ("nav_seller", "/app/seller"),
        ("nav_triage", "/app/triage"),
        ("mkt_eyebrow", "/app/marketplace"),
    ],
    "payer": [
        ("nav_payer", "/app/payer"),
    ],
    "admin": [
        ("nav_admin", "/app/admin"),
        ("nav_admin_onboarding", "/app/admin/onboarding"),
        ("nav_admin_risk", "/app/admin/risk"),
        ("nav_admin_funding", "/app/admin/funding"),
        ("nav_admin_reports", "/app/admin/reports"),
        ("nav_admin_audit", "/app/admin/audit"),
    ],
}

# Back-compat alias (dashboard.py imports app_page/current_investor only).
_APP_LINKS = _NAV_BY_ROLE["investor"]


def _sel_cls():
    return ("bg-bg-elevated border border-line-bright rounded-full px-3 py-1.5 "
            "text-sm text-ink focus:outline-none focus:border-accent cursor-pointer")


def _investor_switcher(investor: dict | None, investors: list[dict], lang: str):
    if not investors:
        return Span("", cls="hidden")
    opts = [
        Option(inv["username"], value=str(inv["id"]),
               selected=bool(investor and inv["id"] == investor["id"]))
        for inv in investors
    ]
    return Div(
        Span(t("app_viewing_as", lang),
             cls="text-[11px] font-mono uppercase tracking-widest text-ink-dim hidden sm:inline"),
        Select(*opts,
               onchange=("document.cookie='investor='+this.value+"
                         "';path=/;max-age=31536000;samesite=lax';location.reload();"),
               cls=_sel_cls()),
        cls="flex items-center gap-2",
    )


def _role_switcher(role: str, subrole: str, lang: str):
    role_opts = [Option(t(f"role_{r}", lang), value=r, selected=(r == role)) for r in ROLES]
    home = {"admin": "/app/admin", "seller": "/app/seller", "payer": "/app/payer"}
    # switching role sets the cookie and jumps to that role's home
    role_sel = Select(
        *role_opts,
        onchange=("document.cookie='role='+this.value+';path=/;max-age=31536000;samesite=lax';"
                  "var h={'admin':'/app/admin','seller':'/app/seller','payer':'/app/payer'};"
                  "location.href=h[this.value]||'/app';"),
        cls=_sel_cls(),
    )
    els = [Span(t("app_role_label", lang),
                cls="text-[11px] font-mono uppercase tracking-widest text-ink-dim hidden sm:inline"),
           role_sel]
    if role == "admin":
        sub_opts = [Option(t(f"subrole_{s}", lang), value=s, selected=(s == subrole)) for s in ADMIN_SUBROLES]
        els.append(Select(
            *sub_opts,
            onchange=("document.cookie='admin_role='+this.value+"
                      "';path=/;max-age=31536000;samesite=lax';location.reload();"),
            cls=_sel_cls()))
    return Div(*els, cls="flex items-center gap-2")


def app_subnav(current_path: str, lang: str,
               investor: dict | None, investors: list[dict],
               role: str = "investor", subrole: str = "ops"):
    links = _NAV_BY_ROLE.get(role, _NAV_BY_ROLE["investor"])
    items = [
        Li(A(t(key, lang), href=href,
             cls="text-sm transition-colors "
                 + ("text-accent font-medium" if current_path == href else "text-ink-muted hover:text-ink")))
        for key, href in links
    ]
    right = _investor_switcher(investor, investors, lang) if role == "investor" \
        else _role_switcher(role, subrole, lang)
    return Nav(
        Div(
            Ul(*items, cls="flex items-center gap-5 md:gap-7 flex-wrap"),
            Div(_role_switcher(role, subrole, lang) if role == "investor" else Span("", cls="hidden"),
                right, cls="flex items-center gap-3"),
            cls="max-w-7xl mx-auto px-5 md:px-6 flex items-center justify-between gap-4 h-12",
        ),
        cls="sticky top-16 z-40 bg-bg-elevated/90 backdrop-blur border-b border-line",
    )


def app_page(title: str, *content, current_path: str = "/app",
             lang: str = DEFAULT_LANG,
             investor: dict | None = None, investors: list[dict] | None = None,
             role: str = "investor", subrole: str = "ops"):
    """Render product-app content inside the left-nav cockpit shell + copilot."""
    from app_routes.shell import app_shell
    investors = investors if investors is not None else list_investors()
    return app_shell(
        title, *content,
        current_path=current_path, lang=lang,
        investor=investor, investors=investors, role=role, subrole=subrole,
    )
