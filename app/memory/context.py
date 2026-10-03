from __future__ import annotations
from typing import Any, Dict

class MemoryManager:
    def __init__(self, store):
        self.store = store

    def retrieve(self, customer_id: str) -> Dict[str, Any]:
        conversations = self.store.customer_conversations(customer_id)[:5]
        tickets = self.store.customer_tickets(customer_id)[:10]
        recent_messages = []
        for conv in conversations:
            for msg in conv.get('messages', [])[-6:]:
                recent_messages.append({
                    'conversation_id': conv.get('conversation_id'),
                    'role': msg.get('role'),
                    'timestamp': msg.get('timestamp'),
                    'message': msg.get('message'),
                })
        return {
            'conversation_count': len(conversations),
            'ticket_count': len(tickets),
            'recent_messages': recent_messages[-20:],
            'open_tickets': [t for t in tickets if t.get('status','').lower() not in {'closed','resolved'}],
            'recent_tickets': tickets,
        }
