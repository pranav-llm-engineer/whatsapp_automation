from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import User, UserProfile
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import uuid
from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    phone: str
    password: str

class UserLogin(BaseModel):
    phone: str
    password: str

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone == user.phone).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Phone already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(phone=user.phone, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create empty profile
    new_profile = UserProfile(user_id=new_user.id)
    db.add(new_profile)
    db.commit()
    
    return {"message": "User created successfully"}

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone == user.phone).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect phone or password")
    
    # Create session token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    
    # Create session record (we will generate a real UUID session token later, but let's use the JWT or UUID for now)
    session_id = str(uuid.uuid4())
    # Note: Using UUID for session_id in our DB.
    # We could just pass this UUID to frontend, or pass the JWT. Let's return token.
    # Let's save a Session explicitly if needed, but for now we rely on JWT.
    # Wait, the plan says:
    # `sessions` table has id=UUID token. So let's create a session.
    
    from backend.db.models import Session as DBSession
    new_session = DBSession(id=session_id, user_id=db_user.id)
    db.add(new_session)
    db.commit()
    
    return {"access_token": session_id, "token_type": "bearer", "user_id": db_user.id}

@router.get("/me")
def get_me(session_id: str, db: Session = Depends(get_db)):
    # Simple dependency replacement, in real app use bearer token
    from backend.db.models import Session as DBSession
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == session.user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    return {
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "onboarding_active": profile.onboarding_active,
        "onboarding_step": profile.onboarding_step,
        "onboarding_complete": profile.onboarding_complete,
        "spaceType": profile.spaceType,
        "seatRangeMin": profile.seatRangeMin,
        "seatRangeMax": profile.seatRangeMax,
        "urgency": profile.urgency,
        "location": profile.location,
        "phone": session.user.phone
    }
