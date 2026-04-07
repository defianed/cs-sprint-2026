# Directive — Churn Risk Summarizer

## Goal
Before every QBR or renewal call, produce a plain-language churn risk brief for the CSM — no manual data gathering required.

## Inputs
| Source | What to pull | Provider |
|---|---|---|
| Call recording tool | Latest 1–2 transcripts for the account | `transcript_provider` in config.yaml |
| Helpdesk | Open tickets, age, priority, last response | `support_provider` in config.yaml |
| CRM | Account health score, NPS, renewal date, champion, last activity | `crm_provider` in config.yaml |
| Sample data | `sample_data/account.json`, `sample_data/transcript.json`, `sample_data/tickets.json`, `sample_data/notes.json` | fallback when provider = manual |

## Output
JSON with keys:
- `summary` — 1-sentence risk classification
- `risk_story` — 3–5 sentence narrative of what's happening and why it matters
- `primary_risks` — list of specific, named risks (not generic statements)
- `stabilizers` — what's working in the account's favour
- `next_call_focus` — ordered list of talking points for the CSM
- `urgency` — `high` | `medium` | `low`

## Execution
- **Test (no setup):** `python3 test.py` — always works, uses hardcoded mock output
- **Local:** `python3 local.py` — reads providers from config.yaml, calls LLM if API key is set
- **Cloud:** `modal deploy execution/main.py`

## LLM Prompt Rules
- Return JSON only — no markdown, no preamble
- `risk_story` must be a narrative, not a bullet list
- `primary_risks` must be specific: name the ticket, the person, the metric — not "there are some open tickets"
- If data is sparse, say so in `risk_story` rather than hallucinating detail

## Edge Cases
- No transcripts available → note in `risk_story`, don't fail
- No open tickets → `primary_risks` can be empty, adjust `urgency` accordingly
- LLM call fails → fall back to `MOCK_OUTPUT` in `local.py`, log the error

## Adding a New Provider
1. Open `local.py`, find the `# --- Provider ---` comment block
2. Add `elif config.get("crm_provider") == "your_provider":` and fetch data
3. Map response to the same shape as `sample_data/account.json`
4. Add credentials to `.env.example` with placeholder values
5. Test with `python3 local.py`
6. Document the provider here under a new `## Provider: YourProvider` section

## Learnings
<!-- Append lessons here as you build. Format: YYYY-MM-DD — [what you learned] -->
