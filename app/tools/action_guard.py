from __future__ import annotations
from typing import Any, Dict, List

class ActionGuard:
    """Refuses write actions unless required evidence is explicitly present."""
    REQUIRED = {
        'create_refund': ['customer_verified','order_owned','eligibility_verified','amount_verified','threshold_verified','destination_verified','no_escalation_trigger'],
        'create_return': ['customer_verified','order_owned','eligibility_verified','no_escalation_trigger'],
        'update_address': ['customer_verified','order_owned','shipment_not_started','new_address_verified'],
        'add_wallet_credit': ['customer_verified','delay_verified','credit_within_cap'],
    }

    def validate(self, action: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        required = self.REQUIRED.get(action, ['customer_verified','order_owned'])
        missing = [x for x in required if not evidence.get(x)]
        proof = {'action': action, 'required_evidence': required, 'missing_evidence': missing, 'permitted': not missing, 'proof_id': f'PROOF-{id(evidence):x}'}
        if missing:
            raise PermissionError('Action blocked: missing proof - ' + ', '.join(missing))
        return proof
