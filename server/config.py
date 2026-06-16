import os

class Config:
    # إعدادات السيرفر
    SERVER_HOST = os.getenv("HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("PORT", 10000))
    
    # إعدادات Quotex
    QUOTEX_URL = "https://qxbroker.com"
    
    # إعدادات التداول
    MAX_CONSECUTIVE_WINS = 5      # عدد صفقات متتالية ربح يوقف
    MAX_CONSECUTIVE_LOSSES = 2    # عدد صفقات متتالية خسارة يوقف
    
    # إعدادات التحليل
    TIMEFRAMES = ["1m", "5m", "15m", "1h"]
    STRATEGIES_COUNT = 4
    
    # مسارات الملفات
    DATABASE_PATH = "trading.db"
    LOGS_PATH = "logs/"

config = Config()
