from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .routers import products_router, orders_router, payments_router, admin_router, auth_router
from .seed import seed_default_users

app = FastAPI(title="FlashOrder Portal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(products_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    from .database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await seed_default_users(session)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {"message": "Welcome to FlashOrder API"}
