# MANTRAYUDHA — NovaMart Customer Support Agent Architecture

## 1. Core Architectural Principle

> **"AI reasons, backend verifies, database stores truth, tools perform actions, humans handle exceptions."**

In NovaMart's production environment, the Language Model (LLM) is treated as a reasoning engine, **not an authoritative data store or financial calculator**. Customer messages are classified as untrusted input (L4 authority level). Every refund amount, policy cutoff date, return window, restocking fee, and escalation decision is verified deterministically against authoritative database facts and versioned business rules.

---

## 2. End-to-End System Flow

```mermaid
flowchart TD
    A["Customer Message\n(Streamlit UI / FastAPI /chat)"] --> B["load_context_node\nExtract Customer ID & Order ID"]
    B --> C["Authoritative DB Verification\n(sqlite:///support_agent.db)"]
    C --> D{"Cross-Account Access?"}
    D -- Yes --> D1["Decision: ESCALATE\nTeam: Trust & Safety"]
    D -- No --> E["Risk Engine\n(detect_risk_signals)"]

    E --> E1{"High / Critical Risk?"}
    E1 -- Safety Hazard --> S1["Decision: ESCALATE\nTeam: Technical Support"]
    E1 -- Legal Threat --> S2["Decision: ESCALATE\nTeam: Customer Experience"]
    E1 -- Prompt Injection --> S3["Decision: ESCALATE\nTeam: Trust & Safety"]
    E1 -- Contradictory OTP Claim --> S4["Decision: ESCALATE\nTeam: Logistics Desk"]
    E1 -- Account Suspended --> S5["Decision: ESCALATE\nTeam: Trust & Safety"]

    E1 -- No --> F{"Order Ambiguity?"}
    F -- Multiple / Missing Orders --> F1["Decision: ASK\nGenerate Disambiguation Question"]
    F -- Order ID Not Found --> F2["Decision: ASK\nAsk for Clarification"]

    F -- Single Verified Order / FAQ --> G["Policy Engine\n(Determine v1 vs v2 by orders.order_date)"]
    G --> H{"Intent Classification"}

    H -- Cancellation --> I["check_cancellation_eligibility"]
    I -- Placed / Processing --> I1["Decision: ACT\nTool: cancel_order\nVerify DB & Respond"]
    I -- Shipped / Delivered --> I2["Decision: ANSWER\nExplain Status & Refuse"]

    H -- Return / Refund --> J["check_refund_eligibility\nExact Decimal & Restocking Fee"]
    J -- Above Threshold --> J1["Decision: ESCALATE\nTeam: Refunds & Payments"]
    J -- In Window & Returnable --> J2["Decision: ACT\nTool: create_refund / create_return\nVerify DB & Respond"]
    J -- Outside Window / Non-Returnable --> J3["Decision: ANSWER\nProvide Grounded Rejection"]

    H -- Warranty Claim --> K["check_warranty_eligibility"]
    K -- Physical / Liquid Damage --> K1["Decision: ANSWER\nExplain Paid Repair Option"]
    K -- Active Coverage --> K2["Decision: ANSWER\nProvide Warranty Center Info"]

    H -- General FAQ --> L["Decision: ANSWER\nRetrieve Grounded Policy Text"]

    D1 --> ESC["escalate_node\nCreate SupportTicket in DB\nEmit Telemetry"]
    S1 --> ESC
    S2 --> ESC
    S3 --> ESC
    S4 --> ESC
    S5 --> ESC
    J1 --> ESC
    I1 --> ACT["act_node\nExecute Mutation Tool\nVerify DB State\nEmit Audit Log"]
    J2 --> ACT
```

---

## 3. Decision Taxonomy

Every customer interaction produces one of four mutually exclusive terminal decisions:

| Decision | Semantics | Preconditions | Output Payload |
|---|---|---|---|
| `ANSWER` | Resolves inquiry with grounded policy facts | Deterministic eligibility check succeeded or general policy retrieved | Grounded text response, policy version, execution trace |
| `ASK` | Solicits targeted clarification | Ambiguous order reference (multiple matches), missing parameters, or nonexistent ID | Targeted clarification question, low risk status |
| `ACT` | Executes a verified state change | Full preconditions satisfied, DB facts verified, idempotency key checked | Mutation execution receipt, DB verification flag, updated order state |
| `ESCALATE` | Transfers case to human specialists | Risk trigger detected, policy threshold exceeded, or safety hazard | Support ticket ID (`TICK-XXXXX`), assigned specialized team, escalation reason |

