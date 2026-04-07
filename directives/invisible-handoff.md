# Directive — Invisible Handoff

## Goal
When a deal closes, automatically generate a CSM handoff brief from the sales call transcript and CRM deal data — delivered to the assigned CSM before the kickoff call.

## Inputs
| Source | What to pull | Provider |
|---|---|---|
| Call recording tool | Closed Won call transcript (most recent) | `transcript_provider` in config.yaml |
| CRM | Deal name, ACV, close date, assigned CSM, key contacts, deal notes | `crm_provider` in config.yaml |
| Helpdesk | Any pre-sales support tickets (if applicable) | `support_provider` in config.yaml |
| Sample data | `sample_data/account.json`, `sample_data/transcript.json`, `sample_data/notes.json` | fallback when provider = manual |

## Output
JSON with keys:
- `account_name` — company name
- `csm_name` — assigned CSM
- `why_they_bought` — 2–3 sentences: problem they were solving, what tipped them
- `what_was_promised` — specific commitments made during the sales process
- `who_to_know` — list of key contacts: name, role, what to know about them
- `first_30_days` — ordered list of priorities for the first month
- `watch_out_for` — potential friction points or sensitivities from the sales process
- `slack_message` — ready-to-send Slack DM to the CSM (≤150 words)

## Execution
- **Test (no setup):** `python3 test.py`
- **Local:** `python3 local.py`
- **Cloud:** `modal deploy execution/main.py`

## LLM Prompt Rules
- Return JSON only
- `what_was_promised` must be specific commitments, not vague reassurances — look for dates, features, integrations, response time SLAs
- `watch_out_for` should surface anything the CSM needs to know that wasn't in the formal deal notes
- `slack_message` must be conversational, not a report — written as if from a colleague

## Edge Cases
- No sales transcript → generate brief from CRM deal notes only, flag that transcript was unavailable
- CSM not assigned in CRM → omit `csm_name`, do not fail
- LLM call fails → fall back to `MOCK_OUTPUT`, log the error

## Adding a New Provider
See `directives/churn-risk-summarizer.md` for the pattern. Same approach applies here.

## Learnings
<!-- Append lessons here as you build. Format: YYYY-MM-DD — [what you learned] -->
