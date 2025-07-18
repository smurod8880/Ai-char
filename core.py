import asyncio
import logging
import time
from globals import PAIRS, TIME_FRAMES, UPDATE_INTERVAL, BOT_ACTIVE
from websocket import connect_binance_websocket, initialize_websocket_data_queues
from signal_analyzer import analyze_pair_and_timeframe
from database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinaryOptionsCoreEngine:
    """Основной движок для анализа бинарных опционов."""
    
    def __init__(self):
        self.ws_task = None
        self.analysis_tasks = []
        self.is_initialized = False
    
    async def initialize(self):
        """Инициализирует все компоненты системы."""
        if self.is_initialized:
            return
        
        logger.info("Инициализация Binary Options Core Engine...")
        
        # Инициализация БД
        init_db()
        
        # Инициализация очередей данных
        await initialize_websocket_data_queues()
        
        # Запуск WebSocket в фоновом режиме
        if not self.ws_task:
            self.ws_task = asyncio.create_task(connect_binance_websocket())
            logger.info("WebSocket задача запущена")
        
        # Даем время на подключение и получение первых данных
        await asyncio.sleep(10)
        
        self.is_initialized = True
        logger.info("Core Engine инициализирован")
    
    async def cleanup(self):
        """Очищает ресурсы при остановке."""
        if self.ws_task and not self.ws_task.done():
            self.ws_task.cancel()
            try:
                await self.ws_task
            except asyncio.CancelledError:
                pass
        
        for task in self.analysis_tasks:
            if not task.done():
                task.cancel()
        
        logger.info("Core Engine очищен")

# Глобальный экземпляр движка
core_engine = BinaryOptionsCoreEngine()

async def main_loop():
    """Основной цикл анализа для бинарных опционов."""
    global BOT_ACTIVE
    
    logger.info("🚀 Запуск основного цикла анализа бинарных опционов")
    
    # Инициализация системы
    await core_engine.initialize()
    
    cycle_count = 0
    total_signals_sent = 0
    
    try:
        while BOT_ACTIVE:
            cycle_start_time = time.time()
            cycle_count += 1
            
            logger.info(f"Цикл анализа #{cycle_count} - Анализ {len(PAIRS)} пар на {len(TIME_FRAMES)} таймфреймах")
            
            # Создаем задачи для параллельного анализа
            analysis_tasks = []
            for pair in PAIRS:
                for timeframe in TIME_FRAMES:
                    task = asyncio.create_task(
                        analyze_pair_and_timeframe(pair, timeframe)
                    )
                    analysis_tasks.append(task)
            
            # Выполняем все задачи параллельно
            if analysis_tasks:
                try:
                    results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
                    
                    # Подсчитываем результаты
                    successful_analyses = sum(1 for r in results if not isinstance(r, Exception))
                    errors = sum(1 for r in results if isinstance(r, Exception))
                    
                    if errors > 0:
                        logger.warning(f"Ошибок в анализе: {errors}/{len(analysis_tasks)}")
                    
                except Exception as e:
                    logger.error(f"Критическая ошибка в цикле анализа: {e}")
            
            # Рассчитываем время выполнения цикла
            cycle_time = time.time() - cycle_start_time
            sleep_time = max(0, UPDATE_INTERVAL - cycle_time)
            
            # Логируем статистику цикла
            if cycle_count % 10 == 0:  # Каждые 10 циклов
                logger.info(f"Статистика: Цикл #{cycle_count}, Время: {cycle_time:.2f}с, Следующий через: {sleep_time:.2f}с")
            
            # Ждем до следующего цикла
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
    
    except asyncio.CancelledError:
        logger.info("Основной цикл анализа отменен")
    except Exception as e:
        logger.error(f"Критическая ошибка в main_loop: {e}")
    finally:
        await core_engine.cleanup()
        logger.info("Основной цикл анализа завершен")

async def emergency_stop():
    """Экстренная остановка всех процессов."""
    global BOT_ACTIVE
    BOT_ACTIVE = False
    await core_engine.cleanup()
    logger.warning("Выполнена экстренная остановка системы")

# Функция для внешнего управления
async def start_analysis():
    """Запускает анализ извне."""
    global BOT_ACTIVE
    if not BOT_ACTIVE:
        BOT_ACTIVE = True
        asyncio.create_task(main_loop())
        return "Анализ запущен"
    return "Анализ уже активен"

async def stop_analysis():
    """Останавливает анализ извне."""
    global BOT_ACTIVE
    if BOT_ACTIVE:
        BOT_ACTIVE = False
        await core_engine.cleanup()
        return "Анализ остановлен"
    return "Анализ уже остановлен"

def get_system_status():
    """Возвращает статус системы."""
    return {
        "bot_active": BOT_ACTIVE,
        "initialized": core_engine.is_initialized,
        "websocket_running": core_engine.ws_task is not None and not core_engine.ws_task.done()
    }
  
