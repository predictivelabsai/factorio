#!/usr/bin/env python3
"""Send email from the Consistente IONOS UK mailbox.

Credentials are read from ``config/credentials.yaml`` (gitignored) — the same
layout as the tendly repo — so no secret ever appears in this script or in git.

Examples::

    python -m scripts.send_email --to a@x.com --subject "Hi" --body "Hello"
    python -m scripts.send_email --to a@x.com --to b@y.com \
        --subject S --body @letter.txt --html @letter.html \
        --attach docs/universalbank_consistente_proposal_en.pdf

A --body / --html value starting with ``@`` is read from that file path.
On success a copy is best-effort APPENDed to the IMAP "Sent" folder.
"""

from __future__ import annotations

import argparse
import mimetypes
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CREDS = ROOT / "config" / "credentials.yaml"


def _load_business_email() -> dict:
    if not CREDS.exists():
        raise SystemExit(f"Missing {CREDS} — add the IONOS credentials there (gitignored).")
    data = yaml.safe_load(CREDS.read_text(encoding="utf-8"))
    be = (data or {}).get("business_email")
    if not be:
        raise SystemExit(f"No 'business_email' entry in {CREDS}.")
    return be


def _read_arg(value: str | None) -> str | None:
    if value is None:
        return None
    if value.startswith("@"):
        return Path(value[1:]).read_text(encoding="utf-8")
    return value


def send_email(to, subject, body, *, html_body=None, attachments=None,
               cc=None, bcc=None, reply_to=None, append_to_sent="Sent"):
    be = _load_business_email()
    mailbox, password = be["mailbox"], be["password"]
    from_name = be.get("from_name", "Julian Kaljuvee")
    smtp, imap = be["smtp"], be.get("imap")

    to_list = [to] if isinstance(to, str) else list(to)
    cc_list = list(cc or [])
    bcc_list = list(bcc or [])

    msg = EmailMessage()
    msg["From"] = f"{from_name} <{mailbox}>"
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg["Subject"] = subject
    msg["Message-Id"] = make_msgid(domain=mailbox.split("@", 1)[-1])
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    for att in attachments or []:
        p = Path(att)
        ctype, _ = mimetypes.guess_type(p.name)
        maintype, _, subtype = (ctype or "application/octet-stream").partition("/")
        msg.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp["host"], int(smtp["port"]), context=ctx, timeout=30) as server:
        server.login(mailbox, password)
        server.send_message(msg, to_addrs=to_list + cc_list + bcc_list)

    if append_to_sent and imap:
        try:
            import imaplib
            with imaplib.IMAP4_SSL(imap["host"], int(imap["port"]), timeout=30) as im:
                im.login(mailbox, password)
                im.append(f'"{append_to_sent}"', r"\Seen", None, msg.as_bytes())
        except Exception as e:  # noqa: BLE001 - Sent append is best-effort
            print(f"  (note: could not append to Sent: {e})")
    return msg["Message-Id"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--to", action="append", required=True, help="Recipient (repeatable).")
    ap.add_argument("--cc", action="append", default=[])
    ap.add_argument("--bcc", action="append", default=[])
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body", required=True, help="Plain text, or @path.")
    ap.add_argument("--html", default=None, help="HTML body, or @path.")
    ap.add_argument("--attach", action="append", default=[], help="Attachment path (repeatable).")
    ap.add_argument("--reply-to", default=None)
    args = ap.parse_args()

    mid = send_email(
        to=args.to, cc=args.cc, bcc=args.bcc, subject=args.subject,
        body=_read_arg(args.body), html_body=_read_arg(args.html),
        attachments=args.attach, reply_to=args.reply_to,
    )
    print(f"Sent to {', '.join(args.to)} — Message-Id {mid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
