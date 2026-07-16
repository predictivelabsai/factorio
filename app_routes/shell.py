"""Left-nav app shell + docked streaming copilot (drvet/monika pattern).

`app_shell()` renders the /app workspace as a CSS-grid cockpit: top bar · left
navigation · center content · right copilot rail. Every /app page flows through
it (via `app_page`, which lazy-imports this). The copilot streams tokens from a
LangGraph/Grok agent (utils.copilot) over hand-rolled SSE.
"""

from __future__ import annotations

import json

from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, Style, NotStr,
    Div, Span, A, Button, Form, Input, P,
)
from starlette.responses import StreamingResponse

from app import rt
from utils.i18n import t, LANG_META, SUPPORTED_LANGS, DEFAULT_LANG
from landing.components import TAILWIND_CONFIG, SITE_NAME
from utils.copilot import copilot_available

# ── Navigation model: (SECTION, [(key, i18n_key_or_label, icon, href)]) ────
NAV = [
    ("Factoring", [
        ("dashboard", "nav_dashboard", "\U0001F4CA", "/app"),
        ("marketplace", "mkt_eyebrow", "\U0001F9FE", "/app/marketplace"),
        ("portfolio", "port_eyebrow", "\U0001F4C1", "/app/portfolio"),
        ("statement", "nav_statement", "\U0001F9EE", "/app/statement"),
        ("autoinvest", "nav_autoinvest", "⚙️", "/app/auto-invest"),
        ("triage", "nav_triage", "\U0001F4AC", "/app/triage"),
        ("reports", "nav_assistant", "\U0001F4C8", "/app/assistant"),
        ("admin", "nav_admin", "\U0001F6E0️", "/app/admin"),
        ("processing", "Processing", "\U0001F9FE", "/app/admin/processing"),
        ("scoring", "Credit scoring", "\U0001F3AF", "/app/admin/scoring"),
        ("collections", "Collections", "\U0001F4E9", "/app/admin/collections"),
        ("accounting", "Accounting", "\U0001F4B7", "/app/admin/accounting"),
    ]),
    ("Sales", [
        ("crm", "Pipeline", "\U0001F4C7", "/app/crm"),
    ]),
    ("Workspace", [
        ("drive", "Drive", "\U0001F5C2️", "/app/drive"),
        ("docs", "Docs", "\U0001F4DD", "/app/docs"),
        ("mail", "Mail", "✉️", "/app/mail"),
    ]),
]

_ACTIVE_BY_PATH = {href: key for _, items in NAV for key, _, _, href in items}

SHELL_CSS = """
.ws { display:grid; grid-template-columns:236px 1fr var(--rail,360px);
  grid-template-rows:56px 1fr; grid-template-areas:"top top top" "left center right";
  height:100vh; overflow:hidden; transition:grid-template-columns .18s ease; }
.ws.rail-collapsed { --rail:0px; }
.ws.rail-collapsed .ws-right { display:none; }
.ws-top { grid-area:top; display:flex; align-items:center; justify-content:space-between;
  padding:0 16px; background:#FFFFFF; border-bottom:1px solid #E3DFD2; }
.ws-left { grid-area:left; background:#FFFFFF; border-right:1px solid #E3DFD2; overflow-y:auto; padding:10px 0; }
.ws-center { grid-area:center; overflow-y:auto; background:#F7F6F1; }
.ws-right { grid-area:right; background:#FFFFFF; border-left:1px solid #E3DFD2; display:flex; flex-direction:column; overflow:hidden; }
.nav-sec { margin:2px 0 8px; }
.nav-head { padding:6px 16px; font-size:10.5px; text-transform:uppercase; letter-spacing:.9px; color:#7A867E; font-weight:700; }
.nav-item { display:flex; align-items:center; gap:9px; padding:8px 16px; font-size:13.5px; color:#415046;
  text-decoration:none; border-left:3px solid transparent; }
.nav-item:hover { background:#EFEDE4; color:#14231B; }
.nav-item.active { background:#CFE5DA; color:#0F3226; border-left-color:#1F5D43; font-weight:600; }
.nav-ic { width:18px; text-align:center; }
.cp-msgs { flex:1; overflow-y:auto; padding:14px; display:flex; flex-direction:column; gap:12px; }
.cp-msg { font-size:13.5px; line-height:1.5; }
.cp-msg.user { align-self:flex-end; background:#1F5D43; color:#fff; padding:8px 12px; border-radius:14px; max-width:88%; }
.cp-msg.assistant { align-self:flex-start; color:#14231B; }
.cp-msg.assistant p { margin:.2em 0; } .cp-msg.assistant ul { margin:.2em 0 .2em 1em; }
.cp-who { font-size:10px; font-family:monospace; text-transform:uppercase; letter-spacing:1px; color:#7A867E; margin-bottom:3px; }
.cp-tool { font-size:11px; color:#7A867E; font-style:italic; }
.cp-form { border-top:1px solid #E3DFD2; padding:10px; display:flex; gap:8px; }
.cp-input { flex:1; border:1px solid #CFC8B4; border-radius:12px; padding:9px 12px; font-size:13.5px; resize:none; outline:none; }
.cp-input:focus { border-color:#1F5D43; }
.cp-send { background:#1F5D43; color:#fff; border:0; border-radius:999px; padding:0 16px; font-size:13px; cursor:pointer; }
.cp-suggest { padding:0 14px 6px; display:flex; flex-wrap:wrap; gap:6px; }
.cp-chip { font-size:11.5px; color:#1F5D43; background:#EFEDE4; border:1px solid #E3DFD2; border-radius:999px; padding:4px 10px; cursor:pointer; }
"""