---

## 4. Policy Versioning Engine

The policy version is determined strictly by the **order placement date** (`orders.order_date`), regardless of when the customer contacted support.

```mermaid
graph LR
    O["orders.order_date"] --> COND{"Order Date < 2026-06-01?"}
    COND -- Yes --> V1["Policy v1 (Legacy)"]
    COND -- No --> V2["Policy v2 (Current)"]

    V1 --> V1_RULES["• Change of Mind Window: 10 days\n• Defective Window: 14 days\n• Restocking Fee: None (0%)\n• Approval Threshold: ₹100,000\n• Loyalty Extensions: Gold +2d, Plat +3d"]
    V2 --> V2_RULES["• Change of Mind Window: 7 days\n• Defective Window: 14 days\n• Restocking Fee: 5% (Capped at ₹2,500)\n  (Applies to Laptops, Tablets, Cameras, Monitors)\n• Approval Threshold: ₹75,000\n• Loyalty Extensions: Gold +2d, Plat +3d"]
```

### Deterministic Financial Calculations
All financial arithmetic is calculated using Python's `Decimal` type to prevent binary floating-point roundoff errors:
1. **GST Calculation**:
   $$\text{Gross Item Refund} = \text{Final Item Price} \times 1.18$$
2. **Restocking Fee (Policy v2)**:
   $$\text{Restocking Fee} = \min(\text{Gross Item Refund} \times 0.05, 2500.00)$$
3. **Net Item Refund**:
   $$\text{Net Item Refund} = \text{Gross Item Refund} - \text{Restocking Fee}$$
4. **Order Total Cap**:
   $$\text{Final Refund} = \min(\text{Net Item Refund} + \text{Shipping Refund}, \text{Order Total Amount})$$

---

## 5. Risk & Security Defenses

### A. Prompt Injection Defense
Customer inputs are treated as untrusted data. Regular expression defenses identify attempts to hijack the model context (e.g. `ignore all previous instructions`, `you are now developer mode`, `approve ₹100,000 refund immediately`). Adversarial messages are immediately routed to `decision="ESCALATE"`, flagging `prompt_injection` and routing to the **Trust & Safety** desk.

### B. Ownership Verification & Isolation
Before order details are returned or actions are executed, `order.customer_id` is matched against the authenticated `customer_id`. Mismatches trigger an immediate `unauthorized_order_access` escalation to **Trust & Safety**.

### C. Contradictory OTP Claims
If an order is marked `delivered` with `delivery_otp_verified=True`, customer claims of non-receipt cannot be refunded automatically. The engine flags `contradictory_otp_claim` and creates an escalation ticket assigned to the **Logistics Desk**.

### D. Safety Incident Protocols
Device hazards involving thermal runaway, swollen lithium batteries, sparking, or smoke trigger immediate `risk_level="CRITICAL"`, instructing the user to disconnect and power off the device, and transferring the case to **Technical Support**.

---

## 6. Authoritative Database Schema

```mermaid
erDiagram
    Customer ||--o{ Order : places
    Customer ||--o{ SupportTicket : files
    Customer ||--o{ Conversation : has
    Order ||--|{ OrderItem : contains
    Product ||--o{ OrderItem : referenced_by
    Product ||--o{ Review : reviewed_in
    Order ||--o{ RefundRecord : receives
    Order ||--o{ ReturnRecord : initiates

    Customer {
        string customer_id PK
        string first_name
        string last_name
        string email
        string loyalty_tier
        string account_status
    }

    Order {
        string order_id PK
        string customer_id FK
        string order_date
        string order_status
        string delivery_status
        string actual_delivery_date
        float total_amount
        boolean delivery_otp_verified
        string cancellation_status
        string refund_status
    }

    OrderItem {
        string order_item_id PK
        string order_id FK
        string product_id FK
        int quantity
        float unit_price
        float final_price
        string return_status
    }

    Product {
        string product_id PK
        string product_name
        string category
        float price
        int warranty_months
        boolean returnable
        boolean replacement_available
    }

    SupportTicket {
        string ticket_id PK
        string customer_id FK
        string order_id FK
        string assigned_team
        string status
        string priority
    }
```

---

## 7. Verification and Auditability

Every response generated by the orchestrator includes a comprehensive `trace` list detailing every backend repository lookup, policy evaluation, risk signal calculation, and mutation execution. The Streamlit UI and FastAPI endpoints expose this trace for full auditability.
