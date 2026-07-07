---
name: check-universalbank-reply
description: Poll the Consistente inbox (julian.kaljuvee@consistente.tech) for a reply from Universalbank / Ulugbek Tavakkalov to the Factorio proposal, and alert when one arrives. Use when the user asks to check for, watch, or poll Ulugbek's / Universalbank's reply, or to see whether the bank has responded.
---

# Check for a Universalbank reply

The Factorio proposal cover letter was sent to `Ulugbek.Tavakkalov@universalbank.uz`
with `Reply-To: julian.kaljuvee@consistente.tech`, so any reply lands in the
**Consistente IONOS inbox**. This skill polls that inbox for a reply and, by
default, emails a heads-up to `kaljuvee@gmail.com` the first time a new one appears.

## How to run

From the repo root (`/home/julian/dev/plai/factorio`), with the virtualenv:

```bash
.venv/bin/python -m scripts.check_reply              # check + alert on a NEW reply
.venv/bin/python -m scripts.check_reply --no-notify  # just print, no alert email
.venv/bin/python -m scripts.check_reply --list       # list everything from universalbank.uz
```

- Credentials come from `config/credentials.yaml` (gitignored) → `business_email`.
- It searches **INBOX + Spam** for mail `FROM universalbank.uz`.
- Seen replies are remembered in `reply_state.json` (gitignored) so it never
  double-alerts. Exit code **10** means a *new* reply was found (0 = nothing new).
- Override the sender or alert target: `--from universalbank.uz --notify someone@example.com`.

## Scheduled polling

A local cron entry runs this every 30 minutes and logs to `logs/reply_check.log`:

```
*/30 * * * * cd /home/julian/dev/plai/factorio && ./.venv/bin/python -m scripts.check_reply >> logs/reply_check.log 2>&1
```

- Inspect: `crontab -l`
- Tail the log: `tail -f logs/reply_check.log`
- Remove the schedule: `crontab -l | grep -v scripts.check_reply | crontab -`

When a reply is detected, read and respond via webmail
(<https://mail.ionos.co.uk>, `julian.kaljuvee@consistente.tech`) or send with
`scripts/send_email.py`.
