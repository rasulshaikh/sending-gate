# Sending Gate workflow

## Goal

Decide PASS / FLAG / FAIL for each outbound row **before** it reaches Smartlead, HeyReach, or another sequencer.

Production Clay workflows (enrichment waterfalls, AI columns, client-specific prompts) stay in your private stack. This document describes the open gate core only.

## Inputs

Minimum fields per row (JSON object or CSV columns):

| Field | Required | Notes |
| --- | --- | --- |
| `email` | yes | Work email to send to |
| `first_name` | yes* | Or `full_name` if your policy allows |
| `company_name` | yes | Display / personalization |
| `company_domain` | recommended | Used for mismatch checks |
| `subject` | yes | Final subject |
| `body` | yes | Final body (plain text) |
| `sequence_key` | optional | Target sequence id or name |
| `icp_score` | optional | 0 to 100 from Clay |

\* If `full_name` is present and `first_name` is empty, the gate derives a first token.

## Phase 1: Validate

Hard checks (any failure => row cannot be PASS):

1. `email` present and matches a simple `local@domain.tld` pattern
2. Role-account local parts flagged (`info`, `hello`, `support`, `admin`, `sales`) when `reject_role_accounts` is true (default true)
3. `subject` and `body` non-empty after trim
4. No placeholder tokens: `{{`, `}}`, `TBD`, `TODO`, `[insert`, `xxx@`
5. Duplicate `email` inside the batch => FAIL on duplicates after the first
6. If `company_domain` and email domain disagree, FLAG (not automatic FAIL)

## Phase 2: Score

Start at 100. Apply deductions:

| Condition | Deduction |
| --- | --- |
| Missing `company_domain` | 5 |
| Email / domain mismatch | 15 |
| Body word count < 30 or > 180 | 10 |
| Subject length < 8 or > 80 | 5 |
| `icp_score` present and < 50 | 20 |
| Role account (if not hard-rejected) | 25 |
| Body contains "leverage" or "synergy" (AI-smell soft list) | 5 each, max 10 |

Clamp to 0..100.

## Phase 3: Block / allow

| Condition | Verdict |
| --- | --- |
| Any hard validation failure | FAIL |
| Score >= 80 and no soft flags | PASS |
| Score >= 60 or soft flags only | FLAG |
| Score < 60 | FAIL |

Soft flags include domain mismatch and AI-smell hits when validation otherwise passed.

## Batch summary

Emit:

- counts of PASS / FLAG / FAIL
- list of FAIL reasons (top N)
- optional allowlist file containing only PASS rows (and FLAG if `--include-flag`)

## Clay mapping tips

1. Add a final Clay view that only includes rows you intend to export.
2. Map gate output columns back if you re-import: `gate_verdict`, `gate_score`, `gate_reasons`.
3. Keep sequencer push as a manual or separate automation step after PASS.

## Non-goals

- Not a deliverability warm-up tool
- Not a full compliance engine
- Not a substitute for your private Clay production workbook
