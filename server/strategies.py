import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

class TradingStrategies:
    """أربع استراتيجيات تحليل متزامنة"""
    
    @staticmethod
    def sma_crossover(close_prices: List[float]) -> Dict:
        """الاستراتيجية 1: تقاطع المتوسطات المتحركة (SMA 9 و SMA 21)"""
        if len(close_prices) < 21:
            return {"signal": 0, "confidence": 0, "name": "SMA Crossover"}
        
        sma_9 = np.mean(close_prices[-9:])
        sma_21 = np.mean(close_prices[-21:])
        
        if sma_9 > sma_21:
            return {"signal": 1, "confidence": 0.75, "name": "SMA Crossover"}
        elif sma_9 < sma_21:
            return {"signal": -1, "confidence": 0.75, "name": "SMA Crossover"}
        return {"signal": 0, "confidence": 0, "name": "SMA Crossover"}
    
    @staticmethod
    def rsi_analysis(close_prices: List[float], period: int = 14) -> Dict:
        """الاستراتيجية 2: تحليل مؤشر القوة النسبية RSI"""
        if len(close_prices) < period + 1:
            return {"signal": 0, "confidence": 0, "name": "RSI"}
        
        deltas = np.diff(close_prices[-period-1:])
        gains = deltas[deltas > 0].sum() / period
        losses = abs(deltas[deltas < 0].sum()) / period
        
        if losses == 0:
            rsi = 100
        else:
            rs = gains / losses
            rsi = 100 - (100 / (1 + rs))
        
        if rsi < 30:
            return {"signal": 1, "confidence": 0.8, "name": "RSI"}
        elif rsi > 70:
            return {"signal": -1, "confidence": 0.8, "name": "RSI"}
        return {"signal": 0, "confidence": 0.3, "name": "RSI"}
    
    @staticmethod
    def bollinger_bands(close_prices: List[float], period: int = 20) -> Dict:
        """الاستراتيجية 3: نطاقات بولينجر Bollinger Bands"""
        if len(close_prices) < period:
            return {"signal": 0, "confidence": 0, "name": "Bollinger Bands"}
        
        prices = np.array(close_prices[-period:])
        sma = np.mean(prices)
        std = np.std(prices)
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        current_price = close_prices[-1]
        
        if current_price <= lower_band:
            return {"signal": 1, "confidence": 0.7, "name": "Bollinger Bands"}
        elif current_price >= upper_band:
            return {"signal": -1, "confidence": 0.7, "name": "Bollinger Bands"}
        return {"signal": 0, "confidence": 0.2, "name": "Bollinger Bands"}
    
    @staticmethod
    def volume_spike(volumes: List[float], close_prices: List[float]) -> Dict:
        """الاستراتيجية 4: تحليل حجم التداول Volume Spike"""
        if len(volumes) < 10 or len(close_prices) < 2:
            return {"signal": 0, "confidence": 0, "name": "Volume Spike"}
        
        avg_volume = np.mean(volumes[-10:])
        current_volume = volumes[-1]
        price_change = close_prices[-1] - close_prices[-2]
        
        if current_volume > avg_volume * 1.5 and price_change > 0:
            return {"signal": 1, "confidence": 0.65, "name": "Volume Spike"}
        elif current_volume > avg_volume * 1.5 and price_change < 0:
            return {"signal": -1, "confidence": 0.65, "name": "Volume Spike"}
        return {"signal": 0, "confidence": 0.1, "name": "Volume Spike"}
    
    def analyze_all(self, close_prices: List[float], volumes: List[float]) -> Dict:
        """تحليل جميع الاستراتيجيات الأربع معاً"""
        results = []
        total_confidence = 0
        total_signal = 0
        
        # تنفيذ الاستراتيجيات الأربع
        strategies = [
            self.sma_crossover(close_prices),
            self.rsi_analysis(close_prices),
            self.bollinger_bands(close_prices),
            self.volume_spike(volumes, close_prices)
        ]
        
        for strategy in strategies:
            results.append(strategy)
            total_signal += strategy["signal"] * strategy["confidence"]
            total_confidence += strategy["confidence"]
        
        # الإشارة النهائية (متوسط مرجح)
        final_signal = total_signal / total_confidence if total_confidence > 0 else 0
        
        # تحديد الاتجاه
        if final_signal > 0.3:
            action = "CALL"  # شراء (ارتفاع)
        elif final_signal < -0.3:
            action = "PUT"   # بيع (انخفاض)
        else:
            action = "HOLD"  # انتظار
        
        return {
            "action": action,
            "final_signal": float(final_signal),
            "strategies_results": results,
            "strength": abs(final_signal)
  }
