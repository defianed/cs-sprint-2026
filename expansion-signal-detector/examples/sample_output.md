# Expansion Signal Detector — Sample Output

**Account:** Acme Corp | **CSM:** Sarah Johnson | **ARR:** $58K | **Confidence:** 83%

---

## Slack Message (sent to CSM)

```
📈 Expansion Signal Detected — Acme Corp

Confidence: 83% ready to expand

Buying Signals:
• Ben mentioned rolling platform out to sales team in Q3 (unprompted)
• At 95/100 seat capacity — organically approaching plan limits
• Champion said "this has transformed how our RevOps team works"
• Proactively asked about pricing for adding seats — not prompted by CSM
• API calls up 40% MoM — deep integration, switching cost is high

Blockers:
• Q3 budget cycle — CFO Chloe Park needs to approve anything over $25K
• CFO is ROI-focused — needs data before sign-off
• Resolve open CRM integration ticket first

Timing: Prepare ROI one-pager in 2 weeks, expansion call in late April when Q3 budget opens

Next Steps:
1. Escalate open CRM ticket — close before expansion conversation
2. Build ROI one-pager with Hana's time-savings data for CFO audience
3. Prepare custom Business 150 quote with per-seat comparison
4. Schedule dedicated expansion call — NOT attached to regular check-in
5. Ask Ben to pre-sell to Chloe before the formal conversation

CSM: Sarah Johnson
```

---

## Analysis JSON

```json
{
  "expansion_ready": true,
  "confidence": 0.83,
  "buying_signals": [
    "Ben mentioned rolling platform out to sales team in Q3 (unprompted)",
    "At 95/100 seat capacity — organically approaching plan limits",
    "Champion said 'this has transformed how our RevOps team works'",
    "Proactively asked about pricing for adding seats",
    "API calls up 40% MoM — deep product integration signals stickiness"
  ],
  "blockers": [
    "Budget cycle resets Q3 — CFO Chloe Park is the approver",
    "CFO is ROI-focused — needs data before sign-off",
    "Open CRM integration ticket should be resolved first"
  ],
  "recommended_timing": "Prepare ROI one-pager in 2 weeks, schedule expansion call for late April once Q3 budget opens",
  "next_steps": [
    "Escalate open CRM integration ticket — resolve before expansion conversation",
    "Build ROI one-pager with Hana's time-savings data for CFO audience",
    "Prepare custom Business 150 quote with per-seat comparison",
    "Schedule dedicated expansion call — do not attach to regular check-in",
    "Ask Ben to pre-sell internally to Chloe before formal call"
  ],
  "rationale": "Acme Corp is organically growing into expansion: near plan limits, API usage accelerating, VP Sales proactively raised expansion pricing. Friction is budget timing and CFO ROI story — both solvable in 3-4 weeks."
}
```
