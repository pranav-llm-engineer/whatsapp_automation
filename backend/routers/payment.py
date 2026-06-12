from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession
from backend.db.database import get_db
from backend.db.models import Session, UserProfile, Payment
import random
import uuid

router = APIRouter(prefix="/payment", tags=["payment"])

class PaymentInitiateRequest(BaseModel):
    session_id: str
    amount: float
    membership_type: str
    billing_cycle: str

class PaymentConfirmRequest(BaseModel):
    txn_ref: str
    mock_result: str = None # "success" | "fail"

@router.post("/initiate")
def initiate_payment(req: PaymentInitiateRequest, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    txn_ref = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    new_payment = Payment(
        user_id=session.user_id,
        amount=req.amount,
        membership_type=req.membership_type,
        billing_cycle=req.billing_cycle,
        status="pending",
        txn_ref=txn_ref
    )
    db.add(new_payment)
    db.commit()
    
    return {"txn_ref": txn_ref, "status": "pending"}

@router.post("/confirm")
def confirm_payment(req: PaymentConfirmRequest, db: DBSession = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.txn_ref == req.txn_ref).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    result = req.mock_result or random.choice(["success", "success", "success", "fail"])
    payment.status = result
    
    if result == "success":
        profile = db.query(UserProfile).filter(UserProfile.user_id == payment.user_id).first()
        if profile:
            profile.onboarding_complete = True
            
    db.commit()
    return {"status": result, "txn_ref": req.txn_ref}
