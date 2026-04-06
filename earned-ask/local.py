#!/usr/bin/env python3
"""
Earned Ask — local runner (no Modal required)
Run: python3 local.py

Modes:
  No API key  — loads sample_data/, prints mock output
  With API key — loads sample_data/, calls real LLM

Config: edit config.yaml (no secrets there)
Secrets: copy .env.example to .env and add your API key
"""
import os, json
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

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

WORKFLOW_DIR = Path(__file__).parent

MOCK_OUTPUT = {
    "should_ask": True,
    "reason": "Acme Corp went live 5 days ahead of schedule, hit 96% seat adoption in month one, and Priya submitted a 9 NPS and told the CSM unprompted she'd recommend the product. This is a genuine earned ask — not a hope ask.",
    "subject_line": "Quick favour — would mean a lot",
    "email_body": "Hi Priya,\n\nWatching your team go live ahead of schedule last month was one of those moments that reminds me why I love this work. 24 of 25 seats active in month one is genuinely rare.\n\nIf you've got 2 minutes, would you mind leaving us a short review on G2? Even a sentence or two about what's worked would make a real difference for us.\n\n[G2 Review Link]\n\nNo pressure at all — and thank you for being such a great partner through onboarding.\n\nSarah",
    "csm_notes": "This is an earned ask. Send it. Priya already told you she'd recommend the product — you're just making it easy for her to do that publicly. She also mentioned two referrals in today's call — follow up on those separately."
}


def load_config() -> dict:
    config_path = WORKFLOW_DIR / "config.yaml"
    if _YAML_AVAILABLE and config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def has_api_key() -> bool:
    return bool((os.getenv("ANTHROPIC_API_KEY") or "").strip()) or bool((os.getenv("OPENAI_API_KEY") or "").strip())


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
    try:
        raw = call_llm(prompt)
    except Exception as e:
        print(f"Warning: LLM call failed: {e}")
        return None
    for marker in ["```json", "```"]:
        if marker in raw:
            raw = raw.split(marker)[1].split("```")[0]
            break
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"should_ask": False, "reason": "Parse error", "raw": raw[:500]}


def load_sample_data() -> dict:
    data = {}
    for filename in ["account.json", "transcript.json", "notes.json"]:
        path = WORKFLOW_DIR / "sample_data" / filename
        if path.exists():
            key = filename.replace(".json", "")
            try:
                data[key] = json.loads(path.read_text())
            except Exception:
                pass
    return data


def main():
    config = load_config()
    account_name = config.get("account_name", "Acme Corp")
    csm_name = config.get("csm_name", "Sarah Johnson")

    print("=" * 60)
    print("  Earned Ask")
    print("=" * 60)
    print(f"  Account : {account_name}")
    print(f"  CSM     : {csm_name}")

    data = load_sample_data()
    if "account" in data:
        data["account"]["name"] = account_name

    if has_api_key():
        print(f"\n[LIVE] Calling {get_provider()} with sample data...\n")
        result = build_review_request(data)
        if result is None:
            print("LLM call failed — falling back to mock output.\n")
            result = MOCK_OUTPUT
    else:
        print("\n[MOCK] No API key found — showing sample output.")
        print("       Add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env to use live LLM.\n")
        result = MOCK_OUTPUT

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
