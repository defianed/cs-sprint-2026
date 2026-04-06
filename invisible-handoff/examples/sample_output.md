# Invisible Handoff — Sample Output

**Account:** Acme Corp | **CSM:** Sarah Johnson | **ARR:** $48K | **Closed:** 2026-03-20

---

## Slack Message (sent to incoming CSM)

```
📋 Handoff Brief Ready — Acme Corp ($48K ACV)

Deal closed 2026-03-20 by Jake Hoffman. Your account: Sarah Johnson.

Read this before your first call 👇

Company: 200-person fintech. Replacing 3 legacy tools with one platform.
Q3 launch (August 1) is a HARD deadline — their product team is building on the API.

Key people:
• Sarah Okonkwo (VP Eng) — your champion. She drove the whole eval. Day-to-day contact.
  Highly bought-in and already advocating internally.
• Mike Chen (CTO) — economic buyer. Skeptical. Been burned by vendor timelines before.
  DO NOT hedge on API GA date in his presence. He asked for everything in writing.
• James Liu (Senior DevOps) — will do the actual integration work.
  Was NOT in any demos. Get him into kickoff before April. He can be a blocker if ignored.

Commitments made (all in writing per Mike's request):
✅ API GA by May 15 — confirmed with product
✅ Marcus (onboarding engineer, ex-Stripe) assigned for 30 days
✅ Custom migration guide for Node.js + Postgres
✅ SOC 2 Type II + pen test results sent with contract
✅ 50/50 milestone payments — 2nd half tied to API GA confirmation
✅ 30-day extension if API slips past May 15

First call agenda (suggested):
1. Introduce yourself — confirm you've read Jake's deal summary
2. Introduce Marcus — confirm his 30-day exclusive availability
3. Confirm API GA date (May 15) on the call — have it in writing
4. Get James on the kickoff invite — ask Sarah to facilitate
5. Walk migration guide outline together
6. Set weekly sync through Q3 launch

Full brief below ↓

CSM: Sarah Johnson
```

---

## Analysis JSON

```json
{
  "account_overview": "Acme Corp is a 200-person fintech that closed a $48K ACV deal on 2026-03-20. Sarah Okonkwo (VP Engineering) is the champion. Mike Chen (CTO) is the economic buyer and openly skeptical — been burned by vendor promises before. James Liu (Senior DevOps) will own the integration but was not in any demos.",
  "customer_goals": [
    "Replace fragmented 3-tool toolchain with single platform by Q3",
    "Reduce time-to-integrate from 3 weeks to under 5 days",
    "Hit Q3 product launch deadline (August 1) with API layer in place"
  ],
  "pain_points": [
    "Previous vendors had good uptime but terrible support SLAs — left them stranded",
    "Engineering team is stretched — migration overhead is costly",
    "CTO skeptical of vendor commitments after being burned before"
  ],
  "commitments_made": [
    "API GA by May 15 — confirmed with product team, not estimated",
    "Marcus (senior onboarding engineer, ex-Stripe) assigned for 30 days",
    "Custom migration guide for Node.js + Postgres stack",
    "SOC 2 Type II report and pen test results sent with contract",
    "Milestone payments: 50% kickoff, 50% at API GA confirmation",
    "30-day contract extension if API slips past May 15"
  ],
  "objections_handled": [
    "Security: SOC 2 Type II certified + pen test report provided",
    "Migration risk: Marcus has prior Node.js migration experience (Stripe)",
    "Reliability: milestone payments tied to delivery, not time",
    "Competitors: differentiated vs DataBridge and NovaSuite on 3 technical points"
  ],
  "key_stakeholders": [
    {"name": "Sarah Okonkwo", "title": "VP Engineering", "role": "Champion — drove evaluation, day-to-day contact, highly bought-in"},
    {"name": "Mike Chen", "title": "CTO", "role": "Economic buyer — skeptical, wants written record of all commitments, will be watching closely"},
    {"name": "James Liu", "title": "Senior DevOps", "role": "Will own integration — NOT in any demos, get him into kickoff ASAP"}
  ],
  "urgency_timeline": "Q3 launch is August 1 (hard deadline). API GA is May 15. First CSM call within 24 hours of deal close (March 20). Kickoff with James must happen before April.",
  "watchouts": [
    "Mike's skepticism is real and earned — do not hedge or over-promise in his presence",
    "API GA (May 15) is tight — reconfirm with product before first call, never guess",
    "James was not in demos — he will have concerns, do not assume Sarah speaks for him",
    "Mike explicitly asked for written record of all commitments — send deal summary today"
  ],
  "suggested_first_call_agenda": [
    "Introduce yourself and confirm you've read Jake's deal summary",
    "Introduce Marcus — confirm his 30-day exclusive availability",
    "Confirm API GA date (May 15) out loud — ask Mike to confirm he has it in writing",
    "Get James added to kickoff — ask Sarah to facilitate the intro",
    "Walk through migration guide outline — get James's input on Node.js specifics",
    "Set weekly sync cadence through Q3 launch"
  ]
}
```
