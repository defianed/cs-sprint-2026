# Directive — Expansion Signal Detector

## Goal
After every customer call, scan the transcript for upsell and expansion signals. Flag accounts where an expansion conversation is overdue based on usage data and what the customer said.

## Inputs
| Source | What to pull | Provider |
|---|---|---|
| Call recording tool | Latest call transcript | `transcript_provider` in config.yaml |
| CRM | Current plan, ACV, seats, account notes | `crm_provider` in config.yaml |
| Billing | Current MRR/ARR, plan tier, seat count | billing provider or CRM |
| Sample data | `sample_data/account.json`, `sample_data/transcript.json`, `sample_data/notes.json` | fallback when provider = manual |

## Output
JSON with keys:
- `expansion_ready` — `true` | `false`
- `confidence` — 0.0–1.0
- `buying_signals` — list of specific quotes or signals from the transcript
- `usage_signals` — seat utilisation %, usage trend, feature adoption gaps
- `recommended_ask` — what to propose and when
- `urgency` — `high` | `medium` | `low`
- `slack_message` — ready-to-send Slack alert to the CSM

## Execution
- **Test (no setup):** `python3 test.py`
- **Local:** `python3 local.py`
- **Cloud:** `modal deploy execution/main.py`

## LLM Prompt Rules
- Return JSON only
- `buying_signals` must include direct quotes where possible — not paraphrases
- Do not flag expansion if the customer expressed budget constraints or dissatisfaction in the same call
- `recommended_ask` should be specific: which product, which tier, which timing — not "consider upselling"

## Signal Types to Watch For
- Team growth mentions ("we're hiring 10 more reps in Q3")
- Feature requests that are on a higher tier
- Seat utilisation >85%
- Unprompted mentions of rolling out to other teams
- Positive NPS + high engagement + approaching tier limits
- Competitor comparison that favours you

## Edge Cases
- No transcript available → run on usage/billing signals only, set `confidence` lower
- Customer is churned or at risk → do not flag for expansion, skip
- LLM call fails → fall back to `MOCK_OUTPUT`, log the error

## Adding a New Provider
See `directives/churn-risk-summarizer.md` for the pattern.

## Learnings
<!-- Append lessons here as you build. Format: YYYY-MM-DD — [what you learned] -->
