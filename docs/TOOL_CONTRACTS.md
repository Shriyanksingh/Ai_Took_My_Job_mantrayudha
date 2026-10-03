# Tool Contracts

## Read tools

`get_customer(customer_id)`

Returns the authenticated customer record.

`get_order(order_id)`

Returns the order and delivery/payment state. Ownership is checked in the decision engine.

`get_product(product_id)`

Returns catalog facts. Product markdown provides additional technical specifications.

`get_conversations(customer_id)`

Returns prior conversations for continuity.

## Decision/calculation tools

`check_refund_eligibility(...)`

Applies the versioned policy and records the reasons for eligibility or rejection.

`calculate_refund(...)`

Calculates item refund + GST, shipping eligibility, restocking fee and order cap.

## Write tools

`create_return(...)`

Creates an idempotent return request.

`create_refund(...)`

Creates an idempotent refund record; amount must already be verified.

`create_support_ticket(...)`

Creates an idempotent support case.

`escalate_to_human(...)`

Creates an idempotent human hand-off record with team and priority.

## Proof-carrying action rule

Writes require a dictionary of verified evidence. The action guard fails closed if required evidence is missing.
