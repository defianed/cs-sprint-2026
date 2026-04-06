"""Earned Ask — tool-agnostic workflow template.
Deploy with: modal deploy main.py
"""

import json
import os
from datetime import datetime

import modal

app = modal.App("earned-ask")
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


def build_review_request(data: dict) -> dict:
    prompt = f"""Return JSON only.
Given the milestone context below, decide if a review request is earned and draft a customer-facing email.

Context:\n{json.dumps(data, indent=2)}

Return keys:
should_ask, reason, subject_line, email_body, csm_notes.
"""
    raw = call_llm(prompt)
    try:
        return json.loads(raw)
    except Exception:
        return {"should_ask": False, "reason": raw, "subject_line": "", "email_body": raw, "csm_notes": "Manual review needed"}


def notify_slack(slack_user_id: str, account_name: str, result: dict) -> None:
    if not _env("SLACK_BOT_TOKEN") or not slack_user_id:
        return
    from slack_sdk import WebClient
    client = WebClient(token=_env("SLACK_BOT_TOKEN"))
    channel = client.conversations_open(users=[slack_user_id])["channel"]["id"]
    text = (
        f"*Earned Ask: {account_name}*\n\n"
        f"Should ask: {result.get('should_ask')}\n"
        f"Reason: {result.get('reason','')}\n\n"
        f"*Subject*\n{result.get('subject_line','')}\n\n"
        f"*Draft*\n{result.get('email_body','')}"
    )
    client.chat_postMessage(channel=channel, text=text)


@app.function(image=image, secrets=[modal.Secret.from_name("earned-ask-secrets")])
@modal.fastapi_endpoint(method="POST")
def webhook(data: dict) -> dict:
    account_name = data.get("account_name") or data.get("account_id") or "Unknown Account"
    result = build_review_request(data)
    notify_slack(data.get("csm_slack_user_id", ""), account_name, result)
    payload = {"status": "ok", "workflow": "earned-ask", "account_name": account_name, "processed_at": datetime.utcnow().isoformat(), "result": result}
    print(json.dumps(payload))
    return payload


@app.local_entrypoint()
def main():
    out = webhook.local({
        "account_id": _env("ACCOUNT_ID"),
        "account_name": _env("ACCOUNT_NAME"),
        "interaction_summary": _env("INTERACTION_SUMMARY"),
        "milestone_achieved": _env("MILESTONE_ACHIEVED"),
        "sentiment_summary": _env("SENTIMENT_SUMMARY"),
        "csm_slack_user_id": _env("CSM_SLACK_USER_ID"),
    })
    print(json.dumps(out, indent=2))
