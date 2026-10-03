from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

INR_RE = re.compile(r'INR\s*([0-9][0-9,]*)', re.I)


class PolicyCompiler:
    """Compile the supplied policy markdown into machine-readable runtime rules.

    `runtime_file` is a small overlay used by the mutation demo. The compiled
    rules are written to `compiled_file`, keeping source/overlay separate from
    the generated artifact.
    """

    def __init__(
        self,
        policy_dir: Path,
        runtime_file: Path,
        compiled_file: Optional[Path] = None,
    ):
        self.policy_dir = Path(policy_dir)
        self.runtime_file = Path(runtime_file)
        self.compiled_file = Path(compiled_file) if compiled_file else self.runtime_file
        self.raw: Dict[str, str] = {}
        self.compiled: Dict[str, Any] = self.compile_all()

    @staticmethod
    def _money(text: str, default: int) -> int:
        m = INR_RE.search(text)
        return int(m.group(1).replace(',', '')) if m else default

    def _compile_refund(self, version: str) -> Dict[str, Any]:
        text = self.raw[f'refund_policy_{version}.md']
        if version == 'v1':
            defaults = {
                'change_of_mind_days': 10,
                'defect_days': 15,
                'approval_threshold': 100000,
                'gold_extra': 2,
                'platinum_extra': 3,
                'restocking_percent': 0.0,
                'restocking_cap': 0,
            }
        else:
            defaults = {
                'change_of_mind_days': 7,
                'defect_days': 10,
                'approval_threshold': 75000,
                'gold_extra': 2,
                'platinum_extra': 3,
                'restocking_percent': 0.05,
                'restocking_cap': 2500,
            }

        cm = re.search(r'Change of mind.*?\*\*(\d+) days\*\*', text, re.I | re.S)
        defect = re.search(r'Product defective.*?\*\*(\d+) days\*\*', text, re.I | re.S)
        threshold_match = re.search(
            r'Order total.*?(?:or less|above).*?(INR\s*[\d,]+)', text, re.I | re.S
        )
        threshold = (
            self._money(threshold_match.group(1), defaults['approval_threshold'])
            if threshold_match
            else defaults['approval_threshold']
        )
        if version == 'v1' and re.search(r'INR\s*1,00,000', text, re.I):
            threshold = 100000
        if version == 'v2' and re.search(r'INR\s*75,000', text, re.I):
            threshold = 75000

        g = re.search(r'Gold \+(\d+) days', text, re.I)
        p = re.search(r'Platinum \+(\d+) days', text, re.I)
        rp = re.search(
            r'(?:fee|restocking fee).*?(\d+(?:\.\d+)?)%.*?maximum INR\s*([0-9,]+)',
            text,
            re.I | re.S,
        )

        return {
            'version': version,
            'effective_date': '2026-01-01' if version == 'v1' else '2026-06-01',
            'change_of_mind_days': int(cm.group(1)) if cm else defaults['change_of_mind_days'],
            'defect_days': int(defect.group(1)) if defect else defaults['defect_days'],
            'approval_threshold': threshold,
            'gold_extra': int(g.group(1)) if g else defaults['gold_extra'],
            'platinum_extra': int(p.group(1)) if p else defaults['platinum_extra'],
            'restocking_percent': float(rp.group(1)) / 100 if rp else defaults['restocking_percent'],
            'restocking_cap': int(rp.group(2).replace(',', '')) if rp else defaults['restocking_cap'],
        }

    def compile_all(self) -> Dict[str, Any]:
        self.raw = {
            p.name: p.read_text(encoding='utf-8')
            for p in self.policy_dir.glob('*.md')
        }

        compiled: Dict[str, Any] = {
            'refund': {
                'v1': self._compile_refund('v1'),
                'v2': self._compile_refund('v2'),
            },
            'shipping': {
                'otp_threshold': 5000,
                'goodwill_per_three_days': 100,
                'goodwill_cap': 300,
                'lost_after_days': 7,
                'lost_investigation_hours': 72,
                'delivered_no_otp_hours': 48,
            },
            'payment': {
                'pending_wait_hours': 24,
                'refund_reflect_business_days': {
                    'wallet': 'instant',
                    'upi': '1-3',
                    'card': '5-7',
                    'net_banking': '5-7',
                },
            },
            'warranty': {},
            'source_files': sorted(self.raw.keys()),
        }

        # Mutations are explicit runtime overlays. This lets the demo change
        # data without editing source code.
        if self.runtime_file.exists():
            try:
                overlay = json.loads(self.runtime_file.read_text(encoding='utf-8'))
                for version, values in overlay.get('refund', {}).items():
                    if version in compiled['refund'] and isinstance(values, dict):
                        compiled['refund'][version].update(values)
                for family in ('shipping', 'payment', 'warranty'):
                    values = overlay.get(family)
                    if isinstance(values, dict) and family in compiled:
                        compiled[family].update(values)
            except (OSError, ValueError, TypeError):
                # Invalid overlay should never crash the support service.
                pass

        self.compiled_file.parent.mkdir(parents=True, exist_ok=True)
        self.compiled_file.write_text(
            json.dumps(compiled, indent=2, sort_keys=True),
            encoding='utf-8',
        )
        return compiled

    def refresh(self) -> Dict[str, Any]:
        self.compiled = self.compile_all()
        return self.compiled

    def version_for_order(self, order_date: str) -> str:
        return 'v1' if order_date[:10] < '2026-06-01' else 'v2'

    def refund(self, version: str) -> Dict[str, Any]:
        return self.compiled['refund'][version]
