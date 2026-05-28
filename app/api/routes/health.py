# -*- coding: utf-8 -*-
"""Health Check Route."""

from fastapi import APIRouter

from app.core.config import cfg

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "app": cfg.app_name,
        "version": cfg.app_version,
    }
