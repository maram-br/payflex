import os
import time
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="PayFlex API")
payments = {}


def apply_demo_latency():
    """Latence désactivée par défaut, utilisée uniquement pour la preuve CI de rejet."""
    delay_ms = int(os.getenv("PAYFLEX_DELAY_MS", "0"))
    if delay_ms > 0:
        time.sleep(delay_ms / 1000)


class Payment(BaseModel):
    account_id: str
    amount: float
    currency: str = "EUR"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/payments", status_code=201)
def create(p: Payment):
    apply_demo_latency()
    if p.amount <= 0:
        raise HTTPException(400, "Montant invalide")
    pid = str(uuid.uuid4())
    payments[pid] = p.model_dump()
    return {"id": pid, **payments[pid]}


@app.get("/payments/{pid}")
def get(pid: str):
    apply_demo_latency()
    if pid not in payments:
        raise HTTPException(404, "Introuvable")
    return payments[pid]
