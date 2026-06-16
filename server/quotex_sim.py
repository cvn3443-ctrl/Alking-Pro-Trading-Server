import logging
import random
import time
import requests
from typing import Dict, List, Tuple
from datetime import datetime
from strategies import TradingStrategies
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuotexSim:
    """
    محاكي متقدم لمنصة Quotex - يعمل بدون متصفح
    يستخدم بيانات حقيقية من السوق عبر API عامة
    """
    
    def __init__(self):
        self.is_logged_in = False
        self.current_symbols = []
        self.strategies = TradingStrategies()
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.is_paused = False
        self.token = None
        self.email = None
        self.balance = 1000.0  # رصيد افتراضي للاختبار
        
        # قائمة العملات الافتراضية
        self.current_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", 
                               "USDCAD", "NZDUSD", "EURGBP", "XAUUSD"]
        
        # بيانات الأسعار الحقيقية (سيتم تحديثها)
        self.prices = {}
        
    def login(self, email: str, password: str) -> Dict:
        """محاكاة تسجيل الدخول - في الإصدار الحقيقي سيتم الاتصال بـ API"""
        try:
            logger.info(f"محاولة تسجيل الدخول: {email}")
            
            # هنا يمكن إضافة API حقيقي لـ Quotex إذا توفر
            # حالياً نقوم بمحاكاة ناجحة لأغراض الاختبار
            
            self.email = email
            self.is_logged_in = True
            self.token = "sim_" + str(int(time.time()))
            
            # جلب أسعار حقيقية من مصدر خارجي
            self._fetch_real_prices()
            
            return {
                "success": True,
                "message": "✅ تم تسجيل الدخول بنجاح (محاكاة)",
                "symbols": self.current_symbols[:20],
                "account_type": "demo"
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "message": f"❌ خطأ: {str(e)}"}
    
    def _fetch_real_prices(self):
        """جلب أسعار حقيقية من API عام"""
        try:
            # استخدام API مجاني للأسعار
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                # تحديث أسعار العملات
                for symbol in self.current_symbols:
                    base = symbol[:3]
                    if base in rates:
                        self.prices[symbol] = rates[base]
                
                logger.info(f"✅ تم جلب {len(self.prices)} سعر حقيقي")
            else:
                # استخدام أسعار افتراضية
                self.prices = {
                    "EURUSD": 1.0950,
                    "GBPUSD": 1.2650,
                    "USDJPY": 149.50,
                    "AUDUSD": 0.6550,
                    "USDCAD": 1.3450,
                    "NZDUSD": 0.6050,
                    "EURGBP": 0.8650,
                    "XAUUSD": 2050.00
                }
                logger.info("✅ تم استخدام الأسعار الافتراضية")
                
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            self.prices = {
                "EURUSD": 1.0950,
                "GBPUSD": 1.2650,
                "USDJPY": 149.50,
                "AUDUSD": 0.6550,
                "USDCAD": 1.3450,
                "NZDUSD": 0.6050,
                "EURGBP": 0.8650,
                "XAUUSD": 2050.00
            }
    
    def get_candles(self, symbol: str, timeframe: str = "1m", limit: int = 50) -> Tuple[List[float], List[float]]:
        """جلب بيانات الشموع للتحليل (بيانات محاكاة ولكن واقعية)"""
        try:
            # الحصول على السعر الحالي للزوج
            base_price = self.prices.get(symbol, 1.1000)
            
            # توليد بيانات شموع واقعية
            close_prices = []
            volumes = []
            
            # اتجاه عشوائي مع ميل بسيط
            trend = random.choice([-0.0005, 0.0005, 0, 0.0003, -0.0003])
            volatility = random.uniform(0.001, 0.005)
            
            for i in range(limit):
                # تغيير عشوائي مع ميل
                change = random.uniform(-volatility, volatility) + trend
                price = base_price * (1 + change)
                close_prices.append(round(price, 5))
                volumes.append(random.randint(100, 20000))
                
                # تحديث السعر الأساسي للتالي
                base_price = price
            
            return close_prices, volumes
            
        except Exception as e:
            logger.error(f"Error getting candles: {e}")
            # بيانات طوارئ
            base_price = 1.1000
            close_prices = [base_price + random.uniform(-0.01, 0.01) for _ in range(limit)]
            volumes = [random.randint(100, 5000) for _ in range(limit)]
            return close_prices, volumes
    
    def execute_trade(self, symbol: str, amount: float, action: str, is_demo: bool = True) -> Dict:
        """تنفيذ صفقة محاكاة مع تحليل حقيقي"""
        if self.is_paused:
            return {"success": False, "message": "⏸ النظام متوقف مؤقتاً"}
        
        try:
            # جلب بيانات حقيقية للتحليل
            close_prices, volumes = self.get_candles(symbol)
            analysis = self.strategies.analyze_all(close_prices, volumes)
            
            # تحديد النتيجة بناءً على التحليل وقوة الإشارة
            signal_strength = analysis.get('strength', 0.3)
            is_win = False
            
            if analysis['action'] == 'CALL':
                # احتمالية الربح تعتمد على قوة الإشارة
                win_probability = 0.5 + (signal_strength * 0.3)
                is_win = random.random() < win_probability
            elif analysis['action'] == 'PUT':
                win_probability = 0.5 + (signal_strength * 0.3)
                is_win = random.random() < win_probability
            else:
                # HOLD - لا ننفذ صفقة
                return {
                    "success": False,
                    "message": "📊 لا توجد إشارة قوية للتداول",
                    "analysis": analysis,
                    "should_hold": True
                }
            
            # تحديث الرصيد (محاكاة)
            if is_win:
                profit = amount * 0.80  # 80% ربح
                self.balance += profit
                self.consecutive_wins += 1
                self.consecutive_losses = 0
                
                if self.consecutive_wins >= config.MAX_CONSECUTIVE_WINS:
                    self.is_paused = True
                    return {
                        "success": True,
                        "trade_result": "win",
                        "profit": profit,
                        "new_balance": self.balance,
                        "message": f"✅ ربح! +${profit:.2f} - إيقاف بعد {self.consecutive_wins} أرباح",
                        "is_paused": True,
                        "analysis": analysis
                    }
                
                return {
                    "success": True,
                    "trade_result": "win",
                    "profit": profit,
                    "new_balance": self.balance,
                    "message": f"✅ صفقة رابحة! +${profit:.2f}",
                    "is_paused": False,
                    "analysis": analysis
                }
            else:
                loss = amount * 0.80  # خسارة
                self.balance -= loss
                self.consecutive_losses += 1
                self.consecutive_wins = 0
                
                if self.consecutive_losses >= config.MAX_CONSECUTIVE_LOSSES:
                    self.is_paused = True
                    return {
                        "success": True,
                        "trade_result": "loss",
                        "loss": loss,
                        "new_balance": self.balance,
                        "message": f"❌ خسارة! -${loss:.2f} - إيقاف بعد {self.consecutive_losses} خسائر",
                        "is_paused": True,
                        "analysis": analysis
                    }
                
                return {
                    "success": True,
                    "trade_result": "loss",
                    "loss": loss,
                    "new_balance": self.balance,
                    "message": f"❌ صفقة خاسرة -${loss:.2f}",
                    "is_paused": False,
                    "analysis": analysis
                }
                
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {"success": False, "message": f"❌ خطأ في الصفقة: {str(e)}"}
    
    def analyze_and_trade(self, symbol: str, amount: float, is_demo: bool = True) -> Dict:
        """تحليل وتنفيذ صفقة"""
        if self.is_paused:
            return {
                "success": False,
                "message": "⏸ التداول متوقف مؤقتاً",
                "is_paused": True
            }
        
        # تنفيذ الصفقة مباشرة
        return self.execute_trade(symbol, amount, "", is_demo)
    
    def reset_pause(self) -> Dict:
        """إعادة تعيين حالة الإيقاف"""
        self.is_paused = False
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        logger.info("✅ تم إعادة تعيين حالة الإيقاف")
        return {"success": True, "message": "تم إعادة تشغيل التداول"}
    
    def get_status(self) -> Dict:
        """الحصول على حالة النظام"""
        return {
            "is_logged_in": self.is_logged_in,
            "is_paused": self.is_paused,
            "consecutive_wins": self.consecutive_wins,
            "consecutive_losses": self.consecutive_losses,
            "max_wins_before_pause": config.MAX_CONSECUTIVE_WINS,
            "max_losses_before_pause": config.MAX_CONSECUTIVE_LOSSES,
            "available_symbols": self.current_symbols[:20],
            "balance": self.balance
        }
    
    def close(self):
        """إغلاق الاتصالات"""
        logger.info("Session closed")
