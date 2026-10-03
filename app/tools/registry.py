from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class ToolRegistry:
    """Transactional tool facade. Read calls use DataStore; write calls are recorded in runtime/state.json."""
    def __init__(self, store, state_file: Path, policy_engine):
        self.store = store
        self.state_file = state_file
        self.policy_engine = policy_engine
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()
        self.trace = []

    def _load_state(self):
        if not self.state_file.exists():
            return {'refunds': [], 'returns': [], 'tickets': [], 'escalations': [], 'address_updates': [], 'wallet_credits': [], 'action_log': []}
        try:
            return json.loads(self.state_file.read_text(encoding='utf-8'))
        except Exception:
            return {'refunds': [], 'returns': [], 'tickets': [], 'escalations': [], 'address_updates': [], 'wallet_credits': [], 'action_log': []}

    def _save(self):
        self.state_file.write_text(json.dumps(self.state, indent=2, default=str), encoding='utf-8')

    def _record(self, name: str, params: Dict[str, Any], result: Any):
        self.trace.append({'type':'tool','name':name,'parameters':params,'success':True,'summary':_summary(name, result)})
        return result

    def get_customer(self, customer_id: str):
        result = self.store.get_customer(customer_id)
        return self._record('get_customer', {'customer_id': customer_id}, result)

    def get_order(self, order_id: str):
        result = self.store.get_order(order_id)
        return self._record('get_order', {'order_id': order_id}, result)

    def get_product(self, product_id: str):
        result = self.store.get_product(product_id)
        return self._record('get_product', {'product_id': product_id}, result)

    def get_conversations(self, customer_id: str):
        result = self.store.customer_conversations(customer_id)
        return self._record('get_conversations', {'customer_id': customer_id}, {'count': len(result), 'conversations': result[:5]})

    def check_refund_eligibility(self, **kwargs):
        result = self.policy_engine.check_refund_eligibility(**kwargs)
        return self._record('check_refund_eligibility', kwargs, result)

    def calculate_refund(self, **kwargs):
        result = self.policy_engine.calculate_refund(**kwargs)
        return self._record('calculate_refund', kwargs, result)

    def _idempotent(self, key: str, collection: str):
        for r in self.state.get(collection, []):
            if r.get('idempotency_key') == key:
                return r
        return None

    def create_return(self, customer_id: str, order_id: str, item_id: Optional[str], reason: str):
        key = f'return:{order_id}:{item_id}:{reason.lower().strip()}'
        existing = self._idempotent(key, 'returns')
        if existing:
            return self._record('create_return', {'order_id':order_id,'item_id':item_id,'reason':reason}, existing)
        row = {'return_id': 'RET-' + uuid.uuid4().hex[:10].upper(), 'customer_id': customer_id, 'order_id': order_id, 'item_id': item_id, 'reason': reason, 'status': 'created', 'created_at': datetime.now().isoformat(), 'idempotency_key': key}
        self.state['returns'].append(row); self._save()
        return self._record('create_return', {'order_id':order_id,'item_id':item_id,'reason':reason}, row)

    def create_refund(self, customer_id: str, order_id: str, amount: float, reason: str):
        key = f'refund:{order_id}:{round(float(amount),2)}:{reason.lower().strip()}'
        existing = self._idempotent(key, 'refunds')
        if existing:
            return self._record('create_refund', {'order_id':order_id,'amount':amount,'reason':reason}, existing)
        row = {'refund_id': 'RF-' + uuid.uuid4().hex[:10].upper(), 'customer_id': customer_id, 'order_id': order_id, 'amount': round(float(amount),2), 'reason': reason, 'status': 'released', 'created_at': datetime.now().isoformat(), 'idempotency_key': key}
        self.state['refunds'].append(row); self._save()
        return self._record('create_refund', {'order_id':order_id,'amount':amount,'reason':reason}, row)

    def create_support_ticket(self, customer_id: str, order_id: Optional[str], category: str, priority: str, summary: str, team: str):
        key = f'ticket:{customer_id}:{order_id}:{category}:{summary.strip().lower()}'
        existing = self._idempotent(key, 'tickets')
        if existing:
            return self._record('create_support_ticket', {'order_id':order_id,'category':category}, existing)
        row = {'ticket_id': 'CASE-' + uuid.uuid4().hex[:10].upper(), 'customer_id':customer_id,'order_id':order_id,'category':category,'priority':priority,'status':'open','assigned_team':team,'issue_summary':summary,'created_at':datetime.now().isoformat(),'idempotency_key':key}
        self.state['tickets'].append(row); self._save()
        return self._record('create_support_ticket', {'order_id':order_id,'category':category,'priority':priority}, row)

    def escalate_to_human(self, customer_id: str, order_id: Optional[str], team: str, reason: str, priority: str='medium'):
        key = f'escalate:{customer_id}:{order_id}:{team}:{reason.strip().lower()}'
        existing = self._idempotent(key, 'escalations')
        if existing:
            return self._record('escalate_to_human', {'order_id':order_id,'team':team}, existing)
        row = {'escalation_id':'ESC-' + uuid.uuid4().hex[:10].upper(),'customer_id':customer_id,'order_id':order_id,'team':team,'priority':priority,'reason':reason,'status':'queued','created_at':datetime.now().isoformat(),'idempotency_key':key}
        self.state['escalations'].append(row); self._save()
        return self._record('escalate_to_human', {'order_id':order_id,'team':team,'priority':priority}, row)

    def update_address(self, customer_id: str, order_id: str, new_address: str):
        key = f'address:{order_id}:{new_address.strip().lower()}'
        existing = self._idempotent(key, 'address_updates')
        if existing:
            return self._record('update_address', {'order_id':order_id}, existing)
        row={'update_id':'ADR-' + uuid.uuid4().hex[:10].upper(),'customer_id':customer_id,'order_id':order_id,'new_address':new_address.strip(),'status':'submitted','created_at':datetime.now().isoformat(),'idempotency_key':key}
        self.state['address_updates'].append(row); self._save()
        return self._record('update_address', {'order_id':order_id,'new_address':'[verified address]'}, row)

    def add_wallet_credit(self, customer_id: str, amount: float, reason: str):
        key=f'wallet:{customer_id}:{round(float(amount),2)}:{reason.strip().lower()}'
        existing=self._idempotent(key,'wallet_credits')
        if existing:
            return self._record('add_wallet_credit', {'amount':amount,'reason':reason}, existing)
        row={'credit_id':'CR-' + uuid.uuid4().hex[:10].upper(),'customer_id':customer_id,'amount':round(float(amount),2),'reason':reason,'created_at':datetime.now().isoformat(),'idempotency_key':key}
        self.state['wallet_credits'].append(row); self._save()
        return self._record('add_wallet_credit', {'amount':amount,'reason':reason}, row)

    def verify_result(self, kind: str, identifier: str):
        if kind == 'refund':
            found = next((r for r in self.state['refunds'] if r['refund_id']==identifier or r['idempotency_key']==identifier), None)
        elif kind == 'return':
            found = next((r for r in self.state['returns'] if r['return_id']==identifier or r['idempotency_key']==identifier), None)
        elif kind == 'ticket':
            found = next((r for r in self.state['tickets'] if r['ticket_id']==identifier or r['idempotency_key']==identifier), None)
        elif kind == 'escalation':
            found = next((r for r in self.state['escalations'] if r['escalation_id']==identifier or r['idempotency_key']==identifier), None)
        else:
            found = None
        self.trace.append({'type':'postcondition','name':'verify_result','parameters':{'kind':kind},'success':found is not None,'summary':'Action state verified' if found else 'Action state not found'})
        return found

    def reset_runtime(self):
        self.state={'refunds': [], 'returns': [], 'tickets': [], 'escalations': [], 'address_updates': [], 'wallet_credits': [], 'action_log': []}
        self._save()
        return self.state


def _summary(name, result):
    if result is None:
        return 'No matching record'
    if isinstance(result, dict) and 'count' in result:
        return f"Retrieved {result['count']} records"
    if isinstance(result, dict):
        keys = [k for k in ('order_id','customer_id','product_id','refund_id','return_id','ticket_id','escalation_id','status') if k in result]
        return 'Verified ' + ', '.join(f'{k}={result[k]}' for k in keys[:4])
    return 'Tool completed'
