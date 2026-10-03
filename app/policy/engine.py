from __future__ import annotations
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, Optional

from .rules import parse_date, day_number, effective_change_window, restocking_fee

class PolicyEngine:
    def __init__(self, store, compiler):
        self.store = store
        self.compiler = compiler

    @property
    def policies(self):
        return self.compiler.compiled

    def refresh(self):
        self.compiler.refresh()

    def version_for_order(self, order: Dict[str, Any]) -> str:
        return self.compiler.version_for_order(order['order_date'])

    def policy_snapshot(self, order: Dict[str, Any]) -> Dict[str, Any]:
        v = self.version_for_order(order)
        return {'version': v, **self.compiler.refund(v)}

    def repeated_claims(self, customer_id: str, now: date) -> int:
        count = 0
        for t in self.store.customer_tickets(customer_id):
            if t.get('category','').lower() not in {'refund','return','delivery','non_delivery','payment'}:
                continue
            try:
                d = parse_date(t.get('created_at',''))
            except Exception:
                continue
            if 0 <= (now - d).days <= 90:
                count += 1
        return count

    def approval_required(self, order: Dict[str, Any]) -> bool:
        p = self.compiler.refund(self.version_for_order(order))
        return float(order['total_amount']) > float(p['approval_threshold'])

    def refund_window(self, order: Dict[str, Any], customer: Dict[str, Any], reason: str) -> int:
        p = self.compiler.refund(self.version_for_order(order))
        if reason == 'change_of_mind':
            return effective_change_window(p, customer.get('loyalty_tier',''))
        if reason in {'defective','damaged','wrong_item','missing_item'}:
            return int(p['defect_days'])
        return 0

    def _evidence_present(self, order_id: str, reason: str, customer_id: str) -> bool:
        for t in self.store.customer_tickets(customer_id):
            if t.get('order_id') != order_id:
                continue
            hay = ' '.join([t.get('category',''), t.get('subcategory',''), t.get('issue_summary',''), t.get('resolution','')]).lower()
            if reason == 'damaged' and ('damage' in hay or 'transit' in hay or 'crack' in hay): return True
            if reason == 'defective' and ('defect' in hay or 'dead' in hay or 'fault' in hay): return True
            if reason == 'wrong_item' and ('wrong' in hay or 'incorrect item' in hay): return True
            if reason == 'missing_item' and ('missing' in hay): return True
        # Public conversations can also indicate evidence was already provided.
        for c in self.store.customer_conversations(customer_id):
            if c.get('order_id') != order_id:
                continue
            text = ' '.join(m.get('message','') for m in c.get('messages', [])).lower()
            if 'photo' in text or 'video' in text or 'image' in text:
                if reason in {'damaged','defective','wrong_item','missing_item'}:
                    return True
        return False

    def _prior_in_window_request(self, customer_id: str, order_id: str, delivery_date: str, window: int, now_date: date) -> Optional[str]:
        for t in self.store.customer_tickets(customer_id):
            if t.get('order_id') != order_id:
                continue
            if t.get('category','').lower() not in {'refund','return','delivery','non_delivery'}:
                continue
            try:
                created = parse_date(t['created_at'])
            except Exception:
                continue
            if 0 <= (created - parse_date(delivery_date)).days <= window:
                if (now_date - parse_date(delivery_date)).days > window:
                    return t['created_at']
        return None

    def check_refund_eligibility(self, order: Dict[str, Any], customer: Dict[str, Any], product: Dict[str, Any], reason: str, now: str, evidence_supplied: bool = False, requested_destination: Optional[str] = None) -> Dict[str, Any]:
        now_date = parse_date(now)
        p = self.compiler.refund(self.version_for_order(order))
        result: Dict[str, Any] = {
            'eligible': False,
            'reason_code': reason,
            'policy_version': p['version'],
            'window_days': None,
            'day_number': None,
            'approval_required': self.approval_required(order),
            'evidence_required': reason in {'defective','damaged','wrong_item','missing_item'},
            'evidence_verified': False,
            'issues': [],
        }
        if customer.get('account_status','').lower() == 'suspended':
            result['issues'].append('account_suspended')
            return result
        if requested_destination and requested_destination.lower() not in {'original','original payment method','original payment instrument'}:
            result['issues'].append('different_refund_destination')
            return result
        if order.get('refund_status','').lower() in {'processed','partial','refunded','partially_refunded'}:
            result['issues'].append('already_refunded_or_partial')
            return result
        window = self.refund_window(order, customer, reason)
        result['window_days'] = window
        if reason == 'non_delivery':
            if order.get('order_status','').lower() == 'delivered':
                result['issues'].append('delivered_order_non_delivery_handled_by_shipping')
                return result
            eta = parse_date(order['estimated_delivery_date'])
            days_after_eta = (now_date - eta).days
            result['day_number'] = days_after_eta
            result['eligible'] = 7 <= days_after_eta <= 30
            if not result['eligible']:
                result['issues'].append('lost_in_transit_window_not_met')
            return result
        if reason in {'cancelled_prepaid'}:
            result['eligible'] = True
            return result
        if reason == 'duplicate_charge':
            result['eligible'] = True
            result['window_days'] = 30
            return result
        if not order.get('actual_delivery_date'):
            result['issues'].append('delivery_not_verified')
            return result
        dn = day_number(order['actual_delivery_date'], now_date)
        result['day_number'] = dn
        if reason == 'change_of_mind' and str(product.get('returnable','')).lower() != 'true':
            result['issues'].append('product_not_returnable_for_change_of_mind')
            return result
        if reason in {'defective','damaged','wrong_item','missing_item'}:
            result['evidence_verified'] = bool(evidence_supplied or self._evidence_present(order['order_id'], reason, customer['customer_id']))
            if not result['evidence_verified']:
                result['issues'].append('evidence_required')
                return result
        if dn <= window:
            result['eligible'] = True
        else:
            # Legitimate exception: request raised inside the original window but processing delayed by NovaMart/courier.
            prior = self._prior_in_window_request(customer['customer_id'], order['order_id'], order['actual_delivery_date'], window, now_date)
            if prior:
                result['eligible'] = True
                result['exception'] = 'request_raised_in_time'
                result['original_request_at'] = prior
            else:
                result['issues'].append('outside_policy_window')
        return result

    def calculate_refund(self, order: Dict[str, Any], items: list[Dict[str, Any]], product: Dict[str, Any], reason: str) -> Dict[str, Any]:
        p = self.compiler.refund(self.version_for_order(order))
        item_rows = items
        base = sum(float(i['final_price']) * 1.18 for i in item_rows)
        shipping_refund = 0.0
        if reason in {'damaged','defective','wrong_item','non_delivery','cancelled_prepaid'}:
            shipping_refund = float(order.get('shipping_fee') or 0)
        fee = 0.0 if reason != 'change_of_mind' else restocking_fee(p, product.get('category',''), base)
        refund = max(0.0, base - fee + shipping_refund)
        order_cap = float(order['total_amount'])
        refund = min(refund, order_cap)
        return {
            'item_refund_before_fee': round(base,2),
            'restocking_fee': round(fee,2),
            'shipping_refund': round(shipping_refund,2),
            'refund_amount': round(refund,2),
            'order_total_cap': order_cap,
            'policy_version': p['version'],
        }
