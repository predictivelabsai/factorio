"""Invoice PDF generation + a vendored pdf.js viewer (ai-indurent pattern).

- `/pdfjs/<file>` serves the vendored pdf.js runtime + the self-contained
  `viewer.html` (canvas render + text-layer search highlighting).
- `/app/invoice-pdf/<invoice_number>` renders a synthetic invoice PDF on the fly
  (WeasyPrint) from the invoice's real row, cached in-process.

The shell exposes a slide-in right pane whose iframe points at
`/pdfjs/viewer.html?file=/app/invoice-pdf/<num>#search=<term>` — clicking an
invoice's "View" opens it there with the debtor name highlighted.
"""

from __future__ import annotations

from pathlib import Path

from starlette.responses import Response

from app import rt

try:
    from db import fetch_one
    _HAS_DB = True
except Exception:  # pragma: no cover
    _HAS_DB = False

PDFJS_DIR = Path(__file__).resolve().parents[1] / "static" / "pdfjs"
_ALLOWED = {"pdf.min.mjs", "pdf.worker.min.mjs"}

_pdf_cache: dict[str, bytes] = {}


@rt("/pdfjs/viewer")
def pdfjs_viewer():
    # served extension-less so the static handler doesn't intercept a .html path
    p = PDFJS_DIR / "viewer.html"
    if not p.exists():
        return Response("not found", status_code=404)
    return Response(p.read_bytes(), media_type="text/html; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=86400"})


@rt("/pdfjs/{fname}")
def pdfjs_asset(fname: str):
    if fname not in _ALLOWED:
        return Response("not found", status_code=404)
    p = PDFJS_DIR / fname
    if not p.exists():
        return Response("not found", status_code=404)
    return Response(p.read_bytes(), media_type="text/javascript",
                    headers={"Cache-Control": "public, max-age=86400"})


def _money(amount, currency="USD") -> str:
    from utils.money import fmt_money
    return fmt_money(amount)


def _invoice_html(r: dict) -> str:
    from utils.money import fmt_money
    face = float(r["amount"] or 0)
    # a couple of synthetic line items that sum to the face value
    li = [("Goods / services supplied per contract", round(face * 0.82, 2)),
          ("Delivery & handling", round(face * 0.18, 2))]
    rows = "".join(
        f"<tr><td>{desc}</td><td class='r'>1</td><td class='r'>{fmt_money(amt)}</td>"
        f"<td class='r'>{fmt_money(amt)}</td></tr>" for desc, amt in li)
    seller = r.get("seller_company") or "Supplier Ltd"
    issue = r.get("issue_date"); due = r.get("due_date")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 1.8cm; }}
body {{ font-family: Inter, Arial, sans-serif; color:#14231B; font-size:11pt; }}
.top {{ display:flex; justify-content:space-between; align-items:flex-start; border-bottom:3px solid #1F5D43; padding-bottom:12px; }}
.brand {{ font-size:20pt; font-weight:700; color:#1F5D43; }}
.muted {{ color:#6b7280; font-size:9.5pt; }}
h1 {{ font-size:15pt; margin:18px 0 4px; }}
.grid {{ display:flex; gap:40px; margin:16px 0; }}
.grid div p {{ margin:2px 0; }}
.lbl {{ font-size:8pt; letter-spacing:1px; text-transform:uppercase; color:#9ca3af; }}
table {{ width:100%; border-collapse:collapse; margin-top:14px; font-size:10.5pt; }}
th {{ background:#1F5D43; color:#fff; text-align:left; padding:6px 8px; }}
td {{ padding:6px 8px; border-bottom:1px solid #E3DFD2; }}
td.r, th.r {{ text-align:right; }}
.total {{ text-align:right; margin-top:10px; font-size:13pt; font-weight:700; color:#1F5D43; }}
.terms {{ margin-top:26px; font-size:9pt; color:#6b7280; }}
</style></head><body>
<div class="top">
  <div><div class="brand">◆ {seller}</div><div class="muted">Supplier · issued via Factorio</div></div>
  <div style="text-align:right"><div class="muted">INVOICE</div><div style="font-size:13pt;font-weight:700">{r['invoice_number']}</div></div>
</div>
<h1>Invoice {r['invoice_number']}</h1>
<div class="grid">
  <div><p class="lbl">Bill to (debtor)</p><p style="font-weight:600">{r['debtor_name']}</p>
       <p class="muted">Sector: {(r.get('sector') or '—').title()}</p></div>
  <div><p class="lbl">Issue date</p><p>{issue}</p><p class="lbl" style="margin-top:8px">Due date</p><p>{due}</p></div>
  <div><p class="lbl">Terms</p><p>{r.get('payment_terms_days') or 60} days</p>
       <p class="lbl" style="margin-top:8px">Risk grade</p><p>{r.get('risk_grade') or 'B'}</p></div>
</div>
<table><thead><tr><th>Description</th><th class="r">Qty</th><th class="r">Unit</th><th class="r">Amount</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="total">Total due: {fmt_money(face)}</div>
<p class="terms">Payment due within {r.get('payment_terms_days') or 60} days of the issue date to the account on file.
This invoice may be assigned to a financing party; on assignment, payment must be made to the assignee's collection account.
Buyer-confirmed on the SoliqOnline e-invoice network. Generated for demonstration — synthetic data.</p>
</body></html>"""


@rt("/app/invoice-pdf/{invoice_number}")
def invoice_pdf(req, invoice_number: str):
    if invoice_number in _pdf_cache:
        data = _pdf_cache[invoice_number]
    else:
        if not _HAS_DB:
            return Response("db unavailable", status_code=503)
        r = fetch_one("""
            SELECT i.invoice_number, i.debtor_name, i.amount, i.currency, i.issue_date,
                   i.due_date, i.payment_terms_days, i.sector, i.risk_grade,
                   c.name AS seller_company
            FROM factorio.invoices i
            LEFT JOIN factorio.companies c ON c.id = i.company_id
            WHERE i.invoice_number = %(n)s
        """, {"n": invoice_number})
        if not r:
            return Response("invoice not found", status_code=404)
        try:
            from weasyprint import HTML
            data = HTML(string=_invoice_html(r)).write_pdf()
        except Exception as e:  # noqa: BLE001
            return Response(f"pdf error: {e}", status_code=500)
        _pdf_cache[invoice_number] = data
    return Response(data, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{invoice_number}.pdf"'})
