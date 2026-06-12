from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from backend.db.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    sessions = relationship("Session", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    full_name = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    membership_type = Column(String, nullable=True)
    billing_cycle = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    gstin = Column(String, nullable=True)
    
    # CRM Lead Fields
    spaceType = Column(String, nullable=True)
    seatRangeMin = Column(Integer, nullable=True)
    seatRangeMax = Column(Integer, nullable=True)
    urgency = Column(String, nullable=True)
    location = Column(String, nullable=True)
    spaceId = Column(Integer, default=1)
    
    onboarding_active = Column(Boolean, default=False)
    onboarding_step = Column(String, default="full_name")
    onboarding_complete = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True) # UUID
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    conversations = relationship("Conversation", back_populates="session")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String, nullable=False) # "user" | "assistant"
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="conversations")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=True)
    membership_type = Column(String, nullable=True)
    billing_cycle = Column(String, nullable=True)
    status = Column(String, default="pending") # "pending" | "success" | "failed"
    txn_ref = Column(String, nullable=True)
    initiated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")
