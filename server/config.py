import os

class Config:
    SERVER_HOST = os.getenv("HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("PORT", 10000))
    QUOTEX_URL = "https://qxbroker.com"
    MAX_CONSECUTIVE_WINS = 5
    MAX_CONSECUTIVE_LOSSES = 2
    TIMEFRAMES = ["1m", "5m", "15m", "1h"]
    STRATEGIES_COUNT = 4
    DATABASE_PATH = "trading.db"
    LOGS_PATH = "logs/"

config = Config()
