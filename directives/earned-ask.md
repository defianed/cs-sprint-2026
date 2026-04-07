# Directive — Earned Ask

## Goal
Identify the exact right moment to ask a customer for a G2 review or referral — and draft the outreach so the CSM can send in one click.

## Inputs
| Source | What to pull | Provider |
|---|---|---|
| CS Platform / CRM | NPS score (current + trend), health score, account tenure | `crm_provider` in config.yaml |
| Call recording tool | Recent sentiment signals from transcripts | `transcript_provider` in config.yaml |
| CRM | Milestones completed, referrals already given, last ask date | `crm_provider` in config.yaml |
| Sample data | `sample_data/account.json`, `sample_data/transcript.json`, `sample_data/notes.json` | fallback when provider = manual |

## Output
JSON with keys:
- `ask_recommended` — `true` | `false`
- `confidence` — 0.0–1.0
- `reason` — why now is (or isn't) the right moment
- `ask_type` — `g2_review` | `referral` | `case_study` | `none`
- `email_draft` — complete email draft ready to send, personalised to the account
- `send_timing` — recommended send time (e.g. "within 48h", "after next QBR")

## Execution
- **Test (no setup):** `python3 test.py`
- **Local:** `python3 local.py`
- **Cloud:** `modal deploy execution/main.py`

## LLM Prompt Rules
- Return JSON only
- `email_draft` must sound human — not templated. Reference something specific about the account.
- Do not recommend an ask if NPS < 8, health score is declining, or there's an open support issue
- Do not recommend an ask if one was sent in the last 90 days (check CRM notes)
- `reason` should explain the positive signals, not just say "NPS is high"

## Right Conditions for an Ask
All of the following should be true:
- NPS ≥ 8 (or strong positive sentiment in recent call)
- No open P1/P2 support tickets
- Account has been live ≥ 3 months
- No ask sent in last 90 days
- At least one meaningful milestone completed

Bonus signals that increase confidence:
- Customer mentioned the product positively unprompted on a call
- Customer referred someone informally
- Health score trending up
- QBR went well

## Edge Cases
- No NPS data → base on call sentiment and health score only, lower confidence
- Customer has already given a G2 review → switch `ask_type` to `referral` or `case_study`
- LLM call fails → fall back to `MOCK_OUTPUT`, log the error

## Adding a New Provider
See `directives/churn-risk-summarizer.md` for the pattern.

## Learnings
<!-- Append lessons here as you build. Format: YYYY-MM-DD — [what you learned] -->
