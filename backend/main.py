from fastapi import FastAPI
from backend.db.database import engine, Base
from backend.routers import auth, chat, payment, whatsapp

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cowork Assistant API")

from fastapi.staticfiles import StaticFiles

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(payment.router)
app.include_router(whatsapp.router)

app.mount("/images", StaticFiles(directory="backend/db/images"), name="images")

@app.get("/")
def read_root():
    return {"message": "Cowork Assistant API is running"}
