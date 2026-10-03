from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

Decision = Literal['ANSWER', 'ASK', 'ACT', 'ESCALATE']

class ChatRequest(BaseModel):
    customer_id: str
    message: str = Field(min_length=1)
    now: Optional[str] = None
    session_id: Optional[str] = None
    use_llm: bool = False

class IntentModel(BaseModel):
    id: str
    intent: str
    text: str
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    requested_amount: Optional[float] = None
    requested_destination: Optional[str] = None
    reason: Optional[str] = None
    dependencies: List[str] = []

class DecisionModel(BaseModel):
    decision: Decision
    reason: str
    customer_response: str
    intent_id: Optional[str] = None
    actions: List[Dict[str, Any]] = []
    evidence: Dict[str, Any] = {}
    policy: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    request_id: str
    decision: Decision
    customer_response: str
    intents: List[IntentModel]
    intent_results: List[DecisionModel]
    evidence: Dict[str, Any]
    trace: List[Dict[str, Any]]
    policy: Dict[str, Any]
    stats: Dict[str, Any]

class MutationRequest(BaseModel):
    policy_version: Literal['v1', 'v2']
    change_of_mind_days: Optional[int] = None
    defect_days: Optional[int] = None
    approval_threshold: Optional[int] = None
    loyalty_gold_extra: Optional[int] = None
    loyalty_platinum_extra: Optional[int] = None
    restocking_percent: Optional[float] = None
    restocking_cap: Optional[int] = None

class GenericMessage(BaseModel):
    message: str

class GeminiConfigRequest(BaseModel):
    api_key: str
    model: Optional[str] = None
