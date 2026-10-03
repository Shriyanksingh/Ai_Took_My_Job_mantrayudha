# 4-Minute Demo Script

## 0:00-0:30
Open the UI and show the Understand -> Verify -> Policy -> Decide flow.

## 0:30-1:00
Run a verified order-status query. Point out that the customer response is generated after database verification.

## 1:00-1:35
Run the ambiguous return case. Show that two matches produce ASK, not an arbitrary refund.

## 1:35-2:05
Run an above-threshold refund case. Show ESCALATE and the applicable policy version.

## 2:05-2:35
Run a prompt-injection case. Show the firewall detects the injection while the legitimate support request remains answerable.

## 2:35-3:10
Run the multi-intent delivery + refund + address case. Show dependency-aware handling.

## 3:10-3:45
Use Mutation mode to change v2 change-of-mind days from 7 to 8. Rerun the same case to show data-driven adaptation without source changes.

## 3:45-4:00
Show runtime metrics and the proof/evidence panel, then point judges to README, architecture, prompt strategy and test results.
