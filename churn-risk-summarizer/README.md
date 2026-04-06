# Churn Risk Summarizer

Turns recent customer activity into a plain-language churn risk narrative before a QBR or renewal call.

Not a health score. An actual story you can use in the conversation.

## Three ways to run

| Mode | Command | Requires |
|---|---|---|
| Instant demo | `python3 test.py` | Nothing |
| Local real run | `python3 local.py` | API key in `.env` |
| Cloud deploy | `modal deploy execution/main.py` | Modal account |

## Quickstart

```bash
# Step 1: Install dependencies
pip install -r requirements.txt

# Step 2: See it work immediately (sample data, no API key needed)
python3 test.py

# Step 3: Set up your API key
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY (or OPENAI_API_KEY)

# Step 4: Run with real AI locally
python3 local.py
```

## What it does

Analyses account activity, support friction, and engagement changes to build a narrative explaining what is driving current churn risk. Highlights stabilisers and the most important next-call focus areas.

## What you get

```json
{
  "summary": "One-sentence read on the account",
  "risk_story": "Plain-language narrative — use this in your next call",
  "primary_risks": ["..."],
  "stabilizers": ["..."],
  "next_call_focus": ["..."],
  "urgency": "high / medium / low"
}
```

## Customising the input

Edit `.env` or set environment variables:
```
ACCOUNT_NAME=Acme Corp
RECENT_ACTIVITY=Login frequency dropped 40%...
SUPPORT_SUMMARY=3 tickets in past 30 days...
ENGAGEMENT_SUMMARY=Skipped last 2 check-ins...
```

## Note

This workflow processes text inputs (activity summaries, support notes, engagement data). It does not connect directly to CRM or support systems out of the box — you feed it the context, it generates the narrative.

## Environment variables

See `.env.example`. Only `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) is required.
