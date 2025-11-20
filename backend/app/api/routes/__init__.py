"""Aggregate API routers."""

from fastapi import APIRouter

from app.api.routes import admin, ledger, transactions, users

router = APIRouter(prefix="/api")
router.include_router(users.router)
router.include_router(transactions.router)
router.include_router(ledger.router, prefix="/ledger")
router.include_router(admin.router)
