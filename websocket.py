import asyncio
import websockets
import json
import logging
from collections import deque
from globals import BINANCE_WS_BASE_URL, PAIRS, TIME_FRAMES, CANDLE_COUNT
from database import save_historical_data, load_historical_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище данных для каждой пары/таймфрейма
live_data_queues = {}

async def connect_binance_websocket():
    """Подключение к Binance WebSocket для получения данных в реальном времени."""
    streams = []
    for pair in PAIRS:
        for tf in TIME_FRAMES:
            stream_name = f"{pair.lower()}@kline_{tf}"
            streams.append(stream_name)
            key = f"{pair}_{tf}"
            if key not in live_data_queues:
                live_data_queues[key] = deque(maxlen=CANDLE_COUNT)
                # Загружаем начальные данные из БД
                initial_data = load_historical_data(pair, tf, CANDLE_COUNT)
                for item in initial_data:
                    live_data_queues[key].append(item)
                if initial_data:
                    logger.info(f"Загружено {len(initial_data)} свечей для {key}")

    uri = f"{BINANCE_WS_BASE_URL}/stream?streams={'/'.join(streams)}"
    logger.info(f"Подключение к Binance WebSocket: {len(streams)} потоков")

    while True:
        try:
            async with websockets.connect(uri) as ws:
                logger.info("WebSocket соединение установлено")
                
                while True:
                    message = await ws.recv()
                    data = json.loads(message)

                    if 'data' in data and 'k' in data['data']:
                        kline = data['data']['k']
                        if kline['x']:  # Закрытая свеча
                            symbol = kline['s']
                            interval = kline['i']
                            key = f"{symbol}_{interval}"

                            candle_data = {
                                "timestamp": kline['t'],
                                "open": float(kline['o']),
                                "high": float(kline['h']),
                                "low": float(kline['l']),
                                "close": float(kline['c']),
                                "volume": float(kline['v'])
                            }

                            if key in live_data_queues:
                                live_data_queues[key].append(candle_data)
                                save_historical_data(symbol, interval, [candle_data])
                                logger.debug(f"Новая свеча {key}: {candle_data['close']}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket соединение закрыто. Переподключение через 5 сек...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Ошибка WebSocket: {e}. Переподключение через 5 сек...")
            await asyncio.sleep(5)

def get_latest_data(pair: str, timeframe: str):
    """Получает последние данные для анализа."""
    key = f"{pair}_{timeframe}"
    if key in live_data_queues and live_data_queues[key]:
        import pandas as pd
        df = pd.DataFrame(list(live_data_queues[key]))
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.sort_index()
    return pd.DataFrame()

async def initialize_websocket_data_queues():
    """Инициализирует очереди данных при старте."""
    for pair in PAIRS:
        for tf in TIME_FRAMES:
            key = f"{pair}_{tf}"
            if key not in live_data_queues:
                live_data_queues[key] = deque(maxlen=CANDLE_COUNT)
            initial_data = load_historical_data(pair, tf, CANDLE_COUNT)
            for item in initial_data:
                live_data_queues[key].append(item)
            if initial_data:
                logger.info(f"Инициализировано {len(initial_data)} свечей для {key}")