SHELL_JS = """
function wsToggleRail(){ document.getElementById('ws').classList.toggle('rail-collapsed'); }
function cpAdd(role, html){ var m=document.getElementById('cp-msgs');
  var d=document.createElement('div'); d.className='cp-msg '+role;
  if(role==='assistant'){ var w=document.createElement('div'); w.className='cp-who'; w.textContent='Copilot'; m.appendChild(w); }
  d.innerHTML=html; m.appendChild(d); m.scrollTop=m.scrollHeight; return d; }
function cpMd(t){ try{ return window.marked ? marked.parse(t) : t.replace(/\\n/g,'<br>'); }catch(e){ return t; } }
function cpEsc(s){ var d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
var _cpBusy=false;
async function cpSend(ev){ if(ev&&ev.preventDefault) ev.preventDefault();
  if(_cpBusy) return false;
  var inp=document.getElementById('cp-input'); var msg=inp.value.trim(); if(!msg) return false;
  _cpBusy=true; inp.value=''; cpAdd('user', cpEsc(msg));
  var think=cpAdd('assistant','<span class=cp-tool>thinking…</span>'); var acc=''; var bubble=null;
  try{
    var resp=await fetch('/app/copilot/stream',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({message:msg})});
    var reader=resp.body.getReader(), dec=new TextDecoder(), buf='';
    while(true){ var r=await reader.read(); if(r.done) break; buf+=dec.decode(r.value,{stream:true});
      var i; while((i=buf.indexOf('\\n\\n'))!==-1){ var raw=buf.slice(0,i); buf=buf.slice(i+2);
        var type=null,data=''; raw.split('\\n').forEach(function(l){ if(l.indexOf('event: ')===0) type=l.slice(7).trim(); else if(l.indexOf('data: ')===0) data+=l.slice(6); });
        var p=data?JSON.parse(data):{};
        if(type==='token'){ if(acc===''){ think.remove(); bubble=cpAdd('assistant',''); } acc+=p.text||''; bubble.innerHTML=cpMd(acc); }
        else if(type==='tool_start'){ think.innerHTML='<span class=cp-tool>checking '+(p.name||'data')+'…</span>'; }
        else if(type==='error'){ think.innerHTML='<span class=cp-tool>error: '+cpEsc(p.message||'')+'</span>'; }
      }
    }
    if(acc==='' && think) think.innerHTML='<span class=cp-tool>(no response)</span>';
  }catch(e){ if(think) think.innerHTML='<span class=cp-tool>connection error</span>'; }
  var m=document.getElementById('cp-msgs'); m.scrollTop=m.scrollHeight; _cpBusy=false; return false;
}
function cpAsk(q){ document.getElementById('cp-input').value=q; cpSend(); }
"""

_SUGGESTIONS = ["How much have we funded?", "Which sector has the most exposure?",
                "Top debtors by concentration", "Summarise the sales pipeline"]


def _copilot_pane():
    if not copilot_available():
        return Div(Div("Copilot", cls="cp-who", style="padding:14px"),
                   P("Set XAI_API_KEY to enable the copilot.", cls="cp-tool", style="padding:0 14px"),
                   cls="ws-right")
    chips = [Span(s, cls="cp-chip", onclick=f"cpAsk('{s}')") for s in _SUGGESTIONS]
    return Div(
        Div(Span("✨ Copilot", style="font-weight:600;color:#1F5D43"),
            Button("‹", onclick="wsToggleRail()", type="button",
                   style="background:none;border:0;cursor:pointer;color:#7A867E;font-size:18px"),
            style="display:flex;align-items:center;justify-content:space-between;padding:12px 14px;border-bottom:1px solid #E3DFD2"),
        Div(Div("Copilot", cls="cp-who"),
            Div(NotStr("Ask me about funding, exposure, the pipeline or portfolio."), cls="cp-msg assistant"),
            id="cp-msgs", cls="cp-msgs"),
        Div(*chips, cls="cp-suggest"),
        Form(Input(id="cp-input", cls="cp-input", placeholder="Ask about the data…",
                   autocomplete="off",
                   onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();cpSend();}"),
             Button("Send", cls="cp-send", type="submit"),
             cls="cp-form", onsubmit="return cpSend(event)"),
        cls="ws-right", id="ws-right")


