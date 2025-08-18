from typing import TypedDict, Optional
from langgraph.graph import StateGraph

class SinistroState(TypedDict, total=False):
    phone: str
    message: str
    customer_data: dict
    policy_validated: bool
    claim_classified: bool
    fraud_analyzed: bool
    protocol_generated: str
    response_sent: bool
    error: Optional[str]

def validate_policy(s: SinistroState) -> SinistroState:
    s["policy_validated"] = bool(s.get("customer_data"))
    return s

def classify_claim(s: SinistroState) -> SinistroState:
    s["claim_classified"] = True
    return s

def analyze_fraud(s: SinistroState) -> SinistroState:
    s["fraud_analyzed"] = True
    return s

def generate_protocol(s: SinistroState) -> SinistroState:
    s["protocol_generated"] = "SIN" + "000001"
    return s

def send_response(s: SinistroState) -> SinistroState:
    s["response_sent"] = True
    return s

def create_sinistro_graph():
    g = StateGraph(SinistroState)
    g.add_node("validate_policy", validate_policy)
    g.add_node("classify_claim", classify_claim)
    g.add_node("analyze_fraud", analyze_fraud)
    g.add_node("generate_protocol", generate_protocol)
    g.add_node("send_response", send_response)

    g.set_entry_point("validate_policy")
    g.add_edge("validate_policy", "classify_claim")
    g.add_edge("classify_claim", "analyze_fraud")
    g.add_edge("analyze_fraud", "generate_protocol")
    g.add_edge("generate_protocol", "send_response")
    return g.compile()
