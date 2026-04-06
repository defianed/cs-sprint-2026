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
    "account_overview": "Acme Corp is a 200-person fintech that closed a $48K ACV deal on 2026-03-20. Sarah Okonkwo (VP Engineering) is the champion who drove the eval. Mike Chen (CTO) is the economic buyer and is openly skeptical — he's been burned by vendor promises before. James Liu (Senior DevOps) will do the actual integration work and was not in any demos.",
    "customer_goals": [
        "Replace fragmented 3-tool toolchain with a single platform by Q3",
        "Reduce time-to-integrate from 3 weeks to under 5 days",
        "Hit Q3 product launch deadline (August 1) with API layer in place"
    ],
    "pain_points": [
        "Previous vendors had good uptime but terrible support SLAs — left them stranded",
        "Engineering team is stretched — migration overhead is costly",
        "CTO is skeptical of vendor commitments and will be watching closely"
    ],
    "commitments_made": [
        "API GA by May 15 — confirmed with product team, not estimated",
        "Marcus (senior onboarding engineer, ex-Stripe) assigned exclusively for 30 days",
        "Custom migration guide for Node.js + Postgres stack",
        "SOC 2 Type II report and pen test results sent with contract",
        "Milestone-based payment: 50% at kickoff, 50% on API GA",
        "30-day contract extension if API slips past May 15"
    ],
    "objections_handled": [
        "Security: SOC 2 Type II certified + pen test report provided",
        "Migration risk: Marcus has prior Node.js migration experience at Stripe",
        "Vendor reliability: milestone-based payments tied to delivery, not time",
        "Competitor comparison: outlined differentiators vs DataBridge and NovaSuite"
    ],
    "key_stakeholders": [
        {"name": "Sarah Okonkwo", "title": "VP Engineering", "role": "Champion — drove evaluation, day-to-day contact, highly bought-in"},
        {"name": "Mike Chen", "title": "CTO", "role": "Economic buyer — skeptical, wants written record of all commitments, will be watching"},
        {"name": "James Liu", "title": "Senior DevOps", "role": "Will own integration — was NOT in demos, get him into kickoff ASAP"}
    ],
    "urgency_timeline": "Q3 product launch is August 1 (hard deadline). API GA is May 15. First CSM call must happen within 24 hours of deal close (March 20). Kickoff with James must happen before April.",
    "watchouts": [
        "Mike's skepticism is real and earned — do not hedge or over-promise in his presence",
        "API GA date (May 15) is tight — reconfirm with product before first call, never guess",
        "James was not in any demos — he will have his own concerns, do not assume alignment",
        "Mike asked for a written record of everything promised — send deal summary today"
    ],
    "suggested_first_call_agenda": [
        "Introduce yourself and confirm you've read Jake's deal summary",
        "Introduce Marcus — confirm his 30-day exclusive availability",
        "Confirm API GA date (May 15) out loud and ask Mike to confirm he has it in writing",
        "Get James added to kickoff — ask Sarah to facilitate the intro",
        "Walk through migration guide outline — get James's input on Node.js specifics",
        "Set weekly sync cadence through Q3 launch"
    ]
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


def build_brief(data: dict) -> dict:
    prompt = f"""Return JSON only.
Create a CSM handoff brief from the sales context below.

Context:
{json.dumps(data, indent=2)}

Return keys: account_overview, customer_goals (list), pain_points (list), commitments_made (list), objections_handled (list), key_stakeholders (list of objects with name/title/role), urgency_timeline, watchouts (list), suggested_first_call_agenda (list)."""
    raw = call_llm(prompt)
    for marker in ["```json", "```"]:
        if marker in raw:
            raw = raw.split(marker)[1].split("```")[0]
            break
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"account_overview": "Parse error", "parse_error": True, "raw": raw[:500]}


def main():
    data = load_sample_data()
    account_name = data.get("account", {}).get("name", "Acme Corp")
    print(f"Invisible Handoff — {account_name}\n")

    if LIVE_MODE and has_api_key():
        print(f"[LIVE] API key found — calling {get_provider()} with sample data...\n")
        result = build_brief(data)
    else:
        print("[MOCK] No API key — showing sample output.")
        print("       Set ANTHROPIC_API_KEY or OPENAI_API_KEY to call live LLM.\n")
        result = MOCK_OUTPUT

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
