from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import time
from contextlib import asynccontextmanager

from quotex_sim import QuotexSim
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = QuotexSim()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Alking-Pro Trading Server")
    yield
    logger.info("🛑 Shutting down...")
    bot.close()

app = FastAPI(
    title="Alking-Pro Trading API",
    description="تداول آلي على منصة Quotex مع تحليل 4 استراتيجيات",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str

class TradeRequest(BaseModel):
    symbol: str
    amount: float
    is_demo: bool = True

@app.get("/")
async def root():
    return {
        "server": "Alking-Pro Trading Server",
        "status": "running",
        "platform": "Quotex",
        "version": "1.0.0",
        "features": [
            "تسجيل الدخول التلقائي",
            "تحليل 4 استراتيجيات",
            "صفقات حقيقية",
            "إيقاف تلقائي بعد 5 أرباح أو خسارتين"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "bot_logged_in": bot.is_logged_in,
        "bot_paused": bot.is_paused
    }

@app.post("/api/login")
async def login(request: LoginRequest):
    logger.info(f"Login attempt: {request.email}")
    result = bot.login(request.email, request.password)
    if result["success"]:
        return JSONResponse(content=result)
    else:
        raise HTTPException(status_code=401, detail=result["message"])

@app.get("/api/symbols")
async def get_symbols():
    if not bot.is_logged_in:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول أولاً")
    return {
        "success": True,
        "symbols": bot.current_symbols,
        "count": len(bot.current_symbols)
    }

@app.post("/api/trade/analyze")
async def analyze_only(request: TradeRequest):
    if not bot.is_logged_in:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول أولاً")
    close_prices, volumes = bot.get_candles(request.symbol)
    analysis = bot.strategies.analyze_all(close_prices, volumes)
    return {
        "success": True,
        "symbol": request.symbol,
        "analysis": analysis,
        "candles_count": len(close_prices)
    }

@app.post("/api/trade/execute")
async def execute_trade(request: TradeRequest):
    if not bot.is_logged_in:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول أولاً")
    result = bot.analyze_and_trade(request.symbol, request.amount, request.is_demo)
    return JSONResponse(content=result)

@app.post("/api/trade/reset")
async def reset_trading():
    result = bot.reset_pause()
    return JSONResponse(content=result)

@app.get("/api/status")
async def get_status():
    return bot.get_status()

@app.get("/api/stats")
async def get_stats():
    return {
        "total_trades": 0,
        "win_rate": 0,
        "total_profit": 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.SERVER_PORT)
