from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

ORDER_RE = re.compile(r'#?\b(?:ORD|NM)[- ]*(\d+)\b', re.I)
ORDER_ALPHA_RE = re.compile(r'#?\b(?:ORD|NM)-([A-Za-z0-9]+)\b', re.I)
ORDER_NUM_RE = re.compile(r'\border\s*(?:id|no|number|#)?\s*[:#-]?\s*(\d{1,6})\b', re.I)
DIGIT_ONLY_RE = re.compile(r'#?(\d{6})\b')
PRODUCT_RE = re.compile(r'\bPROD[- ]?\d{5}\b', re.I)
INR_RE = re.compile(r'(?:₹|INR\s*)\s*([0-9][0-9,]*(?:\.\d+)?)', re.I)
ADDRESS_RE = re.search

INTENT_PATTERNS = [
    ('safety', [r'swollen\s+battery', r'overheating', r'smoke', r'burning\s+smell']),
    ('invoice', [r'\binvoice\b', r'\breceipt\b', r'\bbill\b', r'tax invoice', r'download invoice']),
    ('order_history', [r'show (?:my|all) orders', r'my orders', r'order history', r'past orders', r'recent orders', r'list (?:my|all) orders', r'what (?:did i|have i) (?:buy|order)', r'my purchases']),
    ('delivery', [r'where is', r'order status', r'track', r'courier', r'delivery', r'eta', r'when will .*arrive', r'not arrived', r'not received', r'never received', r'never arrived', r'order details', r'check order', r'about order', r'order info', r'\bmy order\b']),
    ('refund', [r'refund', r'money back', r'give me my money']),
    ('return', [r'\breturn\b', r'send .* back', r'defective', r'faulty', r'dead on arrival', r'damaged', r'wrong item', r'broken']),
    ('replacement', [r'replace', r'replacement', r'exchange']),
    ('cancellation', [r'cancel', r'cancellation']),
    ('address_change', [r'change .*address', r'update .*address', r'deliver .* to', r'ship .* to']),
    ('payment', [r'payment', r'charged', r'debited', r'deducted', r'pending payment', r'double charged', r'duplicate charge']),
    ('warranty', [r'warranty', r'under warranty', r'paid repair', r'repair']),
    ('product_info', [r'spec', r'specification', r'ram', r'storage', r'bluetooth', r'battery life', r'compatible', r'in stock', r'price', r'weight']),
]

REASON_MAP = {
    'change of mind':'change_of_mind', 'changed my mind':'change_of_mind', 'don\'t want':'change_of_mind', 'not needed':'change_of_mind',
    'defective':'defective', 'defect':'defective', 'dead on arrival':'defective', 'faulty':'defective', 'broken':'defective',
    'damaged':'damaged', 'damage':'damaged', 'damaged in transit':'damaged',
    'wrong item':'wrong_item', 'incorrect item':'wrong_item', 'different item':'wrong_item',
    'missing item':'missing_item', 'missing from package':'missing_item',
    'never arrived':'non_delivery', 'never received':'non_delivery', 'not delivered':'non_delivery', 'not received':'non_delivery', 'where is my order':'delivery',
    'duplicate charge':'duplicate_charge', 'charged twice':'duplicate_charge', 'money deducted':'payment_issue',
}


def _find_product_id(text: str) -> Optional[str]:
    m = PRODUCT_RE.search(text)
    if not m:
        return None
    return m.group(0).upper().replace(' ', '-')

def _find_order_id(text: str, customer_orders: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    m = ORDER_RE.search(text)
    if m:
        val = m.group(1)
        return f"ORD-{val.zfill(6)}" if len(val) < 6 else f"ORD-{val}"
    m = ORDER_ALPHA_RE.search(text)
    if m:
        return f"ORD-{m.group(1).upper()}"
    m = ORDER_NUM_RE.search(text)
    if m:
        val = m.group(1)
        return f"ORD-{val.zfill(6)}"
    m = DIGIT_ONLY_RE.search(text)
    if m:
        return f"ORD-{m.group(1)}"
    if customer_orders:
        low = text.lower()
        for o in customer_orders:
            oid = o.get('order_id', '')
            if oid and oid.lower() in low:
                return oid
            num = oid.replace('ORD-', '')
            if num and num in low:
                return oid
    return None


def _amount(text: str) -> Optional[float]:
    m = INR_RE.search(text)
    return float(m.group(1).replace(',','')) if m else None


def _reason(text: str) -> Optional[str]:
    low = text.lower()
    for phrase, reason in sorted(REASON_MAP.items(), key=lambda x: -len(x[0])):
        if phrase in low:
            return reason
    if 'refund' in low or 'return' in low or 'replace' in low:
        return 'change_of_mind'
    return None


def _split_multi(text: str) -> List[str]:
    # Keep clauses coherent; split only when conjunction introduces a distinct support verb.
    pieces = re.split(r'\s*(?:;|\band\s+(?:also|please|can you)?|\bplus\b)\s*', text, flags=re.I)
    return [p.strip(' .') for p in pieces if p.strip(' .')]


def infer_intents(text: str, store, customer_id: str) -> List[Dict[str, Any]]:
    cust_orders = store.customer_orders(customer_id) if (store and customer_id) else []
    clauses = _split_multi(text)
    if len(clauses) == 1:
        clauses = [text]
    intents: List[Dict[str, Any]] = []
    used = set()
    for clause in clauses:
        low = clause.lower()
        matched = []
        for intent, patterns in INTENT_PATTERNS:
            if any(re.search(p, low) for p in patterns):
                matched.append(intent)
        if not matched:
            if _find_order_id(clause, cust_orders):
                matched = ['delivery']
            else:
                matched = ['general']
        # For a clause like "refund and change delivery address", ensure both intents are represented.
        for intent in matched:
            key=(intent, clause.lower())
            if key in used: continue
            used.add(key)
            intents.append({'id': 'I-' + uuid4().hex[:6].upper(), 'intent': intent, 'text': clause, 'order_id': _find_order_id(clause, cust_orders), 'product_id': _find_product_id(clause), 'requested_amount': _amount(clause), 'reason': _reason(clause), 'dependencies': []})

    # De-dupe intent types when the parser split a single multi-intent sentence imperfectly.
    if len(intents) == 1 and ' and ' in text.lower():
        low=text.lower()
        for intent, trigger in [('refund','refund'),('address_change','address'),('delivery','arrive'),('cancellation','cancel'),('replacement','replace'),('warranty','warranty')]:
            if trigger in low and intent not in {intents[0]['intent']}:
                intents.append({'id':'I-'+uuid4().hex[:6].upper(),'intent':intent,'text':text,'order_id':_find_order_id(text, cust_orders),'product_id':_find_product_id(text),'requested_amount':_amount(text),'reason':_reason(text),'dependencies':[]})

    # Dependency rules.
    ids_by_intent = {i['intent']: i['id'] for i in intents}
    for i in intents:
        if i['intent'] == 'refund' and 'non_delivery' in [x.get('reason') for x in intents]:
            i['dependencies'] = [ids_by_intent.get('delivery')] if ids_by_intent.get('delivery') else []
        if i['intent'] == 'refund' and any('never arrived' in x['text'].lower() or 'not received' in x['text'].lower() for x in intents if x is not i):
            i['dependencies'] = [ids_by_intent.get('delivery')] if ids_by_intent.get('delivery') else []
    return intents
