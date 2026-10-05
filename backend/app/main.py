from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import auth_router, users_router
from .routes.admin import router as admin_router
from .routes.bookings import router as bookings_router
from .routes.reports import router as reports_router
from .routes.trains import router as trains_router
from .routes.wallet import router as wallet_router

app = FastAPI(title="Train Booking System API", version="0.7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(trains_router)
app.include_router(bookings_router)
app.include_router(wallet_router)
app.include_router(reports_router)
app.include_router(admin_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "train-booking-system-api"}


@app.get("/")
def root():
    return {"message": "Train Booking System API is running"}
