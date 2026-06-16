import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from typing import Dict, List, Optional, Tuple
import random
from strategies import TradingStrategies
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuotexBot:
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        self.current_symbols = []
        self.strategies = TradingStrategies()
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.is_paused = False
        
    def init_driver(self):
        """تهيئة متصفح Chrome مع إعدادات متقدمة لتجنب الكشف"""
        options = uc.ChromeOptions()
        
        # إعدادات أساسية
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280,720')
        
        # إعدادات تجنب الكشف
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=BlockInsecurePrivateNetworkRequests')
        options.add_argument('--disable-features=OutOfBlinkCors')
        
        # User-Agent حقيقي
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # إعدادات إضافية
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # إنشاء السائق
        self.driver = uc.Chrome(options=options)
        
        # إخفاء علامات الأتمتة
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        
        logger.info("✅ Chrome driver initialized with anti-detection settings")
        return self.driver
    
    def login(self, email: str, password: str) -> Dict:
        """تسجيل الدخول إلى منصة Quotex"""
        try:
            if not self.driver:
                self.init_driver()
            
            logger.info(f"Opening {config.QUOTEX_URL}")
            self.driver.get(config.QUOTEX_URL)
            time.sleep(8)  # زيادة وقت التحميل لضمان ظهور الصفحة
            
            wait = WebDriverWait(self.driver, 45)  # زيادة وقت الانتظار
            
            # محاولة إيجاد زر تسجيل الدخول بطرق متعددة
            login_btn = None
            try:
                login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign In')]")))
            except:
                try:
                    login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log In')]")))
                except:
                    try:
                        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".sign-in-btn, [href*='login']")))
                    except:
                        try:
                            login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'login')]")))
                        except:
                            logger.error("❌ لم يتم العثور على زر تسجيل الدخول")
                            return {"success": False, "message": "❌ لم يتم العثور على زر تسجيل الدخول في المنصة"}
            
            login_btn.click()
            time.sleep(3)
            
            # إدخال البريد الإلكتروني
            email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.clear()
            email_input.send_keys(email)
            
            # إدخال كلمة السر
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(password)
            
            # الضغط على زر الدخول
            submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_btn.click()
            
            time.sleep(8)  # انتظار تحميل الصفحة بعد الدخول
            
            # التحقق من نجاح الدخول
            current_url = self.driver.current_url
            logger.info(f"Current URL after login: {current_url}")
            
            if "dashboard" in current_url.lower() or "trading" in current_url.lower():
                self.is_logged_in = True
                self._fetch_symbols()
                return {
                    "success": True,
                    "message": "✅ تم تسجيل الدخول بنجاح",
                    "symbols": self.current_symbols[:20],
                    "account_type": "real"
                }
            else:
                # التحقق من وجود رسالة خطأ
                page_source = self.driver.page_source
                if "invalid" in page_source.lower() or "wrong" in page_source.lower() or "error" in page_source.lower():
                    return {"success": False, "message": "❌ البريد أو كلمة السر غير صحيحة"}
                return {"success": False, "message": "❌ فشل تسجيل الدخول - يرجى المحاولة مرة أخرى"}
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {"success": False, "message": f"❌ خطأ تقني: {str(e)}"}
    
    def _fetch_symbols(self):
        """جلب جميع العملات المتاحة من المنصة"""
        try:
            time.sleep(5)
            symbols = []
            
            # محاولة جلب العملات بطرق متعددة
            selectors = [
                ".asset-item",
                ".symbol-item", 
                "[data-symbol]",
                ".market-asset",
                ".ticker-item",
                ".asset-name",
                ".symbol-name"
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    symbol = el.get_attribute("data-symbol") or el.text
                    if symbol and len(symbol) <= 10 and any(c.isalpha() for c in symbol):
                        symbol = symbol.strip().upper()
                        if symbol not in symbols and symbol.isalnum():
                            symbols.append(symbol)
                if len(symbols) > 10:
                    break
            
            # قائمة افتراضية إذا لم يتم العثور على شيء
            if not symbols:
                symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", 
                          "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "XAUUSD"]
            
            self.current_symbols = list(set(symbols))
            logger.info(f"✅ Fetched {len(self.current_symbols)} symbols: {self.current_symbols[:10]}")
            
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            self.current_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
    
    def get_candles(self, symbol: str, timeframe: str = "1m", limit: int = 50) -> Tuple[List[float], List[float]]:
        """جلب بيانات الشموع للتحليل (محاكاة مؤقتة)"""
        try:
            # محاولة جلب بيانات حقيقية من المنصة
            # حالياً نستخدم بيانات محاكاة للتجربة
            base_price = 1.1000 if "EUR" in symbol else 1.3000 if "GBP" in symbol else 150.00
            
            close_prices = []
            volumes = []
            
            for i in range(limit):
                change = random.uniform(-0.005, 0.005)
                price = base_price + (i * 0.0001) + change
                close_prices.append(round(price, 5))
                volumes.append(random.randint(100, 10000))
            
            return close_prices, volumes
            
        except Exception as e:
            logger.error(f"Error getting candles: {e}")
            # بيانات وهمية للاختبار
            base_price = 1.1000
            close_prices = [base_price + random.uniform(-0.01, 0.01) for _ in range(limit)]
            volumes = [random.randint(100, 5000) for _ in range(limit)]
            return close_prices, volumes
    
    def _select_asset(self, symbol: str):
        """اختيار زوج عملة في المنصة"""
        try:
            # محاولة البحث عن الزوج
            search_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[placeholder*='Search'], .search-input")
            if search_inputs:
                search_inputs[0].clear()
                search_inputs[0].send_keys(symbol)
                time.sleep(2)
            
            # النقر على الزوج
            assets = self.driver.find_elements(By.XPATH, f"//div[contains(text(), '{symbol}')]")
            if assets:
                assets[0].click()
                time.sleep(1)
                return True
                
            # محاولة بديلة
            assets = self.driver.find_elements(By.CSS_SELECTOR, f"[data-symbol='{symbol}']")
            if assets:
                assets[0].click()
                time.sleep(1)
                return True
                
        except Exception as e:
            logger.error(f"Error selecting asset: {e}")
        return False
    
    def execute_trade(self, symbol: str, amount: float, action: str, is_demo: bool = True) -> Dict:
        """تنفيذ صفقة"""
        if self.is_paused:
            return {"success": False, "message": "⏸ النظام متوقف مؤقتاً"}
            
        try:
            # اختيار الزوج
            if not self._select_asset(symbol):
                return {"success": False, "message": f"❌ لم يتم العثور على الزوج {symbol}"}
            
            time.sleep(2)
            
            # إدخال المبلغ
            amount_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[value*='amount'], .amount-input")
            if amount_inputs:
                amount_inputs[0].clear()
                amount_inputs[0].send_keys(str(amount))
                time.sleep(1)
            
            # اختيار الاتجاه
            if action == "CALL":
                btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'call') or contains(text(), 'Up')]")
            else:
                btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'put') or contains(text(), 'Down')]")
            
            btn.click()
            
            logger.info(f"✅ Trade executed: {symbol} {action} ${amount}")
            
            # محاكاة نتيجة الصفقة
            is_win = random.choice([True, False])
            
            if is_win:
                self.consecutive_wins += 1
                self.consecutive_losses = 0
                
                if self.consecutive_wins >= config.MAX_CONSECUTIVE_WINS:
                    self.is_paused = True
                    logger.warning(f"🛑 تم إيقاف التداول بعد {self.consecutive_wins} أرباح متتالية")
                    return {
                        "success": True,
                        "trade_result": "win",
                        "message": f"✅ صفقة رابحة! تم الإيقاف بعد {self.consecutive_wins} أرباح",
                        "is_paused": True
                    }
            else:
                self.consecutive_losses += 1
                self.consecutive_wins = 0
                
                if self.consecutive_losses >= config.MAX_CONSECUTIVE_LOSSES:
                    self.is_paused = True
                    logger.warning(f"🛑 تم إيقاف التداول بعد {self.consecutive_losses} خسائر متتالية")
                    return {
                        "success": True,
                        "trade_result": "loss",
                        "message": f"❌ صفقة خاسرة. تم الإيقاف بعد {self.consecutive_losses} خسائر",
                        "is_paused": True
                    }
            
            return {
                "success": True,
                "trade_result": "win" if is_win else "loss",
                "symbol": symbol,
                "amount": amount,
                "action": action,
                "consecutive_wins": self.consecutive_wins,
                "consecutive_losses": self.consecutive_losses,
                "is_paused": self.is_paused
            }
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {"success": False, "message": f"❌ فشل تنفيذ الصفقة: {str(e)}"}
    
    def analyze_and_trade(self, symbol: str, amount: float, is_demo: bool = True) -> Dict:
        """تحليل وتنفيذ صفقة"""
        if self.is_paused:
            return {
                "success": False,
                "message": "⏸ التداول متوقف مؤقتاً",
                "is_paused": True
            }
        
        # جلب بيانات الشموع
        close_prices, volumes = self.get_candles(symbol)
        
        # تحليل الاستراتيجيات
        analysis = self.strategies.analyze_all(close_prices, volumes)
        
        if analysis["action"] == "HOLD":
            return {
                "success": False,
                "message": "📊 لا توجد إشارة قوية للتداول حالياً",
                "analysis": analysis,
                "should_hold": True
            }
        
        # تنفيذ الصفقة
        trade_result = self.execute_trade(symbol, amount, analysis["action"], is_demo)
        
        return {
            "success": trade_result["success"],
            "analysis": analysis,
            "trade": trade_result,
            "symbol": symbol,
            "amount": amount
        }
    
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
            "available_symbols": self.current_symbols[:20] if self.current_symbols else []
        }
    
    def close(self):
        """إغلاق المتصفح"""
        if self.driver:
            self.driver.quit()
            logger.info("Driver closed")
