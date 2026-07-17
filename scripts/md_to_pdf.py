"""Render a Markdown doc (with mermaid + images) to a clean A4 PDF.

Mermaid ```mermaid blocks are rendered to PNG via kroki.io; image paths resolve
relative to docs/ so `img/...` screenshots embed. Used to produce a viewable PDF
of the hospitality proposal (and any other md doc).

    python -m scripts.md_to_pdf docs/hospitality_proposal_factorio.md
"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

import markdown as md_lib
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TMP = DOCS / "img" / "_mdpdf"

CSS = """
@page { size: A4; margin: 1.6cm 1.8cm; @bottom-right { content: counter(page); font-size: 8pt; color: #7A867E; } }
body { font-family: "Inter","Helvetica Neue",Arial,"DejaVu Sans",sans-serif; color:#14231B; line-height:1.55; font-size:10.5pt; }
h1 { color:#1F5D43; font-size:22pt; letter-spacing:-.4px; margin:0 0 .1cm; }
h2 { color:#fff; background:#1F5D43; font-size:13pt; padding:.2cm .4cm; border-radius:6px; border-left:6px solid #C8A24B; margin:.7cm 0 .3cm; }
h3 { color:#1F5D43; font-size:11.5pt; margin:.5cm 0 .15cm; }
p,li { margin:.12cm 0; }
strong { color:#1F5D43; }
a { color:#1F5D43; text-decoration:none; }
hr { border:0; border-top:1px solid #E3DFD2; margin:.6cm 0; }
code { background:#ECEAE0; color:#1F5D43; padding:.03cm .12cm; border-radius:3px; font-family:"JetBrains Mono",monospace; font-size:.86em; }
blockquote { margin:.3cm 0; padding:.2cm .5cm; background:#EEEDE5; border-left:4px solid #C8A24B; color:#415046; font-style:italic; }
img { display:block; max-width:100%; margin:.3cm auto; border:1px solid #E3DFD2; border-radius:8px; }
table { border-collapse:collapse; width:100%; font-size:9pt; margin:.3cm 0; page-break-inside:avoid; }
th { background:#1F5D43; color:#fff; text-align:left; padding:4px 8px; border:1px solid #16432F; }
td { padding:4px 8px; border:1px solid #E3DFD2; vertical-align:top; }
tr:nth-child(even) td { background:#EEEDE5; }
h1,h2,h3,table,img,blockquote { page-break-inside:avoid; }

/* Utilities for structured docs (page breaks + persona separators) */
.pagebreak { page-break-before: always; }
.persona {
  page-break-before: always;
  background:#1F5D43; color:#fff; border-radius:12px;
  padding:1.5cm 1.2cm; margin:.2cm 0 .7cm; border-left:12px solid #C8A24B;
}
.persona .kicker {
  font-family:"JetBrains Mono",monospace; font-size:9pt; letter-spacing:2.5px;
  text-transform:uppercase; color:#C8A24B; margin:0 0 .3cm;
}
.persona h1 { color:#fff; font-size:30pt; margin:0 0 .25cm; letter-spacing:-.5px; }
.persona .sub { color:#DCEBE3; font-size:12pt; margin:0; font-style:normal; }
.persona strong { color:#fff; }
.titlepage { text-align:center; padding:3cm 0 1cm; }
.titlepage h1 { font-size:32pt; margin:.2cm 0 .3cm; }
.titlepage .kicker {
  font-family:"JetBrains Mono",monospace; font-size:9pt; letter-spacing:3px;
  text-transform:uppercase; color:#C8A24B; margin:0 0 .3cm;
}
"""


def _kroki_png(src: str, out: Path) -> bool:
    try:
        req = urllib.request.Request(
            "https://kroki.io/mermaid/png", data=("%%{init: {'theme':'neutral'}}%%\n" + src).encode(),
            headers={"Content-Type": "text/plain", "User-Agent": "Mozilla/5.0 (factorio md2pdf)"},
            method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            out.write_bytes(r.read())
        return True
    except Exception as e:  # noqa: BLE001
        print(f"  mermaid render failed: {e}")
        return False


def _render_mermaid(md_text: str) -> str:
    TMP.mkdir(parents=True, exist_ok=True)
    blocks = list(re.finditer(r"```mermaid\n(.*?)```", md_text, re.S))
    for i, m in enumerate(blocks):
        out = TMP / f"d{i}.png"
        if _kroki_png(m.group(1), out):
            md_text = md_text.replace(m.group(0), f"![diagram](img/_mdpdf/d{i}.png)")
    return md_text


def convert(md_path: Path) -> Path:
    text = md_path.read_text(encoding="utf-8")
    text = _render_mermaid(text)
    body = md_lib.markdown(text, extensions=["tables", "attr_list", "sane_lists", "fenced_code"])
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body>{body}</body></html>')
    out = md_path.with_suffix(".pdf")
    HTML(string=html, base_url=str(DOCS)).write_pdf(str(out))
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python -m scripts.md_to_pdf <path.md> [<path2.md> ...]")
        return 1
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.is_absolute():
            p = ROOT / p
        out = convert(p)
        print(f"  {out.relative_to(ROOT)} ({out.stat().st_size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
