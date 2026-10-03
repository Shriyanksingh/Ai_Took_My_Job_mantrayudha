from __future__ import annotations
import re
from typing import Dict, List

INJECTION_PATTERNS = [
    r'ignore\s+(all\s+)?previous\s+instructions',
    r'ignore\s+your\s+instructions',
    r'forget\s+the\s+policy',
    r'reveal\s+(your|the)\s+(system\s+prompt|prompt)',
    r'print\s+(your|the)\s+system\s+prompt',
    r'you\s+are\s+now\s+(an|the)\s+administrator',
    r'you\s+are\s+now\s+in\s+maintenance\s+mode',
    r'bypass\s+(the\s+)?(policy|checks|verification)',
    r'override\s+(the\s+)?(policy|limit|threshold|rules)',
    r'customer\s+is\s+admin',
    r'system\s*:\s*refund\s+approved',
]
LEGAL_PATTERNS = [r'\bi\s+(?:will|am|going to)\s+sue\b', r'\blawyer\b', r'\blegal\s+notice\b', r'\bconsumer\s+court\b', r'\bcourt\b']
SAFETY_PATTERNS = [r'swollen\s+battery', r'overheating', r'\bsmoke\b', r'burning\s+smell', r'battery.*swollen']
ABUSE_PATTERNS = [r'\bidiot\b', r'\bstupid\b', r'\bshut\s+up\b', r'\bkill\b']
HUMAN_PATTERNS = [r'\bhuman\b', r'\bhuman\s+agent\b', r'\breal\s+person\b', r'\bsupervisor\b']


def _matches(patterns: List[str], text: str) -> List[str]:
    low = text.lower()
    return [p for p in patterns if re.search(p, low)]


def inspect(text: str) -> Dict[str, object]:
    return {
        'injection': bool(_matches(INJECTION_PATTERNS, text)),
        'injection_patterns': _matches(INJECTION_PATTERNS, text),
        'legal': bool(_matches(LEGAL_PATTERNS, text)),
        'safety': bool(_matches(SAFETY_PATTERNS, text)),
        'abusive': bool(_matches(ABUSE_PATTERNS, text)),
        'human_request': bool(_matches(HUMAN_PATTERNS, text)),
    }
