import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_ID = os.getenv("MODEL_ID", "mistralai/mistral-7b-instruct")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./backend/db/cowork.db")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./backend/db/chroma")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-jwt-key-replace-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week
CRM_API = os.getenv("CRM_API", "")
SARVAM_API = os.getenv("SARVAM_API", "")

DATABASE_URL = os.getenv("DATABASE_URL", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
