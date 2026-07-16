# Factorio — Admin (Back Office) User Guide

**For internal users: operations, credit, collections, finance, compliance, executives.**

The back office runs the factoring business behind the customer-facing portal —
onboarding, risk, funding, collections, reporting and compliance — under
role-based access control with full audit logging. It is reached at **`/app/admin`**
when signed in with the **Admin** role, and is organised as a left-nav cockpit
with an always-present AI **copilot** for asking questions about the data.

This guide maps each screen to the eight core back-office functional areas.

---

## The cockpit

The workspace is a three-pane cockpit: left navigation (Factoring · Sales ·
Workspace), the center content, and a right-hand **copilot** that answers
questions about funding, exposure, the pipeline and portfolio by querying live
data. The **Role** switcher (top-right) changes persona; the sub-role
(Operations / Credit / Collections / Finance / Compliance / Executive /
Super-admin) scopes what actions you can take (segregation of duties).

![Admin console](img/role-admin-console.png)

---

## 1 · Client & debtor onboarding / management
**Screen: Onboarding.** KYC/AML status per client and debtor, sector, country,
annual turnover, and a derived **facility limit** (advance rates 70–90%). Only
**Credit / Compliance / Super** may set limits — other roles see the data
read-only (segregation of duties).

![Onboarding](img/role-admin-onboarding.png)

## 2 · Invoice processing & verification
Invoices arrive verified against SoliqOnline (buyer-confirmed), assigned, and
risk-graded. The pipeline and detail views show amount, advance rate, grade and
status; holdback/reserve is the difference between face value and advance.

## 3 · Funding & disbursements
**Screen: Funding.** The funding pipeline lists verified/funding invoices with
amount, grade, computed advance and status. **Approve & release** is gated to
**Finance / Super** — a credit officer cannot release funds. Every approval is
written to the audit log.

![Funding & collections](img/role-admin-funding.png)

## 4 · Collections & credit management
Same screen: an **overdue / collections** table with a dunning stage per
invoice. Reminders escalate; disputes and write-offs are handled here (write-off
is Finance/Compliance-gated).

## 5 · Risk management & underwriting
**Screen: Risk.** Risk-grade distribution (A–D), **exposure by sector**,
**debtor concentration**, and a **duplicate-invoice fraud check**. This is the
underwriting and portfolio-risk cockpit.

![Risk & underwriting](img/role-admin-risk.png)

## 6 · Accounting & financial operations
**Screen: Accounting.** A **production double-entry general ledger**, derived
deterministically from the factoring events (advances, settlements, fees,
write-offs) so it always ties out. Includes a **trial balance** (chart of
accounts with debit/credit and a balanced total), a **journal**, per-account
**ledger drill-down**, and **bank reconciliation** (matched vs unmatched). Scoped
to Finance / Compliance / Executive / Super (segregation of duties).

![Trial balance](img/role-admin-accounting.png)
![Journal](img/role-admin-journal.png)
![Bank reconciliation](img/role-admin-reconciliation.png)

Reporting KPIs (DSO, default rate, funded volume by sector) live on the Reports
screen:

![Reports](img/role-admin-reports.png)

## 7 · Reporting & analytics
Reports plus the **copilot**: ask "which sector has the most exposure?", "top
debtors", "summarise the pipeline" and get grounded, real-number answers.

## 8 · Compliance, legal & audit
**Screen: Audit log.** Every state-changing action — who (actor + role), what
action, which entity, when — is recorded immutably. This underpins SoD,
regulatory reporting and dispute evidence.

![Audit log](img/role-admin-audit.png)

---

## Workspace modules (back-office tooling)

### Sales pipeline (CRM)
A kanban pipeline for **back-office sales** — deals by stage (Qualification →
Demo → Proposal → Negotiation → Ready to close), value and owner. Ported from
FastCRM.

![Sales pipeline](img/role-admin-crm.png)

### Drive · Docs · Mail
- **Drive** — invoice, KYC and collateral documents (folders, sharing, links).
- **Docs** — policies, playbooks and term sheets (block editor, versions).
- **Mail** — client, debtor and bureau correspondence (threads, AI draft replies).

![Drive](img/role-admin-drive.png)
![Docs](img/role-admin-docs.png)
![Mail](img/role-admin-mail.png)

---

## RBAC & segregation of duties (summary)
| Action | Who may act |
|---|---|
| Set facility limits | Credit · Compliance · Super |
| Approve / release funding | Finance · Super |
| Run collections / dunning | Collections · Super |
| Write-off / provision | Finance · Compliance · Super |
| View audit log | Compliance · Executive · Super |

Roadmap (see `enterprise_extension_plan.md`): real auth (login/SSO/MFA),
ledger/reconciliation, credit-scoring engine with back-testing, and full
accounting/bank/bureau integrations.
