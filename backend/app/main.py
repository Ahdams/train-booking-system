from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import auth_router, users_router

app = FastAPI(title="Train Booking System API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "train-booking-system-api"}


@app.get("/")
def root():
    return {"message": "Train Booking System API is running"}
