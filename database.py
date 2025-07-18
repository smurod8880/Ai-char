import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_NAME = "binary_options_bot.db"

def init_db():
    """Инициализирует базу данных для бинарных опционов."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # Таблица исторических данных
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_data (
                pair TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (pair, timeframe, timestamp)
            )
        """)

        # Таблица сигналов для бинарных опционов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS binary_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pair TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                entry_time INTEGER NOT NULL,
                expiry_time TEXT NOT NULL,
                probability REAL,
                accuracy REAL,
                entry_price REAL,
                status TEXT DEFAULT 'SENT',
                result TEXT,
                profit_loss REAL,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)

        # Таблица статистики
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_signals INTEGER DEFAULT 0,
                successful_signals INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0,
                total_profit REAL DEFAULT 0,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)

        conn.commit()
        logger.info("База данных для бинарных опционов успешно инициализирована.")
    except sqlite3.Error as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
    finally:
        if conn:
            conn.close()

def save_historical_data(pair: str, timeframe: str, data: list):
    """Сохраняет исторические данные."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR REPLACE INTO historical_data 
            (pair, timeframe, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [(pair, timeframe, int(d['timestamp']/1000), d['open'], 
               d['high'], d['low'], d['close'], d['volume']) for d in data])
        conn.commit()
        logger.debug(f"Сохранено {len(data)} свечей для {pair}-{timeframe}")
    except sqlite3.Error as e:
        logger.error(f"Ошибка сохранения данных: {e}")
    finally:
        if conn:
            conn.close()

def load_historical_data(pair: str, timeframe: str, limit: int):
    """Загружает исторические данные."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, open, high, low, close, volume
            FROM historical_data
            WHERE pair = ? AND timeframe = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (pair, timeframe, limit))
        rows = cursor.fetchall()
        return [{"timestamp": r[0]*1000, "open": r[1], "high": r[2], 
                "low": r[3], "close": r[4], "volume": r[5]} for r in reversed(rows)]
    except sqlite3.Error as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        return []
    finally:
        if conn:
            conn.close()

def save_binary_signal(pair: str, timeframe: str, signal_type: str, 
                      entry_time: int, expiry_time: str, probability: float, 
                      accuracy: float, entry_price: float):
    """Сохраняет сигнал бинарного опциона."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO binary_signals 
            (pair, timeframe, signal_type, entry_time, expiry_time, 
             probability, accuracy, entry_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pair, timeframe, signal_type, entry_time, expiry_time, 
              probability, accuracy, entry_price, "SENT"))
        conn.commit()
        logger.info(f"Сигнал сохранен: {pair}-{timeframe} {signal_type}")
    except sqlite3.Error as e:
        logger.error(f"Ошибка сохранения сигнала: {e}")
    finally:
        if conn:
            conn.close()

def get_daily_statistics():
    """Получает статистику за день."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins
            FROM binary_signals 
            WHERE date(created_at, 'unixepoch') = ?
        """, (today,))
        result = cursor.fetchone()
        return result if result else (0, 0)
    except sqlite3.Error as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return (0, 0)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
