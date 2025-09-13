"""
Health check router for CodeBuddy2API
"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import time
from typing import Dict, Any
import psutil
import os

from .auth import authenticate

router = APIRouter()
START_TIME = time.time()

@router.get("/health", response_model=Dict[str, Any])
async def health_check(_token: str = Depends(authenticate)):
    """健康检查端点"""
    process = psutil.Process(os.getpid())
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(interval=0.1),
    }