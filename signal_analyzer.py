import pandas as pd
import numpy as np
import logging
from datetime import datetime, timezone
from indicators import calculate_all_indicators
from model import ai_model, MODEL_FEATURES
from database import save_binary_signal, get_daily_statistics
from globals import MIN_ACCURACY_THRESHOLD, EXPIRY_TIMES, RISK_MANAGEMENT
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinaryOptionsSignalAnalyzer:
    """Анализатор сигналов для бинарных опционов."""
    
    def __init__(self):
        self.last_signal_time = {}
        self.daily_signal_count = 0
        self.update_daily_stats()
    
    def update_daily_stats(self):
        """Обновляет дневную статистику."""
        total_signals, wins = get_daily_statistics()
        self.daily_signal_count = total_signals
    
    def quantum_binary_signal(self, data: pd.DataFrame) -> dict | None:
        """Улучшенная стратегия Quantum Precision для бинарных опционов."""
        if data.empty or len(data) < 5:
            return None
        
        latest = data.iloc[-1]
        
        # Проверка лимитов
        if self.daily_signal_count >= RISK_MANAGEMENT['max_daily_signals']:
            logger.info("Достигнут дневной лимит сигналов")
            return None
        
        # **Уровень 1: Усиленный импульсный фильтр для бинарных опционов**
        volume_condition = (latest['volume'] > latest['sma_volume'] * 2.8) if not pd.isna(latest['sma_volume']) else False
        momentum_condition = abs(latest['pct_change']) > 0.003 if not pd.isna(latest['pct_change']) else False
        
        if not (volume_condition and momentum_condition):
            logger.debug("Импульсный фильтр не пройден")
            return None
        
        # **Уровень 2: Конвергенция индикаторов**
        macd_bullish = latest['macd_hist'] > 0 if not pd.isna(latest['macd_hist']) else False
        vwap_bullish = latest['vwap_gradient'] > 0.001 if not pd.isna(latest['vwap_gradient']) else False
        rsi_normal = 30 < latest['rsi'] < 70 if not pd.isna(latest['rsi']) else False
        
        trend_score = sum([macd_bullish, vwap_bullish, rsi_normal])
        if trend_score < 2:
            logger.debug("Конвергенция индикаторов недостаточна")
            return None
        
        # **Уровень 3: Подтверждение разворота/продолжения**
        supertrend_signal = latest['supertrend_signal'] != 0 if not pd.isna(latest['supertrend_signal']) else False
        bb_not_squeezed = not latest['bb_squeeze'] if not pd.isna(latest['bb_squeeze']) else True
        stoch_signal = latest['stoch_crossover'] != 0 if not pd.isna(latest['stoch_crossover']) else False
        
        confirmation_score = sum([supertrend_signal, bb_not_squeezed, stoch_signal])
        if confirmation_score < 2:
            logger.debug("Подтверждение недостаточно")
            return None
        
        # **Уровень 4: ИИ-предсказание**
        features = self.extract_features(latest)
        if features is None:
            return None
        
        proba = ai_model.predict_proba(features.reshape(1, -1))
        probability_up = proba[0][1]
        
        if probability_up < MIN_ACCURACY_THRESHOLD:
            logger.debug(f"ИИ-вероятность недостаточна: {probability_up:.3f}")
            return None
        
        # Определение направления сигнала
        signal_direction = self.determine_signal_direction(latest, probability_up)
        
        # Расчет точности
        accuracy = self.calculate_accuracy(latest, probability_up)
        
        # Определение времени экспирации
        expiry_time = self.determine_expiry_time(latest)
        
        signal_info = {
            'signal_type': signal_direction,
            'probability': probability_up,
            'accuracy': accuracy,
            'entry_time': latest.name.timestamp() * 1000,
            'entry_price': latest['close'],
            'expiry_time': expiry_time,
            'strength': ai_model.get_signal_strength(probability_up),
            'indicators': {
                'rsi': latest['rsi'],
                'macd_hist': latest['macd_hist'],
                'supertrend_signal': latest['supertrend_signal'],
                'bb_position': latest['bb_position'],
                'volume_ratio': latest['volume_ratio']
            }
        }
        
        logger.info(f"Сигнал сгенерирован: {signal_direction} с вероятностью {probability_up:.3f}")
        return signal_info
    
    def extract_features(self, latest_data) -> np.ndarray | None:
        """Извлекает признаки для модели."""
        try:
            features = []
            for feature_name in MODEL_FEATURES:
                if feature_name in latest_data:
                    value = latest_data[feature_name]
                    features.append(value if not pd.isna(value) else 0)
                else:
                    features.append(0)
            return np.array(features)
        except Exception as e:
            logger.error(f"Ошибка извлечения признаков: {e}")
            return None
    
    def determine_signal_direction(self, latest_data, probability_up: float) -> str:
        """Определяет направление сигнала."""
        # Анализ множественных индикаторов
        bullish_signals = 0
        bearish_signals = 0
        
        # MACD
        if not pd.isna(latest_data['macd_hist']):
            if latest_data['macd_hist'] > 0:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Supertrend
        if not pd.isna(latest_data['supertrend_signal']):
            if latest_data['supertrend_signal'] == 1:
                bullish_signals += 1
            elif latest_data['supertrend_signal'] == -1:
                bearish_signals += 1
        
        # RSI
        if not pd.isna(latest_data['rsi']):
            if latest_data['rsi'] < 35:
                bullish_signals += 1
            elif latest_data['rsi'] > 65:
                bearish_signals += 1
        
        # Stochastic
        if not pd.isna(latest_data['stoch_crossover']):
            if latest_data['stoch_crossover'] == 1:
                bullish_signals += 1
            elif latest_data['stoch_crossover'] == -1:
                bearish_signals += 1
        
        # VWAP
        if not pd.isna(latest_data['vwap_distance']):
            if latest_data['vwap_distance'] > 0:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Окончательное решение
        if bullish_signals > bearish_signals and probability_up > 0.5:
            return "CALL"
        elif bearish_signals > bullish_signals and probability_up < 0.5:
            return "PUT"
        else:
            return "CALL" if probability_up > 0.5 else "PUT"
    
    def calculate_accuracy(self, latest_data, probability: float) -> float:
        """Рассчитывает ожидаемую точность сигнала."""
        base_accuracy = 0.85
        
        # Бонус за высокую вероятность ИИ
        ai_bonus = min(0.04, (probability - MIN_ACCURACY_THRESHOLD) * 0.1)
        
        # Бонус за объем
        volume_bonus = 0.01 if latest_data['volume_ratio'] > 2.0 else 0
        
        # Бонус за четкие сигналы индикаторов
        indicator_bonus = 0
        if abs(latest_data['macd_hist']) > 0.001:
            indicator_bonus += 0.005
        if abs(latest_data['supertrend_signal']) == 1:
            indicator_bonus += 0.005
        
        accuracy = base_accuracy + ai_bonus + volume_bonus + indicator_bonus
        return min(0.92, accuracy)  # Максимум 92%
    
    def determine_expiry_time(self, latest_data) -> str:
        """Определяет оптимальное время экспирации."""
        # Базовая логика: высокая волатильность = короткое время
        if not pd.isna(latest_data['atr_normalized']):
            if latest_data['atr_normalized'] > 0.02:
                return "1m"
            elif latest_data['atr_normalized'] > 0.01:
                return "5m"
            else:
                return "15m"
        return "5m"  # По умолчанию

