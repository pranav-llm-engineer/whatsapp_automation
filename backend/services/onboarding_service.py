from sqlalchemy.orm import Session
from backend.db.models import UserProfile
import re

FIELDS = [
    "full_name", "spaceType", "seatRange", "location"
]

def get_next_field(profile: UserProfile):
    return profile.onboarding_step

def advance_step(db: Session, profile: UserProfile):
    current_idx = FIELDS.index(profile.onboarding_step) if profile.onboarding_step in FIELDS else -1
    if current_idx + 1 < len(FIELDS):
        profile.onboarding_step = FIELDS[current_idx + 1]
    else:
        profile.onboarding_complete = True
    db.commit()

def validate_and_save(db: Session, profile: UserProfile, value: str) -> bool:
    field = profile.onboarding_step
    
    if field == "seatRange":
        # Extract numbers using regex
        nums = re.findall(r'\d+', value)
        if not nums:
            return False
        
        try:
            profile.seatRangeMin = int(nums[0])
            profile.seatRangeMax = int(nums[-1]) # works if 1 or more numbers
        except:
            return False
    else:
        # Save the value dynamically for other fields
        setattr(profile, field, value)
        
    advance_step(db, profile)
    return True

def update_profile_field(db: Session, profile: UserProfile, field: str, value: str):
    if field == "seatRange":
        nums = re.findall(r'\d+', str(value))
        if nums:
            profile.seatRangeMin = int(nums[0])
            profile.seatRangeMax = int(nums[-1])
    else:
        if hasattr(profile, field):
            setattr(profile, field, value)
    db.commit()
