from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import csv, json
from app.config import DATA_DIR, PRODUCT_SPEC_DIR

EXPECTED={'customers.csv':1500,'orders.csv':8000,'order_items.csv':12444,'products.csv':300,'support_tickets.csv':2500,'reviews.csv':3000}
for file,n in EXPECTED.items():
    with (DATA_DIR/file).open(encoding='utf-8',newline='') as f:
        count=sum(1 for _ in csv.DictReader(f))
    print(f'{file}: {count} records (expected {n})')
with (DATA_DIR/'conversations.json').open(encoding='utf-8') as f:
    conv=json.load(f)
print(f'conversations.json: {len(conv)} records (expected 1500)')
# Product markdown coverage.
ids=set()
import re
for p in PRODUCT_SPEC_DIR.glob('*.md'):
    ids.update(re.findall(r'\bPROD-\d{5}\b',p.read_text(encoding='utf-8')))
print(f'product spec IDs: {len(ids)}')