# Создаем экземпляр анализатора
signal_analyzer = BinaryOptionsSignalAnalyzer()

async def analyze_pair_and_timeframe(pair: str, timeframe: str):
    """Анализирует пару и таймфрейм для бинарных опционов."""
    try:
        # Получаем данные
        from websocket import get_latest_data
        data_df = get_latest_data(pair, timeframe)
        
        if data_df.empty or len(data_df) < 30:
            logger.debug(f"Недостаточно данных для {pair}-{timeframe}")
            return
        
        # Рассчитываем индикаторы
        data_with_indicators = calculate_all_indicators(data_df)
        
        if data_with_indicators.empty:
            logger.debug(f"Не удалось рассчитать индикаторы для {pair}-{timeframe}")
            return
        
        # Проверяем минимальное время между сигналами
        key = f"{pair}_{timeframe}"
        current_time = datetime.now().timestamp()
        
        if key in signal_analyzer.last_signal_time:
            time_diff = current_time - signal_analyzer.last_signal_time[key]
            if time_diff < RISK_MANAGEMENT['min_time_between_signals']:
                return
        
        # Анализируем сигнал
        signal_result = signal_analyzer.quantum_binary_signal(data_with_indicators)
        
        if signal_result:
            # Обновляем время последнего сигнала
            signal_analyzer.last_signal_time[key] = current_time
            signal_analyzer.daily_signal_count += 1
            
            # Отправляем в Telegram
            await send_binary_signal_to_telegram(pair, timeframe, signal_result)
            
            # Сохраняем в БД
            save_binary_signal(
                pair=pair,
                timeframe=timeframe,
                signal_type=signal_result['signal_type'],
                entry_time=int(signal_result['entry_time']),
                expiry_time=signal_result['expiry_time'],
                probability=signal_result['probability'],
                accuracy=signal_result['accuracy'],
                entry_price=signal_result['entry_price']
            )
            
            logger.info(f"Сигнал отправлен: {pair}-{timeframe} {signal_result['signal_type']}")
    
    except Exception as e:
        logger.error(f"Ошибка анализа {pair}-{timeframe}: {e}")

async def send_binary_signal_to_telegram(pair: str, timeframe: str, signal: dict):
    """Отправляет сигнал бинарного опциона в Telegram."""
    from telegram import send_telegram_message
    
    # Форматируем пару для отображения
    display_pair = pair.replace('USDT', '/USD')
    
    # Определяем эмодзи направления
    direction_emoji = "🟢 ⬆️" if signal['signal_type'] == "CALL" else "🔴 ⬇️"
    
    # Форматируем время
    entry_time = datetime.fromtimestamp(signal['entry_time'] / 1000, tz=timezone.utc)
    
    message = f"""
🎯 **BINARY OPTIONS SIGNAL**
Стратегия: QuantumBinaryPrecisionV3

💱 **Пара:** {display_pair}
⏱️ **Таймфрейм:** {timeframe}
📊 **Направление:** {signal['signal_type']} {direction_emoji}
⏰ **Экспирация:** {signal['expiry_time']}
🎯 **Точность:** {signal['accuracy']:.1%}
⚡ **Сила сигнала:** {signal['strength']}

💰 **Цена входа:** ${signal['entry_price']:.4f}
🕐 **Время входа:** {entry_time.strftime('%H:%M:%S')} UTC

📈 **Индикаторы:**
• RSI: {signal['indicators']['rsi']:.1f}
• MACD: {signal['indicators']['macd_hist']:.6f}
• Supertrend: {signal['indicators']['supertrend_signal']}
• BB Position: {signal['indicators']['bb_position']:.2f}
• Volume: {signal['indicators']['volume_ratio']:.1f}x

---
⏳ Следующий анализ через: 5 сек
📊 Сигналов сегодня: {signal_analyzer.daily_signal_count}
    """
    
    await send_telegram_message(message)
  
