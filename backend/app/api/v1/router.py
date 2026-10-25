from fastapi import APIRouter

from app.api.v1.transactions import router as transactions_router
from app.api.v1.alerts import router as alerts_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(transactions_router)
api_router.include_router(alerts_router)
