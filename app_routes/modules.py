"""Back-office workspace modules — CRM (sales pipeline), Drive, Docs, Mail.

Demo-grade ports of the Fast* apps (FastCRM / FastDrive / FastDocs / FastMail),
rendered inside Factorio's left-nav app shell. Data is in-memory demo data so the
modules work without a schema migration; the shapes mirror the source apps and
can be moved to Postgres later (see docs/enterprise_extension_plan.md).
"""

from __future__ import annotations

from fasthtml.common import Div, P, Span, A, H3, Table, Thead, Tbody, Tr, Th, Td, NotStr

from app import rt
from utils.i18n import t, get_lang
from landing.components import Eyebrow, Heading, Section_
from app_routes._shared import app_page, fmt_uzs, current_role, current_subrole

# ── CRM demo data (mirrors FastCRM deals) ─────────────────────────────────
DEAL_STAGES = ["Qualification", "Demo", "Proposal", "Negotiation", "Ready to close"]
DEALS = [
    ("Globex Corporation", "Reverse-factoring programme", "Qualification", 120000, "Aziza K."),
    ("Bright Textiles", "Invoice discounting facility", "Qualification", 60000, "Bek T."),
    ("Meridian Logistics", "Factoring — logistics", "Demo", 45000, "Aziza K."),
    ("Grand Plaza Hotels", "Hospitality SCF", "Demo", 210000, "Dmitry P."),
    ("Greenfield Agro", "Seasonal working capital", "Proposal", 90000, "Bek T."),
    ("Summit Retail", "Supplier finance", "Proposal", 75000, "Aziza K."),
    ("Helios Energy", "Contractor receivables", "Negotiation", 320000, "Dmitry P."),
    ("Vitalis Pharma", "Healthcare receivables", "Negotiation", 130000, "Bek T."),
    ("Vertex Construction", "Milestone financing", "Ready to close", 180000, "Aziza K."),
]


def pipeline_summary() -> str:
    by = {}
    for _, _, stage, val, _ in DEALS:
        s = by.setdefault(stage, [0, 0]); s[0] += 1; s[1] += val
    total = sum(v for _, v in by.values())
    parts = [f"{st}: {by[st][0]} deals / ${by[st][1]:,.0f}" for st in DEAL_STAGES if st in by]
    return f"Open pipeline ${total:,.0f} across {len(DEALS)} deals — " + "; ".join(parts)


def _usd(v):
    return f"${v:,.0f}"


@rt("/app/crm")
def crm(req):
    lang = get_lang(req)
    cols = []
    for stage in DEAL_STAGES:
        deals = [d for d in DEALS if d[2] == stage]
        total = sum(d[3] for d in deals)
        cards = [
            Div(P(name, cls="text-sm font-medium text-ink"),
                P(desc, cls="text-xs text-ink-muted mt-0.5"),
                Div(Span(_usd(val), cls="text-sm font-medium text-accent"),
                    Span(owner, cls="text-[11px] text-ink-dim"),
                    cls="flex items-center justify-between mt-2"),
                cls="p-3 rounded-xl bg-bg-elevated border border-line mb-2")
            for name, desc, _st, val, owner in deals
        ]
        cols.append(Div(
            Div(Span(stage, cls="text-xs font-mono uppercase tracking-wider text-ink-dim"),
                Span(f"{len(deals)} · {_usd(total)}", cls="text-[11px] text-ink-muted"),
                cls="flex items-center justify-between mb-3 px-1"),
            *cards,
            cls="min-w-[220px] flex-1 p-2 rounded-2xl bg-bg-raised/40"))
    return app_page(
        "Sales pipeline",
        Section_(Eyebrow("Sales · CRM"),
                 Heading(1, "Sales pipeline", cls="mt-4"),
                 P(NotStr(pipeline_summary()), cls="mt-3 text-ink-muted max-w-3xl"),
                 cls="border-t border-line"),
        Section_(Div(*cols, cls="flex gap-3 overflow-x-auto pb-4"), cls="border-t border-line"),
        current_path="/app/crm", lang=lang, role=current_role(req), subrole=current_subrole(req),
    )


# ── Drive demo ────────────────────────────────────────────────────────────
FILES = [
    ("📁", "Client agreements", "folder", "—", "2d ago"),
    ("📁", "E-invoice exports", "folder", "—", "1d ago"),
    ("📄", "Globex_master_agreement.pdf", "pdf", "180 KB", "2d ago"),
    ("📄", "INV-1042_assignment.pdf", "pdf", "42 KB", "5h ago"),
    ("📊", "Portfolio_aging_2026Q3.xlsx", "sheet", "88 KB", "3h ago"),
    ("🖼️", "Warehouse_collateral.jpg", "image", "1.2 MB", "1d ago"),
    ("📄", "KYC_Greenfield_Agro.pdf", "pdf", "260 KB", "6h ago"),
]


