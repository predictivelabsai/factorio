---
name: deploy-factorio
description: Deploy / redeploy the Factorio app to production (factorio.co.uk) via the Coolify PaaS, and check its deploy status. Use when the user asks to deploy, redeploy, ship, release, or check whether factorio.co.uk is up to date.
---

# Deploy Factorio (Coolify)

Factorio is hosted on a self-hosted **Coolify** instance and served at
**factorio.co.uk**. **Auto Deploy is ENABLED** (Configuration → Advanced →
"Auto Deploy" is checked), so pushing to `main` triggers a build+rollout via the
GitHub webhook — verified 2026-07-16, when a push built commit `e15de2c`
automatically before a manual Redeploy even ran ("image found with the same Git
Commit SHA — build step skipped"). A **manual Redeploy** in Coolify remains the
guaranteed way to force a rollout (e.g. if the webhook is slow or you want to be
certain the latest commit is live).

## Where it lives
- **Coolify:** `https://coolify.finespresso.org`
- **Team:** `Finespresso Team`  → **Project:** `predictive labs apps` → **Application:** `predictivelabsai/factorio`
- **App config page:** `.../application/vsc4ws8g40cswoss40g0o48k`
- Build pack: **Dockerfile**. Domain: `https://factorio.co.uk`.
- Credentials are in `config/credentials.yaml` (gitignored) under the `coolify:` key
  (url / email / password / app_config URL).

## Deploy steps (browser automation — Playwright/Chrome MCP)
1. Commit + push your changes to `main` first (Coolify builds from the pushed commit).
2. Log in at `https://coolify.finespresso.org/login` with the `coolify` email/password
   from `config/credentials.yaml`.
3. If the current team is wrong (Projects shows only "Kanvas"), switch team to
   **Finespresso Team** (team switcher, top-left dropdown / `/team`).
4. Open the app config page (the `app_config` URL above), or navigate:
   Projects → *predictive labs apps* → *predictivelabsai/factorio*.
5. Dismiss any "Cannot connect to real-time service" popup (Acknowledge & Disable).
6. Click **Redeploy** (top-right). It opens a Deployment page — confirm the log shows
   *"Starting deployment … (commit sha <your latest>)"* and **In Progress**.
7. Wait a few minutes (Docker build). Then verify: `curl -s https://factorio.co.uk/`
   should reflect the new build (e.g. contains `Explore your sector`, `Multidivisa`
   in ES, or whatever your change added).

## Notes
- The app reads `DB_URL` / `XAI_API_KEY` etc. from Coolify **Environment Variables**
  (not from local `.env`). New DB tables are created lazily (schema uses
  `CREATE TABLE IF NOT EXISTS`), so no manual migration step is needed on deploy.
- To fix the root cause (auto-deploy on push), check the app's **Webhooks** tab and
  the GitHub repo webhook; that's separate from the manual Redeploy above.
