"""Real authentication — production (step 8).

Session-based login with PBKDF2-hashed passwords over an ``app_users`` table.
Layered so the demo is not broken: if a user is **logged in**, the session's
role/subrole win; otherwise the app falls back to the cookie role-switcher used
for demos. MFA/SSO are stubbed (documented as the next hardening step).

Passwords use stdlib ``hashlib.pbkdf2_hmac`` — no extra dependency.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, NotStr,
    Div, Span, A, Form, Input, Button, P, H1, Label,
)
from starlette.responses import RedirectResponse

from app import rt
from landing.components import TAILWIND_CONFIG, SITE_NAME

try:
    from db import fetch_all, fetch_one, execute
    _HAS_DB = True
except Exception:  # pragma: no cover
    _HAS_DB = False

# Demo users seeded on first use (password "demo1234" for all).
DEMO_USERS = [
    ("admin@factorio.co.uk", "Super Admin", "admin", "super"),
    ("finance@factorio.co.uk", "Finance Officer", "admin", "finance"),
    ("credit@factorio.co.uk", "Credit Analyst", "admin", "credit"),
    ("compliance@factorio.co.uk", "Compliance Officer", "admin", "compliance"),
    ("collections@factorio.co.uk", "Collections Agent", "admin", "collections"),
    ("investor@factorio.co.uk", "Investor", "investor", "ops"),
    ("seller@factorio.co.uk", "Supplier", "seller", "ops"),
    ("payer@factorio.co.uk", "Payer", "payer", "ops"),
]
DEMO_PASSWORD = "demo1234"


def _hash(pw: str, salt: bytes | None = None):
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100_000)
    return base64.b64encode(salt).decode(), base64.b64encode(dk).decode()


def _verify(pw: str, salt_b64: str, hash_b64: str) -> bool:
    try:
        salt = base64.b64decode(salt_b64)
        _, calc = _hash(pw, salt)
        return hmac.compare_digest(calc, hash_b64)
    except Exception:
        return False


def _ensure():
    if not _HAS_DB:
        return
    execute("""CREATE TABLE IF NOT EXISTS factorio.app_users (
        email TEXT PRIMARY KEY, name TEXT NOT NULL DEFAULT '',
        salt TEXT NOT NULL, pw_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'investor', subrole TEXT NOT NULL DEFAULT 'ops',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")


def seed_users() -> int:
    _ensure()
    if not _HAS_DB:
        return 0
    n = 0
    for email, name, role, subrole in DEMO_USERS:
        if fetch_one("SELECT 1 FROM factorio.app_users WHERE email=%(e)s", {"e": email}):
            continue
        salt, h = _hash(DEMO_PASSWORD)
        execute("INSERT INTO factorio.app_users (email,name,salt,pw_hash,role,subrole) "
                "VALUES (%(e)s,%(n)s,%(s)s,%(h)s,%(r)s,%(sr)s)",
                {"e": email, "n": name, "s": salt, "h": h, "r": role, "sr": subrole})
        n += 1
    return n


def current_user(req):
    """Return the logged-in user dict from the session, or None."""
    s = getattr(req, "session", None)
    if s and s.get("uid"):
        return {"email": s.get("uid"), "name": s.get("name", ""),
                "role": s.get("role"), "subrole": s.get("subrole", "ops")}
    return None


# ── Login / logout ─────────────────────────────────────────────────────────

def _login_page(error: str = "", email: str = ""):
    field = "w-full mt-1 px-4 py-2.5 rounded-xl border border-line-bright bg-bg-elevated text-ink focus:outline-none focus:border-accent"
    return Html(
        Head(Meta(charset="utf-8"), Meta(name="viewport", content="width=device-width, initial-scale=1"),
             Title(f"Sign in · {SITE_NAME}"),
             Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"),
             Script(src="https://cdn.tailwindcss.com"), Script(NotStr(TAILWIND_CONFIG)),
             Link(rel="stylesheet", href="/static/site.css")),
        Body(Div(
            Div(
                A(Span(NotStr("&#9670;"), cls="text-accent mr-2"), Span(SITE_NAME, cls="font-medium"),
                  href="/", cls="flex items-center justify-center text-xl mb-6 text-ink no-underline"),
                H1("Sign in", cls="text-2xl font-medium text-ink text-center mb-1"),
                P("Back-office & investor portal", cls="text-ink-muted text-sm text-center mb-6"),
                (P(error, cls="text-red-700 text-sm text-center mb-4") if error else None),
                Form(
                    Label("Email", cls="text-sm text-ink-muted"),
                    Input(name="email", type="email", value=email, required=True, cls=field),
                    Label("Password", cls="text-sm text-ink-muted mt-4 block"),
                    Input(name="password", type="password", required=True, cls=field),
                    Button("Sign in", type="submit",
                           cls="w-full mt-6 px-5 py-2.5 rounded-full bg-accent text-bg font-medium hover:bg-ink transition-colors"),
                    method="post", action="/login"),
                P(NotStr("Demo: <b>admin@factorio.co.uk</b> / <b>demo1234</b> "
                         "(also finance@, credit@, compliance@, investor@, seller@, payer@)"),
                  cls="text-ink-dim text-xs text-center mt-6"),
                cls="w-full max-w-sm p-8 rounded-2xl bg-bg-elevated border border-line shadow-sm"),
            cls="min-h-screen flex items-center justify-center px-4 bg-bg"),
            cls="bg-bg text-ink font-sans antialiased"))


@rt("/login", methods=["GET"])
def login_get(req):
    if current_user(req):
        return RedirectResponse("/app", status_code=303)
    return _login_page()


@rt("/login", methods=["POST"])
def login_post(req, email: str = "", password: str = ""):
    seed_users()
    email = (email or "").strip().lower()
    u = fetch_one("SELECT * FROM factorio.app_users WHERE email=%(e)s", {"e": email}) if _HAS_DB else None
    if not u or not _verify(password, u["salt"], u["pw_hash"]):
        return _login_page("Invalid email or password.", email)
    s = req.session
    s["uid"] = u["email"]; s["name"] = u["name"]; s["role"] = u["role"]; s["subrole"] = u["subrole"]
    dest = {"admin": "/app/admin", "seller": "/app/seller", "payer": "/app/payer"}.get(u["role"], "/app")
    return RedirectResponse(dest, status_code=303)


@rt("/logout")
def logout(req):
    try:
        req.session.clear()
    except Exception:
        pass
    return RedirectResponse("/", status_code=303)