def _left_nav(active: str, lang: str):
    secs = []
    for section, items in NAV:
        links = [
            A(Span(NotStr(icon), cls="nav-ic"),
              Span(t(label, lang) if "_" in label and label.islower() else label),
              href=href, cls="nav-item active" if active == key else "nav-item")
            for key, label, icon, href in items
        ]
        secs.append(Div(Div(section, cls="nav-head"), *links, cls="nav-sec"))
    return Div(*secs, cls="ws-left")


def _lang_pill(lang: str):
    opts = [A(Span(LANG_META[c]["flag"], cls="mr-2"), Span(LANG_META[c]["name"], cls="text-xs"),
              href=f"/set-lang?lang={c}",
              onclick=f"document.cookie='lang={c};path=/;max-age=31536000;samesite=lax';location.reload();return false;",
              cls="flex items-center gap-1 px-3 py-1.5 text-sm text-ink-muted hover:bg-bg-raised no-underline")
            for c in SUPPORTED_LANGS]
    return Div(
        Button(LANG_META.get(lang, LANG_META["en"])["flag"], type="button",
               onclick="this.nextElementSibling.classList.toggle('hidden')",
               cls="text-base px-1.5 py-1 rounded hover:bg-bg-raised cursor-pointer bg-transparent border-0"),
        Div(*opts, cls="hidden absolute right-0 top-full mt-1 bg-bg-elevated border border-line rounded-lg shadow-lg z-50 py-1 min-w-[150px] flex flex-col"),
        cls="relative")


def app_shell(title: str, *content, current_path: str = "/app", lang: str = DEFAULT_LANG,
              investor=None, investors=None, role: str = "investor", subrole: str = "ops"):
    from app_routes._shared import _role_switcher, _investor_switcher, list_investors
    investors = investors if investors is not None else list_investors()
    active = _ACTIVE_BY_PATH.get(current_path, "")
    right = _role_switcher(role, subrole, lang) if role != "investor" else _investor_switcher(investor, investors, lang)
    head = [
        Meta(charset="utf-8"), Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Title(f"{title} · {SITE_NAME}"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"),
        Script(src="https://cdn.tailwindcss.com"), Script(NotStr(TAILWIND_CONFIG)),
        Script(src="https://unpkg.com/htmx.org@2.0.3"),
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Link(rel="stylesheet", href="/static/site.css"),
        Style(SHELL_CSS),
    ]
    topbar = Div(
        A(Span(NotStr("&#9670;"), cls="text-accent mr-2"), Span(SITE_NAME, cls="font-medium tracking-tight text-ink"),
          href="/", cls="flex items-center text-base no-underline"),
        Div(right, _lang_pill(lang),
            Button(NotStr("&#9776;"), onclick="wsToggleRail()", type="button",
                   cls="text-ink-dim text-lg bg-transparent border-0 cursor-pointer", title="Toggle copilot"),
            cls="flex items-center gap-3"),
        cls="ws-top")
    return Html(
        Head(*head),
        Body(Div(topbar, _left_nav(active, lang),
                 Div(*content, cls="ws-center"), _copilot_pane(),
                 cls="ws", id="ws"),
             Script(NotStr(SHELL_JS)),
             cls="bg-bg text-ink font-sans antialiased"),
        lang={"en": "en", "uz": "uz", "ru": "ru", "es": "es", "fr": "fr"}.get(lang, "en"),
    )


# ── Copilot streaming endpoint (hand-rolled SSE) ──────────────────────────

def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@rt("/app/copilot/stream")
async def copilot_stream(req):
    form = await req.form()
    msg = (form.get("message") or "").strip()

    async def gen():
        if not msg:
            yield _sse("done", {}); return
        from utils.copilot import answer_stream
        got = False
        try:
            async for ev, data in answer_stream(msg):
                if ev == "token":
                    got = True; yield _sse("token", {"text": data})
                elif ev == "tool_start":
                    yield _sse("tool_start", data)
                elif ev == "error":
                    yield _sse("error", {"message": data})
        except Exception as e:  # noqa: BLE001
            yield _sse("error", {"message": str(e)})
        if not got:
            yield _sse("token", {"text": "(no response)"})
        yield _sse("done", {})

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
