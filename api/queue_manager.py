from __future__ import annotations
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class QueueManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_to_queue(self, phone: str, message: str, priority: int = 5):
        # Evita duplicata em AGUARDANDO para o mesmo phone
        dup = await self.session.execute(
            text("""
                SELECT id FROM atendimento_queue
                WHERE phone = :phone AND status = 'AGUARDANDO'
                ORDER BY created_at ASC
                LIMIT 1
            """),
            {"phone": phone},
        )
        row = dup.first()
        if row:
            pos = await self._position(row[0])
            return {"queue_id": row[0], "position": pos, "estimated_wait": "~5 min"}

        rid = await self.session.execute(
            text("""
                INSERT INTO atendimento_queue (phone, message, priority)
                VALUES (:phone, :message, :priority)
                RETURNING id
            """),
            {"phone": phone, "message": message, "priority": priority},
        )
        qid = rid.scalar_one()
        await self.session.commit()
        return {"queue_id": qid, "position": await self._position(qid), "estimated_wait": "~5 min"}

    async def _position(self, queue_id: int) -> int:
        res = await self.session.execute(
            text("""
                WITH target AS (
                  SELECT priority, created_at FROM atendimento_queue WHERE id = :id
                )
                SELECT COUNT(*) FROM atendimento_queue, target
                WHERE status = 'AGUARDANDO'
                  AND (
                    atendimento_queue.priority < target.priority OR
                    (atendimento_queue.priority = target.priority AND atendimento_queue.created_at < target.created_at)
                  )
            """),
            {"id": queue_id},
        )
        return int(res.scalar_one())

    async def get_next(self, batch_size: int = 5):
        # Concorrência segura: FOR UPDATE SKIP LOCKED
        rows = await self.session.execute(
            text("""
                UPDATE atendimento_queue
                SET status = 'PROCESSANDO', started_at = NOW()
                WHERE id IN (
                  SELECT id FROM atendimento_queue
                  WHERE status = 'AGUARDANDO'
                  ORDER BY priority ASC, created_at ASC
                  FOR UPDATE SKIP LOCKED
                  LIMIT :batch
                )
                RETURNING id, phone, message, priority
            """),
            {"batch": batch_size},
        )
        await self.session.commit()
        return [dict(r._mapping) for r in rows.all()]

    # api/queue_manager.py (apenas mark_completed)
    async def mark_completed(self, queue_id: int, result: dict | None):
        from sqlalchemy import bindparam
        from sqlalchemy.dialects.postgresql import JSONB

        stmt = (
            text("""
                UPDATE atendimento_queue
                SET status = 'CONCLUIDO',
                    completed_at = NOW(),
                    result = :result
                WHERE id = :id
            """)
            .bindparams(bindparam("result", type_=JSONB))
        )

        await self.session.execute(stmt, {"id": queue_id, "result": result})
        await self.session.commit()


    async def mark_error(self, queue_id: int, error: str):
        await self.session.execute(
            text("""
                UPDATE atendimento_queue
                SET
                  status = CASE WHEN retry_count + 1 >= 3 THEN 'ERRO' ELSE 'AGUARDANDO' END,
                  last_error = :err,
                  retry_count = retry_count + 1
                WHERE id = :id
            """),
            {"id": queue_id, "err": error or "unknown"},
        )
        await self.session.commit()
