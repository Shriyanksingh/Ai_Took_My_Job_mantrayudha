from __future__ import annotations
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

class DataStore:
    def __init__(self, data_dir: Path, product_spec_dir: Path):
        self.data_dir = data_dir
        self.product_spec_dir = product_spec_dir
        self.customers = self._load_csv('customers.csv')
        self.orders = self._load_csv('orders.csv')
        self.order_items = self._load_csv('order_items.csv')
        self.products = self._load_csv('products.csv')
        self.reviews = self._load_csv('reviews.csv')
        self.tickets = self._load_csv('support_tickets.csv')
        self.conversations = self._load_json('conversations.json')

        self.customers_by_id = {r['customer_id']: r for r in self.customers}
        self.orders_by_id = {r['order_id']: r for r in self.orders}
        self.products_by_id = {r['product_id']: r for r in self.products}
        self.items_by_order: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.items_by_product: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in self.order_items:
            self.items_by_order[r['order_id']].append(r)
            self.items_by_product[r['product_id']].append(r)
        self.orders_by_customer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in self.orders:
            self.orders_by_customer[r['customer_id']].append(r)
        self.tickets_by_customer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in self.tickets:
            self.tickets_by_customer[r['customer_id']].append(r)
        self.conversations_by_customer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in self.conversations:
            self.conversations_by_customer[r.get('customer_id', '')].append(r)
        self.product_specs = self._load_product_specs()

    def _load_csv(self, filename: str) -> List[Dict[str, str]]:
        path = self.data_dir / filename
        with path.open('r', encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))

    def _load_json(self, filename: str) -> Any:
        with (self.data_dir / filename).open('r', encoding='utf-8') as f:
            return json.load(f)

    def _load_product_specs(self) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for path in self.product_spec_dir.glob('*.md'):
            text = path.read_text(encoding='utf-8')
            blocks = re.split(r'(?=^##\s+.+\(PROD-\d+\))', text, flags=re.M)
            for block in blocks:
                m = re.search(r'\((PROD-\d+)\)', block)
                if not m:
                    continue
                pid = m.group(1)
                title = re.search(r'^##\s+(.+?)\s*\((PROD-\d+)\)', block, re.M)
                specs = {}
                for row in re.findall(r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$', block, re.M):
                    k, v = row
                    if k.strip().lower() not in {'specification', 'field'} and k.strip() not in {'---', '---:'}:
                        specs[k.strip()] = v.strip()
                result[pid] = {
                    'product_id': pid,
                    'product_name': title.group(1) if title else self.products_by_id.get(pid, {}).get('product_name', pid),
                    'source_file': path.name,
                    'raw_text': block.strip(),
                    'specs': specs,
                }
        return result

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        return self.customers_by_id.get(customer_id)

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        return self.orders_by_id.get(order_id)

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        return self.products_by_id.get(product_id)

    def get_order_items(self, order_id: str) -> List[Dict[str, Any]]:
        return list(self.items_by_order.get(order_id, []))

    def get_product_spec(self, product_id: str) -> Optional[Dict[str, Any]]:
        return self.product_specs.get(product_id)

    def customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        return sorted(self.orders_by_customer.get(customer_id, []), key=lambda x: x['order_date'], reverse=True)

    def customer_tickets(self, customer_id: str) -> List[Dict[str, Any]]:
        return sorted(self.tickets_by_customer.get(customer_id, []), key=lambda x: x.get('created_at', ''), reverse=True)

    def customer_conversations(self, customer_id: str) -> List[Dict[str, Any]]:
        return sorted(self.conversations_by_customer.get(customer_id, []), key=lambda x: x.get('started_at', ''), reverse=True)

    def search_customer_products(self, customer_id: str, text: str) -> List[Dict[str, Any]]:
        tokens = {t.lower() for t in re.findall(r'[a-z0-9]+', text) if len(t) > 2}
        candidates = []
        for order in self.customer_orders(customer_id):
            for item in self.get_order_items(order['order_id']):
                prod = self.get_product(item['product_id'])
                if not prod:
                    continue
                hay = ' '.join([prod.get('product_name',''), prod.get('category',''), prod.get('subcategory',''), prod.get('brand','')]).lower()
                score = sum(1 for t in tokens if t in hay)
                if score:
                    candidates.append((score, order, item, prod))
        candidates.sort(key=lambda x: (x[0], x[1]['order_date']), reverse=True)
        return [{'order': o, 'item': i, 'product': p, 'score': s} for s,o,i,p in candidates]

    def search_products(self, text: str, limit: int = 8) -> List[Dict[str, Any]]:
        tokens = {t.lower() for t in re.findall(r'[a-z0-9]+', text) if len(t) > 2}
        scored = []
        for p in self.products:
            hay = ' '.join([p.get('product_name',''), p.get('category',''), p.get('subcategory',''), p.get('brand',''), p.get('description','')]).lower()
            score = sum(1 for t in tokens if t in hay)
            if score:
                scored.append((score, p))
        scored.sort(key=lambda x: (x[0], float(x[1].get('rating') or 0)), reverse=True)
        return [p for _, p in scored[:limit]]
