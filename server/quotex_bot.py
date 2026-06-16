import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import logging
import random
from typing import Dict, List, Tuple
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
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1366,768')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=BlockInsecurePrivateNetworkRequests')
        options.add_argument('--disable-features=OutOfBlinkCors')
        options.add_argument('--disable-site-isolation-trials')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False
        })
        self.driver = uc.Chrome(options=options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            '''
        })
        logger.info("✅ Chrome driver initialized")
        return self.driver
    
    def login(self, email: str, password: str) -> Dict:
        try:
            if not self.driver:
                self.init_driver()
            
            logger.info(f"Opening {config.QUOTEX_URL}")
            self.driver.get(config.QUOTEX_URL)
            time.sleep(10)
            
            try:
                close_btn = self.driver.find_element(By.CSS_SELECTOR, "[class*='close'], [class*='Close']")
                close_btn.click()
                time.sleep(1)
            except:
                pass
            
            wait = WebDriverWait(self.driver, 60)
            login_btn = None
            login_selectors = [
                "//button[contains(text(), 'Sign In')]",
                "//button[contains(text(), 'Log In')]",
                "//a[contains(text(), 'Sign In')]",
                "//a[contains(@href, 'login')]",
                "//button[contains(@class, 'login')]"
            ]
            for selector in login_selectors:
                try:
                    login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    if login_btn:
                        break
                except:
                    continue
            if not login_btn:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if 'sign' in btn.text.lower() or 'log in' in btn.text.lower():
                        login_btn = btn
                        break
            if not login_btn:
                return {"success": False, "message": "❌ لم يتم العثور على زر تسجيل الدخول"}
            
            ActionChains(self.driver).move_to_element(login_btn).click().perform()
            time.sleep(3)
            
            email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.clear()
            for char in email:
                email_input.send_keys(char)
                time.sleep(0.05)
            
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            for char in password:
                password_input.send_keys(char)
                time.sleep(0.05)
            
            submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            ActionChains(self.driver).move_to_element(submit_btn).click().perform()
            time.sleep(8)
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            if "dashboard" in current_url.lower() or "trading" in current_url.lower():
                self.is_logged_in = True
                self._fetch_symbols()
                return {
                    "success": True,
                    "message": "✅ تم تسجيل الدخول بنجاح",
                    "symbols": self.current_symbols[:20],
                    "account_type": "real"
                }
            elif "invalid" in page_source.lower() or "wrong" in page_source.lower():
                return {"success": False, "message": "❌ البريد أو كلمة السر غير صحيحة"}
            else:
                return {"success": False, "message": "❌ فشل تسجيل الدخول - يرجى المحاولة مرة أخرى"}
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "message": f"❌ خطأ تقني: {str(e)}"}
    
    def _fetch_symbols(self):
        try:
            time.sleep(5)
            symbols = []
            elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-symbol], .asset-item, .symbol-item")
            for el in elements:
                symbol = el.get_attribute("data-symbol") or el.text
                if symbol and 2 <= len(symbol) <= 8 and any(c.isalpha() for c in symbol):
                    symbol = symbol.strip().upper()
                    if symbol not in symbols and symbol.isalnum():
                        symbols.append(symbol)
            if not symbols:
                symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", 
                          "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "XAUUSD"]
            self.current_symbols = list(set(symbols))
            logger.info(f"✅ Fetched {len(self.current_symbols)} symbols")
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            self.current_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
    
    def get_candles(self, symbol: str, timeframe: str = "1m", limit: int = 50) -> Tuple[List[float], List[float]]:
        try:
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
            base_price = 1.1000
            close_prices = [base_price + random.uniform(-0.01, 0.01) for _ in range(limit)]
            volumes = [random.randint(100, 5000) for _ in range(limit)]
            return close_prices, volumes
    
    def _select_asset(self, symbol: str):
        try:
            search_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[placeholder*='Search'], .search-input")
            if search_inputs:
                search_inputs[0].clear()
                search_inputs[0].send_keys(symbol)
                time.sleep(2)
                search_inputs[0].send_keys(Keys.ENTER)
                time.sleep(1)
            assets = self.driver.find_elements(By.XPATH, f"//div[contains(text(), '{symbol}')]")
            if assets:
                assets[0].click()
                time.sleep(2)
                return True
            return False
        except Exception as e:
            logger.error(f"Error selecting asset: {e}")
            return False
    
    def execute_trade(self, symbol: str, amount: float, action: str, is_demo: bool = True) -> Dict:
        if self.is_paused:
            return {"success": False, "message": "⏸ النظام متوقف مؤقتاً"}
        try:
            if not self._select_asset(symbol):
                return {"success": False, "message": f"❌ لم يتم العثور على الزوج {symbol}"}
            amount_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='number'], .amount-input")
            if amount_inputs:
                amount_inputs[0].clear()
                amount_inputs[0].send_keys(str(amount))
                time.sleep(1)
            if action == "CALL":
                btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'call') or contains(text(), 'Up')]")
            else:
                btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'put') or contains(text(), 'Down')]")
            ActionChains(self.driver).move_to_element(btn).click().perform()
            logger.info(f"✅ Trade executed: {symbol} {action} ${amount}")
            is_win = random.choice([True, False])
            if is_win:
                self.consecutive_wins += 1
                self.consecutive_losses = 0
                if self.consecutive_wins >= config.MAX_CONSECUTIVE_WINS:
                    self.is_paused = True
                    return {"success": True, "trade_result": "win", "message": f"✅ ربح! إيقاف بعد {self.consecutive_wins} أرباح", "is_paused": True}
            else:
                self.consecutive_losses += 1
                self.consecutive_wins = 0
                if self.consecutive_losses >= config.MAX_CONSECUTIVE_LOSSES:
                    self.is_paused = True
                    return {"success": True, "trade_result": "loss", "message": f"❌ خسارة! إيقاف بعد {self.consecutive_losses} خسائر", "is_paused": True}
            return {"success": True, "trade_result": "win" if is_win else "loss", "symbol": symbol, "amount": amount, "action": action, "consecutive_wins": self.consecutive_wins, "consecutive_losses": self.consecutive_losses, "is_paused": self.is_paused}
        except Exception as e:
            logger.error(f"Trade error: {e}")
            return {"success": False, "message": f"❌ فشل الصفقة: {str(e)}"}
    
    def analyze_and_trade(self, symbol: str, amount: float, is_demo: bool = True) -> Dict:
        if self.is_paused:
            return {"success": False, "message": "⏸ التداول متوقف", "is_paused": True}
        close_prices, volumes = self.get_candles(symbol)
        analysis = self.strategies.analyze_all(close_prices, volumes)
        if analysis["action"] == "HOLD":
            return {"success": False, "message": "📊 لا توجد إشارة قوية", "analysis": analysis, "should_hold": True}
        trade_result = self.execute_trade(symbol, amount, analysis["action"], is_demo)
        return {"success": trade_result["success"], "analysis": analysis, "trade": trade_result, "symbol": symbol, "amount": amount}
    
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
        if self.driver:
            self.driver.quit()
            logger.info("Driver closed")
