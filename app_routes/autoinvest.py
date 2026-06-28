"""Auto-invest route: /app/auto-invest — per-investor automated bidding rules.

Modelled on investly.co's Autobidder: the current investor configures a minimum
risk grade, a maximum amount per invoice, preferred sectors and an on/off switch.
Backed by the `factorio.auto_invest` table (one row per investor; there is
no unique constraint, so saving does a delete-then-insert for that investor).
"""

from __future__ import annotations

from fasthtml.common import (
    Div, P, Span, Form, Input, Select, Option, Button, Label, NotStr,
)
from starlette.responses import RedirectResponse

from app import rt
from utils.i18n import t, get_lang
from landing.components import Eyebrow, Heading, Section_
from app_routes._shared import app_page, list_investors, current_investor

try:
    from db import fetch_one, execute
    _HAS_DB = True
except Exception:
    _HAS_DB = False

_GRADES = ["A", "B", "C", "D"]
_INPUT = ("w-full bg-bg-elevated border border-line rounded-lg px-3 py-2 text-sm "
          "text-ink focus:outline-none focus:border-accent")


def _load_rule(investor_id: int) -> dict:
    defaults = {"max_amount_per_invoice": 500, "min_risk_grade": "B",
                "preferred_sectors": "", "is_active": True, "_exists": False}
    if not _HAS_DB:
        return defaults
    try:
        row = fetch_one("""
            SELECT max_amount_per_invoice, min_risk_grade, preferred_sectors, is_active
            FROM factorio.auto_invest
            WHERE investor_id = %(iid)s
            ORDER BY id DESC LIMIT 1
        """, {"iid": investor_id})
        if row:
            row["_exists"] = True
            return row
    except Exception:
        pass
    return defaults


def _save_rule(investor_id: int, *, max_amount, min_grade, sectors, is_active):
    if not _HAS_DB:
        return
    try:
        execute("DELETE FROM factorio.auto_invest WHERE investor_id = %(iid)s",
                {"iid": investor_id})
        execute("""
            INSERT INTO factorio.auto_invest
                (investor_id, max_amount_per_invoice, min_risk_grade,
                 preferred_sectors, is_active)
            VALUES (%(iid)s, %(amt)s, %(grade)s, %(sectors)s, %(active)s)
        """, {"iid": investor_id, "amt": max_amount, "grade": min_grade,
              "sectors": sectors, "active": is_active})
    except Exception:
        pass


def _field(label, control, hint=None):
    return Div(
        Label(label, cls="block text-[11px] font-mono uppercase tracking-widest text-ink-dim mb-1"),
        control,
        P(hint, cls="text-xs text-ink-dim mt-1") if hint else None,
    )


def _status_pill(active: bool, lang: str):
    if active:
        return Span(t("ai_active", lang),
                    cls="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800")
    return Span(t("ai_inactive", lang),
                cls="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700")


def _form(rule: dict, lang: str, saved: bool):
    grade_opts = [
        Option(g, value=g, selected=(rule["min_risk_grade"] == g)) for g in _GRADES
    ]
    active = bool(rule["is_active"])
    return Form(
        Div(
            P(t("ai_status", lang), cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim"),
            _status_pill(active, lang),
            cls="flex items-center justify-between mb-6",
        ),
        Div(
            _field(t("ai_min_grade", lang),
                   Select(*grade_opts, name="min_risk_grade", cls=_INPUT)),
            _field(t("ai_max_amount", lang),
                   Input(type="number", name="max_amount_per_invoice", min="0", step="any",
                         value=str(rule["max_amount_per_invoice"] or ""), cls=_INPUT)),
            cls="grid md:grid-cols-2 gap-4 mb-4",
        ),
        _field(t("ai_sectors", lang),
               Input(type="text", name="preferred_sectors",
                     value=rule["preferred_sectors"] or "", cls=_INPUT),
               hint=t("ai_sectors_hint", lang)),
        Label(
            Input(type="checkbox", name="is_active", value="1", checked=active,
                  cls="mr-2 align-middle accent-accent"),
            Span(t("ai_enable", lang), cls="text-sm text-ink align-middle"),
            cls="flex items-center mt-5 cursor-pointer",
        ),
        Div(
            Button(t("ai_save", lang), type="submit",
                   cls="inline-flex items-center px-5 py-2 rounded-full text-sm font-medium bg-accent text-bg hover:bg-ink transition-all"),
            Span(t("ai_saved", lang), cls="text-sm text-accent ml-3") if saved else None,
            cls="flex items-center mt-6",
        ),
        method="post", action="/app/auto-invest",
        cls="p-7 rounded-2xl bg-bg-elevated border border-line max-w-2xl",
    )


@rt("/app/auto-invest", methods=["GET"])
def auto_invest(req):
    lang = get_lang(req)
    investors = list_investors()
    investor = current_investor(req, investors)
    rule = _load_rule(investor["id"]) if investor else _load_rule(0)
    saved = req.query_params.get("saved") == "1"

    return app_page(
        t("ai_eyebrow", lang),
        Section_(
            Eyebrow(t("ai_eyebrow", lang)),
            Heading(1, t("ai_h1", lang), cls="mt-4 max-w-4xl"),
            P(t("ai_lede", lang), cls="mt-4 text-ink-muted text-lg max-w-3xl leading-relaxed"),
            cls="border-t border-line",
        ),
        Section_(_form(rule, lang, saved), cls="border-t border-line"),
        current_path="/app/auto-invest", lang=lang, investor=investor, investors=investors,
    )


@rt("/app/auto-invest", methods=["POST"])
async def auto_invest_save(req):
    investors = list_investors()
    investor = current_investor(req, investors)
    form = await req.form()
    if investor:
        try:
            amt = float(form.get("max_amount_per_invoice") or 0)
        except (TypeError, ValueError):
            amt = 0
        grade = form.get("min_risk_grade") or "B"
        if grade not in _GRADES:
            grade = "B"
        _save_rule(
            investor["id"],
            max_amount=amt,
            min_grade=grade,
            sectors=(form.get("preferred_sectors") or "").strip(),
            is_active=bool(form.get("is_active")),
        )
    return RedirectResponse("/app/auto-invest?saved=1", status_code=303)
