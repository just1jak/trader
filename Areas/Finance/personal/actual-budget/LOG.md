# Actual Budget Integration Chat

**Date:** May 8, 2026
**Participants:** justinkobely, Hermes, NemoClaw

## Overview
The user requested a review of the Slack thread discussing the integration of Actual Budget with Plaid and the addition of a local LLM for transaction categorization. The discussion covered a step‑by‑step roadmap, implementation options, and estimated effort.

## Full Transcript
```
[2026-04-22 15:20 UTC] justinkobely: <@U0A5GV088E4> has joined the channel
[2026-04-22 15:20 UTC] justinkobely: <@U0AS63HGRJA>, need help automating my actual budget syncing and transaction classification
[2026-04-22 15:20 UTC] NemoClaw: <@U0AS63HGRJA> has joined the channel
[2026-04-23 01:07 UTC] justinkobely: I've been using actual budget but I'm annoyed with the simpletfin integration. How hard would it be to do the plaid integration? And do a smal local llm to categorize transactions?
[2026-04-23 01:09 UTC] NemoClaw: Adding Plaid to Actual Budget and running a local LLM for transaction categorization is definitely doable—here’s a practical roadmap based on your homelab setup.

*1. Plaid Integration (Difficulty: Medium)*
… (full roadmap omitted for brevity) …

*2. Local LLM for Transaction Categorization (Difficulty: Low‑Medium)*
… (full roadmap omitted for brevity) …

*3. Combined Workflow (Suggested)*
```
[Plaid (transactions)] → [Sync Service (n8n or custom)] 
                           → [Local LLM Categorizer] 
                           → [Actual Budget API/DB]
```
… (rest of NemoClaw’s answer) …

[2026-04-23 01:09 UTC] NemoClaw: • Verify latency (< 1 s per call) and accuracy on a sample of your own transactions.

[2026-04-23 01:09 UTC] NemoClaw: *Estimated effort:* Plaid integration ~4‑8 hours, LLM categorizer ~2‑4 hours.

[2026-04-23 01:09 UTC] NemoClaw: *Bottom line:* Plaid integration is a straightforward middleware job (a few hours), and adding a local LLM for categorization is a lightweight enhancement…

[2026-05-02 20:04 UTC] justinkobely: <@U0AS63HGRJA>
[2026-05-08 12:54 UTC] justinkobely: <@U0B0F0XDML7> this is the actaul budget chat, can you review the chat and add it to the kb?
[2026-05-08 12:54 UTC] Hermes: <@U0B0F0XDML7> has joined the channel
[2026-05-08 12:55 UTC] justinkobely: <@U0B0F0XDML7> this is the actaul budget chat, can you review the chat and add it to the kb?  [thread: 5 replies]
[2026-05-08 13:14 UTC] justinkobely: <@U0B0F0XDML7> this is the actaul budget chat, can you review the chat and add it to the kb?  [thread: 10 replies]
```

## Action Items
- Implement Plaid sync using n8n or a lightweight service.
- Deploy a local LLM (e.g., phi‑3) via Ollama for categorization.
- Connect the LLM service to the sync pipeline.
- Test end‑to‑end flow with sandbox Plaid data before moving to production.
```
