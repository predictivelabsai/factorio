#!/usr/bin/env python3
"""Poll the Consistente inbox for a reply from Universalbank (Ulugbek).

Reads IONOS credentials from ``config/credentials.yaml`` (gitignored). Searches
the mailbox (INBOX + Spam) for messages from the target sender/domain, tracks
which it has already seen in a local state file so it never double-alerts, and
— by default — emails a heads-up to a notify address when a NEW reply lands.

Built to run on a schedule (cron) or via the `check-universalbank-reply` skill.

    python -m scripts.check_reply                       # default: from universalbank.uz, notify kaljuvee@gmail.com
    python -m scripts.check_reply --from universalbank.uz --notify kaljuvee@gmail.com
    python -m scripts.check_reply --no-notify           # just print, don't email
    python -m scripts.check_reply --list                # show all matches (ignore seen-state)

Exit code 0 = ran OK (10 = a NEW reply was found, for easy cron/if-checks).
"""

from __future__ import annotations

import argparse
import email
import imaplib
import json
import sys
from datetime import datetime, timezone
from email.header import decode_header, make_header
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CREDS = ROOT / "config" / "credentials.yaml"
STATE = ROOT / "reply_state.json"

DEFAULT_FROM = "universalbank.uz"
DEFAULT_NOTIFY = "kaljuvee@gmail.com"
FOLDERS = ("INBOX", "Spam")


def _mailbox() -> dict:
    if not CREDS.exists():
        sys.exit(f"Missing {CREDS} (gitignored) — add the IONOS business_email block.")
    be = (yaml.safe_load(CREDS.read_text(encoding="utf-8")) or {}).get("business_email")
    if not be:
        sys.exit(f"No 'business_email' entry in {CREDS}.")
    return be


def _hdr(msg, key: str) -> str:
    try:
        return str(make_header(decode_header(msg.get(key, ""))))
    except Exception:
        return msg.get(key, "")


def _load_state() -> set[str]:
    try:
        return set(json.loads(STATE.read_text()).get("seen", []))
    except Exception:
        return set()


def _save_state(seen: set[str]) -> None:
    STATE.write_text(json.dumps({"seen": sorted(seen),
                                 "updated": datetime.now(timezone.utc).isoformat()}, indent=2))


def find_replies(from_match: str) -> list[dict]:
    be = _mailbox()
    out: list[dict] = []
    im = imaplib.IMAP4_SSL(be["imap"]["host"], int(be["imap"]["port"]), timeout=30)
    im.login(be["mailbox"], be["password"])
    try:
        for folder in FOLDERS:
            typ, _ = im.select(f'"{folder}"', readonly=True)
            if typ != "OK":
                continue
            typ, data = im.search(None, "FROM", from_match)
            if typ != "OK":
                continue
            for i in data[0].split():
                typ, md = im.fetch(i, "(BODY.PEEK[HEADER])")
                m = email.message_from_bytes(md[0][1])
                out.append({
                    "folder": folder,
                    "message_id": (m.get("Message-Id") or f"{folder}:{i.decode()}").strip(),
                    "from": _hdr(m, "From"),
                    "subject": _hdr(m, "Subject"),
                    "date": _hdr(m, "Date"),
                })
    finally:
        try:
            im.logout()
        except Exception:
            pass
    return out


def _notify(to_addr: str, replies: list[dict]) -> None:
    from scripts.send_email import send_email
    lines = ["A reply from Universalbank has arrived in the Consistente inbox:\n"]
    for r in replies:
        lines.append(f"• From: {r['from']}\n  Subject: {r['subject']}\n  Date: {r['date']}  [{r['folder']}]\n")
    lines.append("\nOpen https://mail.ionos.co.uk (julian.kaljuvee@consistente.tech) to read and respond.")
    send_email(to=to_addr,
               subject=f"↩︎ Universalbank replied — {replies[0]['subject'][:60]}",
               body="\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="from_match", default=DEFAULT_FROM,
                    help="Sender address or domain to match (default: universalbank.uz)")
    ap.add_argument("--notify", default=DEFAULT_NOTIFY, help="Email to alert on a new reply")
    ap.add_argument("--no-notify", action="store_true", help="Print only; do not send an alert email")
    ap.add_argument("--list", action="store_true", help="List all matches, ignoring seen-state")
    args = ap.parse_args()

    replies = find_replies(args.from_match)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if args.list:
        print(f"[{stamp}] {len(replies)} message(s) from {args.from_match}:")
        for r in replies:
            print(f"  [{r['folder']}] {r['date']} | {r['from']} | {r['subject']}")
        return 0

    seen = _load_state()
    fresh = [r for r in replies if r["message_id"] not in seen]
    if not fresh:
        print(f"[{stamp}] no new reply from {args.from_match} ({len(replies)} known).")
        return 0

    print(f"[{stamp}] {len(fresh)} NEW repl(y/ies) from {args.from_match}:")
    for r in fresh:
        print(f"  [{r['folder']}] {r['date']} | {r['from']} | {r['subject']}")
    if not args.no_notify:
        try:
            _notify(args.notify, fresh)
            print(f"  alerted {args.notify}")
        except Exception as e:  # noqa: BLE001
            print(f"  (could not send alert: {e})")
    _save_state(seen | {r["message_id"] for r in fresh})
    return 10


if __name__ == "__main__":
    raise SystemExit(main())
