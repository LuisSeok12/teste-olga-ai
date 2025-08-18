from __future__ import annotations
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class CustomerRouter:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_customer(self, phone: str):
        row = await self.session.execute(
            text("""
                SELECT
                  c.id,
                  c.name,
                  EXISTS(
                    SELECT 1 FROM policies p
                    WHERE p.customer_id = c.id AND p.status = 'ACTIVE'
                  ) AS has_active_policy
                FROM customers c
                WHERE c.phone = :phone
                LIMIT 1
            """),
            {"phone": phone},
        )
        r = row.first()
        return dict(r._mapping) if r else None

    async def classify_intent(self, message: str):
        m = (message or "").lower()
        if any(k in m for k in ["sinistro", "batida", "roubo", "acidente"]):
            return {"category": "SINISTRO"}
        if any(k in m for k in ["comprar", "cotação", "cotacao", "renovar", "reativar", "simulação", "simulacao"]):
            return {"category": "VENDAS"}
        return {"category": "NEUTRO"}

    # api/customer_router.py (apenas o método route)
    async def route(self, phone: str, message: str):
        cust = await self.find_customer(phone)
        intent = await self.classify_intent(message)

        # 1) Se a intenção é SINISTRO
        if intent["category"] == "SINISTRO":
            if cust and cust["has_active_policy"]:
                return {
                    "flow": "SINISTRO",
                    "subworkflow": "process-sinistro",
                    "customer_data": cust,
                    "next_action": "VALIDATE_POLICY",
                }
            else:
                # Sem apólice ativa ou cliente desconhecido:
                # abrir intake de sinistro pedindo identificação/apólice
                return {
                    "flow": "SINISTRO_INTAKE",
                    "subworkflow": "collect-identity-and-policy",
                    "customer_data": cust,  # pode ser None
                    "next_action": "COLLECT_ID_AND_POLICY",
                }

        # 2) Cliente conhecido mas sem apólice ativa
        if cust and not cust["has_active_policy"]:
            return {
                "flow": "REATIVACAO",
                "subworkflow": "process-reativacao",
                "customer_data": cust,
                "next_action": "OFFER_RENEWAL",
            }

        # 3) Intenção de vendas
        if intent["category"] == "VENDAS":
            return {
                "flow": "VENDAS",
                "subworkflow": "process-vendas",
                "customer_data": cust,
                "next_action": "COLLECT_LEAD_INFO",
            }

        # 4) Caso neutro
        return {
            "flow": "TRIAGEM",
            "subworkflow": "process-triagem",
            "customer_data": cust,
            "next_action": "ASK_INTENT",
        }

