# Directive — Trust Radar

## Goal
Read escalation and win-back call transcripts. Classify the situation — genuine loss of trust vs using dissatisfaction as leverage — and recommend a specific response strategy.

## Inputs
| Source | What to pull | Provider |
|---|---|---|
| Call recording tool | Full transcript of the escalation or win-back call | `transcript_provider` in config.yaml |
| Helpdesk | Open tickets, ticket history, unresolved issues | `support_provider` in config.yaml |
| CRM | Account health, NPS history, previous escalations | `crm_provider` in config.yaml |
| Sample data | `sample_data/account.json`, `sample_data/transcript.json`, `sample_data/tickets.json`, `sample_data/notes.json` | fallback when provider = manual |

## Output
JSON with keys:
- `classification` — `GENUINE_LOSS_OF_TRUST` | `NEGOTIATING` | `MIXED` | `UNCLEAR`
- `confidence` — 0.0–1.0
- `reasoning` — 2–4 sentences explaining the classification, citing specific evidence
- `evidence_snippets` — list of `{timestamp, speaker, text, signal_type, confidence}` — the moments that drove the classification
- `response_strategy` — specific, actionable guidance for the CSM. What to say, what not to say, what to do in the next 24h
- `urgency_score` — 1–10
- `recommended_actions` — ordered list of next steps

## Execution
- **Test (no setup):** `python3 test.py`
- **Local:** `python3 local.py`
- **Cloud:** `modal deploy execution/main.py`

## LLM Prompt Rules
- Return JSON only
- `reasoning` must cite specific moments from the transcript — not general impressions
- `response_strategy` must be concrete: what to say, not what to consider
- `evidence_snippets` must include the actual text from the transcript, not a paraphrase
- Distinguish carefully: conditional threats ("if you do X by Y, I'll stay") = negotiating. No conditions, no engagement with solutions = genuine loss of trust.

## Classification Guide
**GENUINE_LOSS_OF_TRUST signals:**
- Customer disengages from problem-solving ("it doesn't matter anymore")
- Refuses to give a specific bar to clear
- Mentions competitor by name with positive framing
- Tone is resigned, not angry
- Has stopped raising issues (went quiet before this call)

**NEGOTIATING signals:**
- Customer gives a specific, achievable condition ("if you do X by Y")
- Anger is focused on a specific issue, not the relationship
- Customer is still engaged, asking questions, pushing back
- "We're evaluating alternatives" — without specifics = often leverage
- Call happened at all — customers who are truly gone don't do win-back calls

## Edge Cases
- Transcript too short (<5 min) → classify as `UNCLEAR`, note insufficient data
- Customer is primarily complaining about pricing → likely negotiating unless relationship signals suggest otherwise
- LLM call fails → fall back to `MOCK_OUTPUT`, log the error

## Adding a New Provider
See `directives/churn-risk-summarizer.md` for the pattern.

## Learnings
<!-- Append lessons here as you build. Format: YYYY-MM-DD — [what you learned] -->
