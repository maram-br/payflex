from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import time 
app = FastAPI(title="PayFlex API")
payments = {}

class Payment(BaseModel):
    account_id: str
    amount: float
    currency: str = "EUR"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/payments", status_code=201)
def create(p: Payment):
    //time.sleep(0.6) 
    if p.amount <= 0:
        raise HTTPException(400, "Montant invalide")
    pid = str(uuid.uuid4())
    payments[pid] = p.model_dump()
    return {"id": pid, **payments[pid]}

@app.get("/payments/{pid}")
def get(pid: str):
    if pid not in payments:
        raise HTTPException(404, "Introuvable")
    return payments[pid]