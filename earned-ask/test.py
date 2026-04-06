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
    "should_ask": True,
    "reason": "Acme Corp went live 5 days ahead of schedule, hit 96% seat adoption in month one, and Priya submitted a 9 NPS and told the CSM unprompted she'd recommend the product. This is a genuine earned ask — not a hope ask.",
    "subject_line": "Quick favour — would mean a lot",
    "email_body": "Hi Priya,\n\nWatching your team go live ahead of schedule last month was one of those moments that reminds me why I love this work. 24 of 25 seats active in month one is genuinely rare.\n\nIf you've got 2 minutes, would you mind leaving us a short review on G2? Even a sentence or two about what's worked would make a real difference for us.\n\n[G2 Review Link]\n\nNo pressure at all — and thank you for being such a great partner through onboarding.\n\nSarah",
    "csm_notes": "This is an earned ask. Send it. Priya already told you she'd recommend the product — you're just making it easy for her to do that publicly. Send today while the NPS is warm. She also mentioned two referrals in today's call — follow up on those separately."
}


def load_sample_data() -> dict:
    data = {}
    for filename in ["account.json", "transcript.json"]:
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


def build_review_request(data: dict) -> dict:
    prompt = f"""Return JSON only.
Given the account context below, decide if a review request is earned and draft a customer-facing email.

Context:
{json.dumps(data, indent=2)}

Return keys: should_ask (bool), reason, subject_line, email_body, csm_notes."""
    raw = call_llm(prompt)
    for marker in ["```json", "```"]:
        if marker in raw:
            raw = raw.split(marker)[1].split("```")[0]
            break
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"should_ask": False, "reason": "Parse error", "raw": raw[:500]}


def main():
    data = load_sample_data()
    account_name = data.get("account", {}).get("name", "Acme Corp")
    print(f"Earned Ask — {account_name}\n")

    if LIVE_MODE and has_api_key():
        print(f"[LIVE] API key found — calling {get_provider()} with sample data...\n")
        result = build_review_request(data)
    else:
        print("[MOCK] No API key — showing sample output.")
        print("       Set ANTHROPIC_API_KEY or OPENAI_API_KEY to call live LLM.\n")
        result = MOCK_OUTPUT

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
