import lightgbm as lgb
import joblib
import numpy as np
import logging
from globals import AI_MODEL_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinaryOptionsAIModel:
    """ИИ-модель для предсказания направления движения цены в бинарных опционах."""
    
    def __init__(self, model_path: str = AI_MODEL_PATH):
        self.model = None
        self.model_path = model_path
        self.feature_names = [
            'vwap_distance', 'macd_hist', 'rsi', 'supertrend_signal',
            'volume_ratio', 'bb_position', 'bb_width', 'stoch_k', 'stoch_d',
            'atr_normalized', 'williams_r', 'price_momentum', 'pct_change',
            'vwap_gradient', 'stoch_diff', 'stoch_crossover'
        ]
        self._load_model()

    def _load_model(self):
        """Загружает предобученную модель или создает заглушку."""
        try:
            self.model = joblib.load(self.model_path)
            logger.info(f"Модель загружена из {self.model_path}")
        except FileNotFoundError:
            logger.warning(f"Модель не найдена: {self.model_path}. Используется заглушка.")
            self.model = self._create_enhanced_dummy_model()
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            self.model = self._create_enhanced_dummy_model()

    def _create_enhanced_dummy_model(self):
        """Создает улучшенную заглушку с логикой для бинарных опционов."""
        logger.warning("Используется заглушка модели с базовой логикой!")
        
        class EnhancedDummyModel:
            def predict_proba(self, X):
                """Предсказание с базовой логикой для бинарных опционов."""
                probabilities = []
                
                for row in X:
                    # Базовая логика на основе индикаторов
                    score = 0.5  # Базовая вероятность
                    
                    # MACD Histogram
                    if len(row) > 1 and not np.isnan(row[1]):
                        score += 0.1 if row[1] > 0 else -0.1
                    
                    # RSI
                    if len(row) > 2 and not np.isnan(row[2]):
                        if row[2] < 30:
                            score += 0.15  # Перепроданность
                        elif row[2] > 70:
                            score -= 0.15  # Перекупленность
                    
                    # Supertrend Signal
                    if len(row) > 3 and not np.isnan(row[3]):
                        score += 0.1 * row[3]
                    
                    # Volume Ratio
                    if len(row) > 4 and not np.isnan(row[4]):
                        if row[4] > 1.5:
                            score += 0.1
                    
                    # BB Position
                    if len(row) > 5 and not np.isnan(row[5]):
                        if row[5] < 0.2:
                            score += 0.1
                        elif row[5] > 0.8:
                            score -= 0.1
                    
                    # Stochastic Crossover
                    if len(row) > 15 and not np.isnan(row[15]):
                        score += 0.1 * row[15]
                    
                    # Ограничиваем диапазон
                    score = max(0.1, min(0.9, score))
                    
                    # Добавляем небольшую случайность для реализма
                    noise = np.random.normal(0, 0.05)
                    score = max(0.1, min(0.9, score + noise))
                    
                    probabilities.append([1 - score, score])
                
                return np.array(probabilities)
            
            def predict(self, X):
                proba = self.predict_proba(X)
                return (proba[:, 1] >= 0.5).astype(int)
        
        return EnhancedDummyModel()

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Предсказание вероятности для бинарных опционов."""
        if self.model is None:
            logger.error("Модель не загружена")
            return np.array([[0.5, 0.5]])
        
        try:
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # Проверяем количество признаков
            if features.shape[1] != len(self.feature_names):
                logger.warning(f"Несоответствие количества признаков: {features.shape[1]} != {len(self.feature_names)}")
                # Дополняем или обрезаем до нужного размера
                if features.shape[1] < len(self.feature_names):
                    padding = np.zeros((features.shape[0], len(self.feature_names) - features.shape[1]))
                    features = np.hstack([features, padding])
                else:
                    features = features[:, :len(self.feature_names)]
            
            probabilities = self.model.predict_proba(features)
            return probabilities
            
        except Exception as e:
            logger.error(f"Ошибка предсказания: {e}")
            return np.array([[0.5, 0.5]])

    def get_signal_strength(self, probability: float) -> str:
        """Определяет силу сигнала."""
        if probability >= 0.9:
            return "ОЧЕНЬ СИЛЬНЫЙ"
        elif probability >= 0.85:
            return "СИЛЬНЫЙ"
        elif probability >= 0.75:
            return "СРЕДНИЙ"
        else:
            return "СЛАБЫЙ"

# Инициализация модели
ai_model = BinaryOptionsAIModel()

# Список признаков для модели
MODEL_FEATURES = [
    'vwap_distance', 'macd_hist', 'rsi', 'supertrend_signal',
    'volume_ratio', 'bb_position', 'bb_width', 'stoch_k', 'stoch_d',
    'atr_normalized', 'williams_r', 'price_momentum', 'pct_change',
    'vwap_gradient', 'stoch_diff', 'stoch_crossover'
]
