from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .db import get_session, ping_db
from .queue_manager import QueueManager
from .customer_router import CustomerRouter

app = FastAPI(title="Olga AI - API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db/health")
async def db_health():
    ok = await ping_db()
    return {"db": "ok" if ok else "down"}

@app.get("/customers/count")
async def customers_count(session: AsyncSession = Depends(get_session)):
    r = await session.execute(text("SELECT COUNT(*) FROM customers"))
    return {"customers": r.scalar_one()}

# -----------------------
# Fila de atendimento
# -----------------------
@app.post("/api/queue/add")
async def add_queue(payload: dict, session: AsyncSession = Depends(get_session)):
    phone = payload.get("phone")
    message = payload.get("message")
    priority = int(payload.get("priority", 5))
    if not phone or not message:
        raise HTTPException(status_code=400, detail="phone e message são obrigatórios")
    qm = QueueManager(session)
    return await qm.add_to_queue(phone, message, priority)

@app.post("/api/queue/next")
async def next_items(payload: dict | None = None, session: AsyncSession = Depends(get_session)):
    batch = int((payload or {}).get("batchSize", 5))
    qm = QueueManager(session)
    return await qm.get_next(batch)

@app.post("/api/queue/{qid}/complete")
async def complete(
    qid: int = Path(..., ge=1),
    payload: dict | None = None,
    session: AsyncSession = Depends(get_session)
):
    qm = QueueManager(session)
    await qm.mark_completed(qid, payload or {})
    return {"ok": True}

@app.post("/api/queue/{qid}/error")
async def error(
    qid: int = Path(..., ge=1),
    payload: dict | None = None,
    session: AsyncSession = Depends(get_session)
):
    qm = QueueManager(session)
    await qm.mark_error(qid, (payload or {}).get("error", "unknown"))
    return {"ok": True}

# -----------------------
# Roteamento
# -----------------------
@app.post("/api/router/route")
async def route(payload: dict, session: AsyncSession = Depends(get_session)):
    phone = payload.get("phone")
    message = payload.get("message")
    if not phone or not message:
        raise HTTPException(status_code=400, detail="phone e message são obrigatórios")
    cr = CustomerRouter(session)
    return await cr.route(phone, message)
