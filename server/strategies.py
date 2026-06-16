from typing import Dict, List

class TradingStrategies:
    """أربع استراتيجيات تحليل متزامنة"""
    
    @staticmethod
    def sma_crossover(close_prices: List[float]) -> Dict:
        if len(close_prices) < 21:
            return {"signal": 0, "confidence": 0, "name": "SMA Crossover"}
        sma_9 = sum(close_prices[-9:]) / 9
        sma_21 = sum(close_prices[-21:]) / 21
        if sma_9 > sma_21:
            return {"signal": 1, "confidence": 0.75, "name": "SMA Crossover"}
        elif sma_9 < sma_21:
            return {"signal": -1, "confidence": 0.75, "name": "SMA Crossover"}
        return {"signal": 0, "confidence": 0, "name": "SMA Crossover"}
    
    @staticmethod
    def rsi_analysis(close_prices: List[float], period: int = 14) -> Dict:
        if len(close_prices) < period + 1:
            return {"signal": 0, "confidence": 0, "name": "RSI"}
        gains = []
        losses = []
        for i in range(-period, 0):
            diff = close_prices[i] - close_prices[i-1]
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 1
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        if rsi < 30:
            return {"signal": 1, "confidence": 0.8, "name": "RSI"}
        elif rsi > 70:
            return {"signal": -1, "confidence": 0.8, "name": "RSI"}
        return {"signal": 0, "confidence": 0.3, "name": "RSI"}
    
    @staticmethod
    def bollinger_bands(close_prices: List[float], period: int = 20) -> Dict:
        if len(close_prices) < period:
            return {"signal": 0, "confidence": 0, "name": "Bollinger Bands"}
        prices = close_prices[-period:]
        sma = sum(prices) / period
        variance = sum((x - sma) ** 2 for x in prices) / period
        std = variance ** 0.5
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
        if len(volumes) < 10 or len(close_prices) < 2:
            return {"signal": 0, "confidence": 0, "name": "Volume Spike"}
        avg_volume = sum(volumes[-10:]) / 10
        current_volume = volumes[-1]
        price_change = close_prices[-1] - close_prices[-2]
        if current_volume > avg_volume * 1.5 and price_change > 0:
            return {"signal": 1, "confidence": 0.65, "name": "Volume Spike"}
        elif current_volume > avg_volume * 1.5 and price_change < 0:
            return {"signal": -1, "confidence": 0.65, "name": "Volume Spike"}
        return {"signal": 0, "confidence": 0.1, "name": "Volume Spike"}
    
    def analyze_all(self, close_prices: List[float], volumes: List[float]) -> Dict:
        results = []
        total_confidence = 0
        total_signal = 0
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
        final_signal = total_signal / total_confidence if total_confidence > 0 else 0
        if final_signal > 0.3:
            action = "CALL"
        elif final_signal < -0.3:
            action = "PUT"
        else:
            action = "HOLD"
        return {
            "action": action,
            "final_signal": round(final_signal, 4),
            "strategies_results": results,
            "strength": round(abs(final_signal), 4)
                   }
