import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# **Конфигурация Telegram Bot API**
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# **Конфигурация WebSocket Binance**
BINANCE_WS_BASE_URL = "wss://stream.binance.com:9443/ws"

# **Конфигурация для бинарных опционов**
PAIRS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT"]
TIME_FRAMES = ["1m", "5m", "15m", "30m", "1h"]  # Оптимизировано для бинарных опционов
EXPIRY_TIMES = {
    "1m": "1m",
    "5m": "5m", 
    "15m": "15m",
    "30m": "30m",
    "1h": "1h"
}

# **Параметры анализа для бинарных опционов**
UPDATE_INTERVAL = 5  # Ускорено для бинарных опционов
CANDLE_COUNT = 30    # Уменьшено для быстрого анализа
MIN_ACCURACY_THRESHOLD = 0.85

# **Параметры индикаторов**
RSI_PERIOD = 14
MACD_FAST_PERIOD = 12
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9
BOLLINGER_PERIOD = 20
BOLLINGER_NUM_STD_DEV = 2
SUPERTREND_PERIOD = 10
SUPERTREND_MULTIPLIER = 2.8  # Оптимизировано для бинарных опционов
ATR_PERIOD = 14
STOCH_K_PERIOD = 14
STOCH_D_PERIOD = 3
STOCH_SMOOTH_K_PERIOD = 3

# **Параметры ИИ-модели**
AI_MODEL_PATH = "model.pkl"

# **Системные флаги**
BOT_ACTIVE = False
DATA_STORES = {}

# **Параметры для бинарных опционов**
MAX_CONCURRENT_SIGNALS = 3
RISK_MANAGEMENT = {
    "max_daily_signals": 50,
    "min_time_between_signals": 30,  # секунд
    "volatility_filter": True
}

# **Логирование**
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "bot.log"
