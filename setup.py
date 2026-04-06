#!/usr/bin/env python3
"""
cs-webinar setup wizard
Run this once after cloning the repo.
It will configure all 5 workflows for your environment.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).parent

WORKFLOWS = [
    "churn-risk-summarizer",
    "earned-ask",
    "expansion-signal-detector",
    "invisible-handoff",
    "trust-radar",
]

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def header(text):
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}\n")

def success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def warn(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def error(text):
    print(f"{RED}❌ {text}{RESET}")

def ask(prompt, default=None, secret=False):
    if default:
        full_prompt = f"  {prompt} [{default}]: "
    else:
        full_prompt = f"  {prompt}: "

    if secret:
        import getpass
        value = getpass.getpass(full_prompt)
    else:
        value = input(full_prompt).strip()

    return value if value else default

def ask_choice(prompt, options, default=None):
    print(f"\n  {prompt}")
    for i, (key, label) in enumerate(options, 1):
        marker = " (default)" if key == default else ""
        print(f"    {i}. {label}{marker}")
    while True:
        raw = input(f"\n  Enter number [{default}]: ").strip()
        if not raw and default:
            return default
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
        except ValueError:
            pass
        print("  Please enter a valid number.")

def test_workflow(workflow):
    path = ROOT / workflow / "test.py"
    if not path.exists():
        return False, "test.py not found"
    result = subprocess.run(
        [sys.executable, str(path)],
        capture_output=True, text=True, cwd=ROOT / workflow
    )
    return result.returncode == 0, result.stdout[-500:] if result.stdout else result.stderr[-200:]


def main():
    print(f"\n{BOLD}Welcome to the Agentic CS Workflow Setup{RESET}")
    print("This wizard will configure all 5 workflows for your environment.")
    print("It takes about 5 minutes.\n")

    env = {}
    configs = {wf: {} for wf in WORKFLOWS}

    # ─────────────────────────────────────────────
    # STEP 0 — DATA SOURCE
    # ─────────────────────────────────────────────
    header("Step 0 — Data Source")
    print("  These workflows need CS data to run against.\n")
    print(f"  {BOLD}Option 1 — Live demo data (recommended){RESET}")
    print("  We host 10 realistic dummy companies — full CRM records, call")
    print("  transcripts, helpdesk tickets, billing data, and usage stats.")
    print("  Use your sprint API key and the workflows connect instantly.\n")
    print(f"  {BOLD}Option 2 — Your own tools{RESET}")
    print("  Connect your real Salesforce, Gong, Zendesk etc.")
    print("  Takes 5–10 minutes to configure.\n")

    data_source = ask_choice(
        "Which would you like to start with?",
        [
            ("demo_stack", "Live demo data  (instant — recommended for the webinar)"),
            ("own",        "My own tools   (Salesforce, Gong, Zendesk etc.)"),
        ],
        default="demo_stack"
    )

    use_demo_stack = (data_source == "demo_stack")

    if use_demo_stack:
        print()
        demo_key = ask("Enter your demo stack API key (sprint-XXXXXX-XXXXXX)", secret=False)
        if demo_key and demo_key.startswith("sprint-"):
            env["DEMO_STACK_API_KEY"] = demo_key
            for wf in WORKFLOWS:
                configs[wf]["data_source"] = "demo_stack"
                configs[wf]["crm_provider"] = "demo_stack"
                configs[wf]["transcript_provider"] = "demo_stack"
                configs[wf]["support_provider"] = "demo_stack"
            success("Demo stack key saved. All workflows will use live demo data.")
        else:
            warn("Key not recognised — expected format: sprint-XXXXXX-XXXXXX")
            warn("Continuing without demo stack — falling back to sample data mode.")
            use_demo_stack = False

    # ─────────────────────────────────────────────
    # STEP 1 — API KEY
    # ─────────────────────────────────────────────
    header("Step 1 — LLM API Key")
    print("  These workflows use Claude (Anthropic) or GPT (OpenAI) to analyse your CS data.")
    print("  Get your key from: https://console.anthropic.com  or  https://platform.openai.com\n")

    llm_provider = ask_choice(
        "Which LLM do you want to use?",
        [("anthropic", "Anthropic — Claude (recommended)"), ("openai", "OpenAI — GPT")],
        default="anthropic"
    )

    if llm_provider == "anthropic":
        key = ask("Anthropic API key (starts with sk-ant-)", secret=True)
        if key:
            env["ANTHROPIC_API_KEY"] = key
            env["ANTHROPIC_MODEL"] = "claude-opus-4-6"
            success("Anthropic key saved.")
        else:
            warn("No key entered — workflows will run in demo mode with sample data.")
    else:
        key = ask("OpenAI API key (starts with sk-proj-)", secret=True)
        if key:
            env["OPENAI_API_KEY"] = key
            env["OPENAI_MODEL"] = "gpt-4o"
            success("OpenAI key saved.")
        else:
            warn("No key entered — workflows will run in demo mode with sample data.")

    # ─────────────────────────────────────────────
    # STEP 2 — TEST IT
    # ─────────────────────────────────────────────
    header("Step 2 — Quick Test")
    print("  Let's make sure everything is working before we go further.")
    print("  Running churn-risk-summarizer with sample data...\n")

    # Write temp env so test.py can use it
    if env:
        _write_env(ROOT / ".env", env)

    ok, output = test_workflow("churn-risk-summarizer")
    if ok:
        success("Test passed! Here's a sample output:\n")
        print(f"  {CYAN}{'─' * 56}{RESET}")
        for line in output.strip().split("\n")[:20]:
            print(f"  {line}")
        print(f"  {CYAN}{'─' * 56}{RESET}\n")
    else:
        warn("Test ran but may have used demo mode (no API key). That's fine for now.")
        print(f"  Output: {output[:300]}\n")

    # ─────────────────────────────────────────────
    # STEP 3 — BUSINESS INFO
    # ─────────────────────────────────────────────
    header("Step 3 — About Your Business")
    print("  This personalises the workflow outputs for your team.\n")

    company_name = ask("Your company name", default="Acme Corp")
    csm_name = ask("Your name (CSM or CS leader running this)")
    product_name = ask("What product do you sell?")
    customer_type = ask("Who are your customers? (e.g. SaaS companies, retail brands)")

    for wf in WORKFLOWS:
        configs[wf]["account_name"] = company_name
        configs[wf]["csm_name"] = csm_name or "CS Team"
        configs[wf]["product_name"] = product_name or ""
        configs[wf]["customer_type"] = customer_type or ""

    # ─────────────────────────────────────────────
    # STEP 4 — TOOL STACK
    # ─────────────────────────────────────────────
    if use_demo_stack:
        header("Step 4 — Tool Stack (skipped)")
        print("  Using demo stack — no tool configuration needed.")
        print("  When you're ready to connect your real tools, re-run setup.py and choose 'My own tools'.\n")
    else:
        _configure_tool_stack(env, configs)

    _write_and_test(env, configs)


def _configure_tool_stack(env, configs):
    header("Step 4 — Your Tool Stack")
    print("  Tell us what tools you use. We'll connect the workflows automatically.")
    print("  Choose 'manual' if you don't use that category — you can always add it later.\n")

    # CRM
    crm = ask_choice(
        "CRM:",
        [
            ("manual", "I don't use one / paste data manually"),
            ("salesforce", "Salesforce"),
            ("hubspot", "HubSpot"),
        ],
        default="manual"
    )
    env["CRM_PROVIDER"] = crm
    for wf in WORKFLOWS:
        configs[wf]["crm_provider"] = crm

    if crm == "salesforce":
        env["SALESFORCE_INSTANCE_URL"] = ask("Salesforce instance URL (e.g. https://yourorg.my.salesforce.com)")
        env["SALESFORCE_ACCESS_TOKEN"] = ask("Salesforce access token", secret=True)
    elif crm == "hubspot":
        env["HUBSPOT_PRIVATE_APP_TOKEN"] = ask("HubSpot private app token", secret=True)

    # Call transcripts
    transcript = ask_choice(
        "Call recording / transcript tool:",
        [
            ("manual", "I don't use one / paste transcripts manually"),
            ("gong", "Gong"),
            ("fireflies", "Fireflies"),
            ("fathom", "Fathom"),
            ("zoom", "Zoom (cloud recordings)"),
        ],
        default="manual"
    )
    env["CALL_TRANSCRIPT_PROVIDER"] = transcript
    for wf in WORKFLOWS:
        configs[wf]["transcript_provider"] = transcript

    if transcript == "gong":
        env["GONG_ACCESS_KEY"] = ask("Gong access key")
        env["GONG_ACCESS_KEY_SECRET"] = ask("Gong access key secret", secret=True)
    elif transcript == "fireflies":
        env["FIREFLIES_API_KEY"] = ask("Fireflies API key", secret=True)
    elif transcript == "zoom":
        env["ZOOM_OAUTH_TOKEN"] = ask("Zoom OAuth token", secret=True)

    # Support
    support = ask_choice(
        "Customer support / ticketing tool:",
        [
            ("manual", "I don't use one / paste ticket data manually"),
            ("zendesk", "Zendesk"),
            ("intercom", "Intercom"),
        ],
        default="manual"
    )
    env["SUPPORT_PROVIDER"] = support
    for wf in WORKFLOWS:
        configs[wf]["support_provider"] = support

    if support == "zendesk":
        env["ZENDESK_SUBDOMAIN"] = ask("Zendesk subdomain (e.g. mycompany)")
        env["ZENDESK_EMAIL"] = ask("Zendesk email")
        env["ZENDESK_API_TOKEN"] = ask("Zendesk API token", secret=True)
    elif support == "intercom":
        env["INTERCOM_ACCESS_TOKEN"] = ask("Intercom access token", secret=True)

    # ─────────────────────────────────────────────
    # STEP 5 — OUTPUT / WHERE TO PUSH DATA
    # ─────────────────────────────────────────────
    header("Step 5 — Where Should Results Be Sent?")

    print("  Where do you want workflow results delivered?")
    print("  These workflows can push output anywhere you can receive a webhook or API call.")
    print()
    print("  Ideas:")
    print("    • Slack — post to #cs-alerts or DM the CSM directly")
    print("    • Notion — create a page per account automatically")
    print("    • Email — send a summary to the account owner")
    print("    • Your CRM — log as a note or activity on the account")
    print("    • Google Sheets — append a row per run")
    print("    • Webhook — POST to any tool (Zapier, Make, n8n, HubSpot, Salesforce)")
    print("    • Terminal only — just print the output, you handle the rest")
    print()
    print("  For now, we'll set up Slack (easiest to start) and/or Notion.")
    print("  You can always add other outputs later by editing the workflow code.")
    print()
    output_dest = ask_choice(
        "Set up now:",
        [
            ("slack", "Slack"),
            ("notion", "Notion"),
            ("both", "Both Slack and Notion"),
            ("terminal", "Skip for now — just print to terminal"),
        ],
        default="slack"
    )

    if output_dest in ("slack", "both"):
        print("\n  You need a Slack bot token and the channel to post to.")
        print("  Create a bot at https://api.slack.com/apps → Add 'chat:write' scope → Install to workspace\n")
        slack_token = ask("Slack bot token (starts with xoxb-)", secret=True)
        slack_channel = ask("Slack channel to post to (e.g. #cs-alerts)", default="#cs-alerts")
        csm_user_id = ask("Your Slack user ID (optional, for @mentions — find in your Slack profile)")
        if slack_token:
            env["SLACK_BOT_TOKEN"] = slack_token
        if slack_channel:
            for wf in WORKFLOWS:
                configs[wf]["slack_channel"] = slack_channel
        if csm_user_id:
            env["CSM_SLACK_USER_ID"] = csm_user_id

    if output_dest in ("notion", "both"):
        print("\n  You need a Notion integration token and a parent page ID.")
        print("  Create at https://www.notion.so/my-integrations\n")
        notion_key = ask("Notion integration token (starts with ntn_ or secret_)", secret=True)
        notion_page = ask("Notion parent page ID (from the page URL)")
        if notion_key:
            env["NOTION_API_KEY"] = notion_key
        if notion_page:
            env["NOTION_PARENT_PAGE_ID"] = notion_page

    for wf in WORKFLOWS:
        configs[wf]["output_destination"] = output_dest


def _write_and_test(env, configs):
    # ─────────────────────────────────────────────
    # WRITE FILES
    # ─────────────────────────────────────────────
    header("Writing Your Configuration")

    # Write root .env
    _write_env(ROOT / ".env", env)
    success(f".env written to repo root ({len(env)} variables)")

    # Write config.yaml for each workflow
    for wf in WORKFLOWS:
        _write_config(ROOT / wf / "config.yaml", configs[wf])
    success(f"config.yaml written for all 5 workflows")

    # ─────────────────────────────────────────────
    # FINAL TEST
    # ─────────────────────────────────────────────
    header("Final Check — Running All Workflows")

    results = {}
    for wf in WORKFLOWS:
        print(f"  Testing {wf}...", end=" ", flush=True)
        ok, out = test_workflow(wf)
        results[wf] = ok
        if ok:
            print(f"{GREEN}✅{RESET}")
        else:
            print(f"{YELLOW}⚠️  (check output){RESET}")

    print()
    all_ok = all(results.values())
    if all_ok:
        success("All 5 workflows are ready to go!\n")
    else:
        warn("Some workflows need attention — check the output above.\n")

    print(f"{BOLD}You're set up. Here's what to do next:{RESET}\n")
    print(f"  • Run any workflow locally:  {CYAN}python3 <workflow>/local.py{RESET}")
    print(f"  • See sample output first:   {CYAN}python3 <workflow>/test.py{RESET}")
    print(f"  • Deploy to cloud (Modal):   {CYAN}modal deploy <workflow>/execution/main.py{RESET}")
    print(f"\n  Your config is in {CYAN}.env{RESET} (secrets) and each workflow's {CYAN}config.yaml{RESET} (settings).")
    print(f"  To change settings later, edit those files directly.\n")


def _write_env(path, env_dict):
    lines = [
        "# cs-webinar — generated by setup.py",
        "# Edit this file to update your configuration\n",
    ]
    for k, v in env_dict.items():
        lines.append(f"{k}={v}")
    path.write_text("\n".join(lines) + "\n")


def _write_config(path, config_dict):
    lines = ["# Generated by setup.py — edit freely\n"]
    for k, v in config_dict.items():
        if isinstance(v, str):
            lines.append(f"{k}: {json.dumps(v)}")
        else:
            lines.append(f"{k}: {v}")
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Setup cancelled. Run python3 setup.py to start again.{RESET}\n")
        sys.exit(0)
