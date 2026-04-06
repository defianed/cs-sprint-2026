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
    "summary": "Acme Corp is showing early-to-mid churn indicators: login drop, ghost users, a stalled support ticket, and two missed check-ins.",
    "risk_story": "Acme Corp started strong but has gone quiet. Two users — Tom and Alicia — haven't logged in since February. The Salesforce sync ticket has been open 14 days with no resolution date, and their COO scored renewal confidence at 6/10 in today's QBR. The open ticket is the most urgent issue: at this stage, an unresolved support problem becomes the reason they leave.",
    "primary_risks": [
        "14-day open Salesforce sync ticket — COO is tracking it personally",
        "Login frequency down 40% — 2 ghost users since February",
        "Missed last 2 monthly check-ins — two-month communication gap",
        "NPS dropped from 8 to 6 in latest survey"
    ],
    "stabilizers": [
        "Core workflow still in use by 61 of 100 seats",
        "Renewal is 189 days away — time to course-correct",
        "COO said 'we're not looking around' — no confirmed competitor evaluation",
        "Both Marcus and Dana engaged in today's QBR and gave specific conditions"
    ],
    "next_call_focus": [
        "Lead with the Salesforce ticket — give a written resolution date before end of day",
        "Schedule separate 30-min call with Tom and Alicia — listening only, no sales",
        "Propose monthly check-ins with fixed agenda starting April",
        "Ask directly what would move their renewal confidence from 6 to 8"
    ],
    "urgency": "high"
}


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


def call_llm(prompt: str) -> str:
    provider = get_provider()
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        return resp.choices[0].message.content
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6"),
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def build_risk_story(data: dict) -> dict:
    prompt = f"""Return JSON only.
Create a plain-language churn risk story from the account context below.

Context:
{json.dumps(data, indent=2)}

Return keys: summary, risk_story, primary_risks (list), stabilizers (list), next_call_focus (list), urgency."""
    raw = call_llm(prompt)
    for marker in ["```json", "```"]:
        if marker in raw:
            raw = raw.split(marker)[1].split("```")[0]
            break
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"summary": "Parse error", "risk_story": raw[:300], "primary_risks": [], "stabilizers": [], "next_call_focus": [], "urgency": "unknown"}


def main():
    data = load_sample_data()
    account_name = data.get("account", {}).get("name", "Acme Corp")
    print(f"Churn Risk Summarizer — {account_name}\n")

    if LIVE_MODE and has_api_key():
        print(f"[LIVE] API key found — calling {get_provider()} with sample data...\n")
        result = build_risk_story(data)
    else:
        print("[MOCK] No API key — showing sample output.")
        print("       Set ANTHROPIC_API_KEY or OPENAI_API_KEY to call live LLM.\n")
        result = MOCK_OUTPUT

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
