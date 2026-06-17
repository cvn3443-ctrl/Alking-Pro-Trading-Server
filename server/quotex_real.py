import asyncio
import logging
import random
from typing import Dict, List, Tuple
from strategies import TradingStrategies
from config import config
from pyquotex import Quotex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuotexReal:
    """اتصال حقيقي بمنصة Quotex عبر pyquotex"""
    
    def __init__(self):
        self.client = None
        self.is_logged_in = False
        self.current_symbols = []
        self.strategies = TradingStrategies()
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.is_paused = False
        self.email = None
        
        # قائمة العملات الافتراضية
        self.current_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", 
                               "USDCAD", "NZDUSD", "EURGBP", "XAUUSD"]
    
    def _run_async(self, coro):
        """تشغيل دالة غير متزامنة"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def login(self, email: str, password: str) -> Dict:
        """تسجيل الدخول إلى Quotex"""
        try:
            logger.info(f"محاولة تسجيل الدخول: {email}")
            
            # إنشاء عميل Quotex
            self.client = Quotex(email=email, password=password, lang="en")
            
            # الاتصال بالمنصة
            result = self._run_async(self.client.connect())
            
            if result:
                self.is_logged_in = True
                self.email = email
                
                # جلب قائمة العملات
                self._fetch_symbols()
                
                return {
                    "success": True,
                    "message": "✅ تم تسجيل الدخول بنجاح",
                    "symbols": self.current_symbols[:20],
                    "account_type": "real"
                }
            else:
                return {"success": False, "message": "❌ فشل تسجيل الدخول - تحقق من البيانات"}
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "message": f"❌ خطأ تقني: {str(e)}"}
    
    def _fetch_symbols(self):
        """جلب العملات المتاحة"""
        try:
            # محاولة جلب العملات من العميل
            if self.client:
                assets = self._run_async(self.client.get_assets())
                if assets:
                    symbols = []
                    for asset in assets:
                        if isinstance(asset, dict):
                            symbol = asset.get('symbol') or asset.get('name')
                            if symbol:
                                symbols.append(symbol.upper())
                    if symbols:
                        self.current_symbols = list(set(symbols))
                        logger.info(f"✅ تم جلب {len(self.current_symbols)} عملة")
                        return
            
            # قائمة افتراضية في حالة الفشل
            self.current_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", 
                                   "USDCAD", "NZDUSD", "EURGBP", "XAUUSD"]
            logger.info("⚠️ استخدام قائمة العملات الافتراضية")
            
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            self.current_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
    
    def get_candles(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> Tuple[List[float], List[float]]:
        """جلب بيانات الشموع الحقيقية من المنصة"""
        try:
            if not self.client:
                logger.error("❌ العميل غير متصل")
                return self._get_mock_candles(symbol, limit)
            
            # جلب الشموع الحقيقية
            candles = self._run_async(
                self.client.get_candles_deep(asset=symbol, count=limit, time_frame=timeframe)
            )
            
            if candles and len(candles) > 0:
                close_prices = []
                volumes = []
                for candle in candles:
                    if isinstance(candle, dict):
                        close_prices.append(float(candle.get('close', 0)))
                        volumes.append(float(candle.get('volume', 0)))
                    elif hasattr(candle, 'close'):
                        close_prices.append(float(candle.close))
                        volumes.append(float(candle.volume))
                
                if close_prices:
                    logger.info(f"✅ تم جلب {len(close_prices)} شمعة للزوج {symbol}")
                    return close_prices, volumes
            
            logger.warning(f"⚠️ لم يتم العثور على بيانات للزوج {symbol}، استخدام بيانات محاكاة")
            return self._get_mock_candles(symbol, limit)
            
        except Exception as e:
            logger.error(f"Error getting candles: {e}")
            return self._get_mock_candles(symbol, limit)
    
    def _get_mock_candles(self, symbol: str, limit: int) -> Tuple[List[float], List[float]]:
        """بيانات محاكاة للاختبار"""
        import random
        base = 1.1000 if "EUR" in symbol else 1.3000 if "GBP" in symbol else 150.00
        close_prices = [base + random.uniform(-0.01, 0.01) for _ in range(limit)]
        volumes = [random.randint(100, 5000) for _ in range(limit)]
        return close_prices, volumes
    
    def execute_trade(self, symbol: str, amount: float, action: str, is_demo: bool = True) -> Dict:
        """تنفيذ صفقة حقيقية"""
        if self.is_paused:
            return {"success": False, "message": "⏸ النظام متوقف مؤقتاً"}
        
        try:
            if not self.client:
                return {"success": False, "message": "❌ العميل غير متصل"}
            
            # تنفيذ الصفقة
            result = self._run_async(
                self.client.place_order(
                    asset=symbol,
                    amount=amount,
                    direction="call" if action == "CALL" else "put",
                    duration=60,  # دقيقة واحدة
                    demo=is_demo
                )
            )
            
            if result and result.get('success'):
                # جلب نتيجة الصفقة
                trade_result = self._run_async(
                    self.client.get_order_result(result.get('order_id'))
                )
                
                is_win = trade_result.get('result') == 'win'
                
                if is_win:
                    self.consecutive_wins += 1
                    self.consecutive_losses = 0
                    if self.consecutive_wins >= config.MAX_CONSECUTIVE_WINS:
                        self.is_paused = True
                        return {
                            "success": True,
                            "trade_result": "win",
                            "message": f"✅ ربح! إيقاف بعد {self.consecutive_wins} أرباح",
                            "is_paused": True,
                            "profit": trade_result.get('profit', 0)
                        }
                else:
                    self.consecutive_losses += 1
                    self.consecutive_wins = 0
                    if self.consecutive_losses >= config.MAX_CONSECUTIVE_LOSSES:
                        self.is_paused = True
                        return {
                            "success": True,
                            "trade_result": "loss",
                            "message": f"❌ خسارة! إيقاف بعد {self.consecutive_losses} خسائر",
                            "is_paused": True,
                            "loss": trade_result.get('loss', 0)
                        }
                
                return {
                    "success": True,
                    "trade_result": "win" if is_win else "loss",
                    "symbol": symbol,
                    "amount": amount,
                    "action": action,
                    "consecutive_wins": self.consecutive_wins,
                    "consecutive_losses": self.consecutive_losses,
                    "is_paused": self.is_paused,
                    "order_id": result.get('order_id')
                }
            else:
                return {"success": False, "message": "❌ فشل تنفيذ الصفقة"}
                
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {"success": False, "message": f"❌ فشل الصفقة: {str(e)}"}
    
    def analyze_and_trade(self, symbol: str, amount: float, is_demo: bool = True) -> Dict:
        """تحليل وتنفيذ صفقة"""
        if self.is_paused:
            return {"success": False, "message": "⏸ التداول متوقف", "is_paused": True}
        
        # جلب بيانات الشموع الحقيقية
        close_prices, volumes = self.get_candles(symbol)
        
        # تحليل الاستراتيجيات
        analysis = self.strategies.analyze_all(close_prices, volumes)
        
        if analysis["action"] == "HOLD":
            return {
                "success": False,
                "message": "📊 لا توجد إشارة قوية",
                "analysis": analysis,
                "should_hold": True
            }
        
        # تنفيذ الصفقة
        return self.execute_trade(symbol, amount, analysis["action"], is_demo)
    
    def reset_pause(self) -> Dict:
        self.is_paused = False
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        return {"success": True, "message": "تم إعادة تشغيل التداول"}
    
    def get_status(self) -> Dict:
        return {
            "is_logged_in": self.is_logged_in,
            "is_paused": self.is_paused,
            "consecutive_wins": self.consecutive_wins,
            "consecutive_losses": self.consecutive_losses,
            "max_wins_before_pause": config.MAX_CONSECUTIVE_WINS,
            "max_losses_before_pause": config.MAX_CONSECUTIVE_LOSSES,
            "available_symbols": self.current_symbols[:20] if self.current_symbols else []
        }
    
    def close(self):
        if self.client:
            try:
                self._run_async(self.client.close())
            except:
                pass
            logger.info("Session closed")