@rt("/app/drive")
def drive(req):
    lang = get_lang(req)
    tiles = [
        Div(Span(icon, cls="text-3xl"),
            P(name, cls="text-sm text-ink mt-2 truncate"),
            P(f"{size} · {when}", cls="text-[11px] text-ink-dim mt-0.5"),
            cls="p-5 rounded-2xl bg-bg-elevated border border-line hover:border-accent transition-colors")
        for icon, name, kind, size, when in FILES
    ]
    return app_page(
        "Drive",
        Section_(Eyebrow("Workspace · Drive"),
                 Heading(1, "Document drive", cls="mt-4"),
                 P("Invoice, KYC and collateral documents — folders, sharing and public links.",
                   cls="mt-3 text-ink-muted max-w-3xl"), cls="border-t border-line"),
        Section_(Div(*tiles, cls="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"),
                 cls="border-t border-line"),
        current_path="/app/drive", lang=lang, role=current_role(req), subrole=current_subrole(req),
    )


# ── Docs demo ─────────────────────────────────────────────────────────────
DOCS = [
    ("Credit policy — v3", "Underwriting", "Advance rates, concentration limits and grade thresholds…", 1240, True),
    ("Onboarding checklist", "Operations", "KYC/AML steps for new clients and debtors…", 480, True),
    ("Collections playbook", "Collections", "Dunning cadence, dispute handling and write-off rules…", 760, False),
    ("SPV term sheet (DIFC)", "Capital", "Structure, waterfall and investor reporting…", 2100, False),
]


@rt("/app/docs")
def docs(req):
    lang = get_lang(req)
    cards = [
        Div(Div(Span(folder, cls="text-[11px] font-mono uppercase tracking-wider text-accent"),
                Span("Published" if pub else "Draft",
                     cls="text-[11px] " + ("text-green-700" if pub else "text-ink-dim")),
                cls="flex items-center justify-between"),
            H3(title, cls="text-ink text-lg font-medium mt-1"),
            P(excerpt, cls="text-sm text-ink-muted mt-1"),
            P(f"{words} words", cls="text-[11px] text-ink-dim mt-2"),
            cls="p-6 rounded-2xl bg-bg-elevated border border-line")
        for title, folder, excerpt, words, pub in DOCS
    ]
    return app_page(
        "Docs",
        Section_(Eyebrow("Workspace · Docs"),
                 Heading(1, "Documents", cls="mt-4"),
                 P("Policies, playbooks and term sheets — block editor, templates and version history.",
                   cls="mt-3 text-ink-muted max-w-3xl"), cls="border-t border-line"),
        Section_(Div(*cards, cls="grid md:grid-cols-2 gap-4"), cls="border-t border-line"),
        current_path="/app/docs", lang=lang, role=current_role(req), subrole=current_subrole(req),
    )


# ── Mail demo ─────────────────────────────────────────────────────────────
MAIL = [
    ("David Chen", "Re: Factorio proposal", "Thanks — let's schedule a call next week…", "10:24", False),
    ("Globex Corporation AP", "Invoice INV-20260012 confirmed", "We confirm the obligation on the e-invoice network…", "09:12", False),
    ("CRIF Bureau", "Debtor report ready", "The credit report for Meridian Logistics is available…", "Yesterday", True),
    ("Oleg Kim", "Pipeline review", "Attaching the updated deal list for this week…", "Yesterday", True),
    ("E-Invoice Network", "Daily e-invoice digest", "42 new buyer-confirmed invoices for your clients…", "Mon", True),
]


@rt("/app/mail")
def mail(req):
    lang = get_lang(req)
    rows = [
        Div(Span("●", cls=("text-accent" if not read else "text-transparent") + " text-xs mr-3"),
            Div(P(sender, cls="text-sm font-medium text-ink"),
                P(Span(subject, cls="text-ink"), Span(" — " + snippet, cls="text-ink-muted"),
                  cls="text-sm truncate"),
                cls="flex-1 min-w-0"),
            Span(when, cls="text-[11px] text-ink-dim ml-3 whitespace-nowrap"),
            cls="flex items-center py-3 px-4 border-b border-line hover:bg-bg-raised/40")
        for sender, subject, snippet, when, read in MAIL
    ]
    return app_page(
        "Mail",
        Section_(Eyebrow("Workspace · Mail"),
                 Heading(1, "Inbox", cls="mt-4"),
                 P("Client, debtor and bureau correspondence — threads, labels and AI draft replies.",
                   cls="mt-3 text-ink-muted max-w-3xl"), cls="border-t border-line"),
        Section_(Div(*rows, cls="rounded-2xl bg-bg-elevated border border-line overflow-hidden"),
                 cls="border-t border-line"),
        current_path="/app/mail", lang=lang, role=current_role(req), subrole=current_subrole(req),
    )
