"""Churn Risk Summarizer — tool-agnostic workflow template.
Deploy with: modal deploy main.py
"""

import json
import os
from datetime import datetime

import modal

app = modal.App("churn-risk-summarizer")
image = modal.Image.debian_slim().pip_install("anthropic>=0.20.0", "openai>=1.0.0", "slack-sdk>=3.20.0")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def call_llm(prompt: str) -> str:
    if _env("LLM_PROVIDER", "anthropic") == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=_env("OPENAI_API_KEY"))
        return client.responses.create(model=_env("OPENAI_MODEL", "gpt-4.1-mini"), input=prompt).output_text
    import anthropic
    client = anthropic.Anthropic(api_key=_env("ANTHROPIC_API_KEY"))
    resp = client.messages.create(model=_env("ANTHROPIC_MODEL", "claude-opus-4-6"), max_tokens=4096, messages=[{"role": "user", "content": prompt}])
    return resp.content[0].text


def build_risk_story(data: dict) -> dict:
    prompt = f"""Return JSON only.
Create a plain-language churn risk story from the account context below.
Do not output a numeric health score only; explain the situation as a narrative.

Context:\n{json.dumps(data, indent=2)}

Return keys:
summary, risk_story, primary_risks, stabilizers, next_call_focus, urgency.
"""
    raw = call_llm(prompt)
    try:
        return json.loads(raw)
    except Exception:
        return {"summary": raw, "risk_story": raw, "primary_risks": [], "stabilizers": [], "next_call_focus": [], "urgency": "unknown"}


def notify_slack(slack_user_id: str, account_name: str, result: dict) -> None:
    if not _env("SLACK_BOT_TOKEN") or not slack_user_id:
        return
    from slack_sdk import WebClient
    client = WebClient(token=_env("SLACK_BOT_TOKEN"))
    channel = client.conversations_open(users=[slack_user_id])["channel"]["id"]
    client.chat_postMessage(channel=channel, text=f"*Churn Risk Summarizer: {account_name}*\n\n{result.get('summary','')}\n\n*Risk story*\n{result.get('risk_story','')}")


@app.function(image=image, secrets=[modal.Secret.from_name("churn-risk-summarizer-secrets")])
@modal.fastapi_endpoint(method="POST")
def webhook(data: dict) -> dict:
    account_name = data.get("account_name") or data.get("account_id") or "Unknown Account"
    result = build_risk_story(data)
    notify_slack(data.get("csm_slack_user_id", ""), account_name, result)
    payload = {"status": "ok", "workflow": "churn-risk-summarizer", "account_name": account_name, "processed_at": datetime.utcnow().isoformat(), "result": result}
    print(json.dumps(payload))
    return payload


@app.local_entrypoint()
def main():
    out = webhook.local({
        "account_id": _env("ACCOUNT_ID"),
        "account_name": _env("ACCOUNT_NAME"),
        "recent_activity": _env("RECENT_ACTIVITY"),
        "support_summary": _env("SUPPORT_SUMMARY"),
        "engagement_summary": _env("ENGAGEMENT_SUMMARY"),
        "csm_slack_user_id": _env("CSM_SLACK_USER_ID"),
    })
    print(json.dumps(out, indent=2))
