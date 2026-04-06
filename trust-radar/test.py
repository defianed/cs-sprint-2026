# test.py — zero setup required. If API key found, calls real LLM with sample_data/.
# Otherwise prints labelled mock output and exits 0.
# Run: python3 test.py
import os, json, sys
LIVE_MODE = "--live" in sys.argv
from pathlib import Path

try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Load .env from repo root (one level up from workflow dir)
    _root = Path(__file__).parent.parent
    load_dotenv(_root / ".env")
    load_dotenv()  # fallback: local .env
except ImportError:
    pass

WORKFLOW_DIR = Path(__file__).parent

MOCK_OUTPUT = {
    "classification": "NEGOTIATING",
    "confidence": 0.82,
    "reasoning": "Sarah Mitchell's frustration is real — three missed API commitments caused 40 hours of manual work. But the language is classic negotiation, not relationship exit. The conditional offer at 03:18 is the tell: 'If you can get the API live by March 28 and give me written commitments on the next two milestones, I'll hold off the evaluation.' Someone who has genuinely lost trust doesn't give you a specific, actionable bar to clear. They leave quietly. She's giving you a very precise path to keep the account.",
    "evidence_snippets": [
        {
            "timestamp": "00:12",
            "speaker": "Sarah Mitchell",
            "text": "You've missed three commitments in a row. The API was supposed to be live in January. It's March.",
            "signal_type": "genuine_frustration",
            "confidence": 0.93
        },
        {
            "timestamp": "01:35",
            "speaker": "Sarah Mitchell",
            "text": "We are actively evaluating Salesforce and HubSpot right now. Just so you're aware.",
            "signal_type": "negotiation_leverage",
            "confidence": 0.87
        },
        {
            "timestamp": "03:18",
            "speaker": "Sarah Mitchell",
            "text": "If you can get the API live by March 28 and give me written commitments on the next two milestones, I'll hold off the evaluation.",
            "signal_type": "conditional_opening",
            "confidence": 0.91
        },
        {
            "timestamp": "04:08",
            "speaker": "Sarah Mitchell",
            "text": "Okay. I'll hold off calling DataBridge until I see it.",
            "signal_type": "door_left_open",
            "confidence": 0.88
        }
    ],
    "response_strategy": "Do not get defensive. Do not hedge. Confirm the API date with engineering today and deliver the CTO's written commitment by 5pm. Come back within 24 hours with: (1) written API GA date — March 28, no wriggle room, (2) written commitments on next two milestones with specific dates, (3) PM added to a weekly sync. She gave you a specific bar — clear it.",
    "urgency_score": 8,
    "recommended_actions": [
        "Deliver CTO written commitment letter to Sarah Mitchell by 5pm today",
        "Confirm API GA date (March 28) with engineering before sending anything",
        "Set up weekly PM sync — invite Sarah to the first one this week",
        "Do not offer financial concessions — she has not asked for them",
        "Follow up within 24 hours — do not let this go cold"
    ]
}

SYSTEM_PROMPT = """You are an expert CS analyst specialising in trust signals during win-back and escalation calls.

Classify trust status as one of:
- GENUINE_LOSS_OF_TRUST: real relationship damage, needs repair before anything else
- NEGOTIATING: customer is using dissatisfaction as leverage for concessions
- MIXED: genuine frustration with openness to repair
- UNCLEAR: insufficient signal to classify

Return JSON with keys:
classification, confidence (0.0-1.0), reasoning,
evidence_snippets (list of {timestamp, speaker, text, signal_type, confidence}),
response_strategy, urgency_score (1-10), recommended_actions (list)."""


def load_sample_data() -> dict:
    data = {}
    for filename in ["account.json", "transcript.json", "tickets.json"]:
        path = WORKFLOW_DIR / "sample_data" / filename
        if path.exists():
            key = filename.replace(".json", "")
            data[key] = json.loads(path.read_text())
    return data


def has_api_key() -> bool:
    ak = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    ok = (os.getenv("OPENAI_API_KEY") or "").strip()
    # Validate OpenAI key format — skip revoked/invalid keys
    return bool(ak) or (bool(ok) and ok.startswith("sk-"))


def get_provider() -> str:
    if (os.getenv("ANTHROPIC_API_KEY") or "").strip():
        return "anthropic"
    if (os.getenv("OPENAI_API_KEY") or "").strip():
        return "openai"
    return "anthropic"


def call_llm(system: str, user: str) -> str:
    provider = get_provider()
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6"),
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text


def analyse_trust(data: dict) -> dict:
    user_msg = f"Analyse this call and return your classification as JSON.\n\n{json.dumps(data, indent=2)}"
    raw = call_llm(SYSTEM_PROMPT, user_msg)
    for marker in ["```json", "```"]:
        if marker in raw:
            raw = raw.split(marker)[1].split("```")[0]
            break
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"classification": "UNCLEAR", "confidence": 0.0, "reasoning": f"Parse error: {raw[:300]}", "evidence_snippets": [], "response_strategy": "Manual review required.", "urgency_score": 5, "recommended_actions": []}


def main():
    data = load_sample_data()
    account_name = data.get("account", {}).get("name", "Acme Corp")
    print(f"Trust Radar — {account_name}\n")

    if LIVE_MODE and has_api_key():
        print(f"[LIVE] API key found — calling {get_provider()} with sample data...\n")
        result = analyse_trust(data)
    else:
        print("[MOCK] No API key — showing sample output.")
        print("       Set ANTHROPIC_API_KEY or OPENAI_API_KEY to call live LLM.\n")
        result = MOCK_OUTPUT

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
