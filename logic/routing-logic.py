# Classificador simples por regras/keywords
def classify_intent(message: str) -> dict:
    m = (message or "").lower()
    if "sinistro" in m or "batida" in m:
        return {"category": "SINISTRO"}
    if "seguro" in m or "cotação" in m or "venda" in m:
        return {"category": "VENDAS"}
    return {"category": "TRIAGEM"}