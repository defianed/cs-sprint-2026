# Expansion Signal Detector

Scans call transcripts and post-call notes for signals that a customer is ready to expand.

Surface the upsell conversation before the moment passes.

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

Analyses account context, transcript snippets, and usage notes to identify expansion buying signals, blockers, and the right timing for an expansion conversation.

## What you get

```json
{
  "expansion_ready": true,
  "confidence": 0.82,
  "buying_signals": ["..."],
  "blockers": ["..."],
  "recommended_timing": "When to have the conversation",
  "next_steps": ["..."],
  "rationale": "Why this recommendation"
}
```

## Customising the input

Edit `.env` or set environment variables:
```
ACCOUNT_NAME=ScaleUp Ltd
TRANSCRIPT_SNIPPETS=We're rolling this out to sales next quarter...
POST_CALL_NOTES=At 95 of 100 seats, budget opens in Q3...
USAGE_SUMMARY=API calls up 40% month-over-month...
```

## Note

This workflow processes text inputs you supply. It does not connect directly to CRM or call recording systems out of the box.

## Environment variables

See `.env.example`. Only `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) is required.
