import asyncio
import logging
from typing import Dict, Any
from globals import BOT_ACTIVE
from core import start_analysis, stop_analysis, get_system_status
from database import get_daily_statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinaryOptionsBotController:
    """Контроллер для управления ботом бинарных опционов."""
    
    def __init__(self):
        self.start_time = None
        self.command_history = []
    
    async def start_bot(self) -> Dict[str, Any]:
        """Запускает бота."""
        try:
            result = await start_analysis()
            self.start_time = asyncio.get_event_loop().time()
            self.command_history.append({"command": "start", "timestamp": self.start_time})
            
            return {
                "status": "success",
                "message": result,
                "timestamp": self.start_time
            }
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            return {
                "status": "error",
                "message": f"Ошибка запуска: {e}",
                "timestamp": asyncio.get_event_loop().time()
            }
    
    async def stop_bot(self) -> Dict[str, Any]:
        """Останавливает бота."""
        try:
            result = await stop_analysis()
            stop_time = asyncio.get_event_loop().time()
            self.command_history.append({"command": "stop", "timestamp": stop_time})
            
            return {
                "status": "success",
                "message": result,
                "timestamp": stop_time,
                "uptime": stop_time - self.start_time if self.start_time else 0
            }
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}")
            return {
                "status": "error",
                "message": f"Ошибка остановки: {e}",
                "timestamp": asyncio.get_event_loop().time()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает текущий статус бота."""
        system_status = get_system_status()
        current_time = asyncio.get_event_loop().time()
        
        return {
            "bot_active": system_status["bot_active"],
            "initialized": system_status["initialized"],
            "websocket_running": system_status["websocket_running"],
            "uptime": current_time - self.start_time if self.start_time else 0,
            "start_time": self.start_time,
            "current_time": current_time
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику работы бота."""
        try:
            total_signals, wins = get_daily_statistics()
            win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
            
            return {
                "daily_signals": total_signals,
                "successful_signals": wins,
                "win_rate": win_rate,
                "target_win_rate": 85.0,
                "performance": "good" if win_rate >= 85 else "needs_improvement"
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {
                "error": str(e),
                "daily_signals": 0,
                "successful_signals": 0,
                "win_rate": 0
            }
    
    async def restart_bot(self) -> Dict[str, Any]:
        """Перезапускает бота."""
        logger.info("Перезапуск бота...")
        
        # Останавливаем
        stop_result = await self.stop_bot()
        if stop_result["status"] != "success":
            return stop_result
        
        # Ждем полной остановки
        await asyncio.sleep(3)
        
        # Запускаем
        start_result = await self.start_bot()
        
        return {
            "status": "success" if start_result["status"] == "success" else "error",
            "message": "Бот перезапущен" if start_result["status"] == "success" else "Ошибка перезапуска",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    def get_command_history(self) -> list:
        """Возвращает историю команд."""
        return self.command_history[-10:]  # Последние 10 команд

# Глобальный контроллер
bot_controller = BinaryOptionsBotController()

# Функции для внешнего использования
async def start_bot_analysis():
    """Запускает анализ бота."""
    return await bot_controller.start_bot()

async def stop_bot_analysis():
    """Останавливает анализ бота."""
    return await bot_controller.stop_bot()

async def restart_bot_analysis():
    """Перезапускает бота."""
    return await bot_controller.restart_bot()

def get_bot_status():
    """Возвращает статус бота."""
    return bot_controller.get_status()

async def get_bot_statistics():
    """Возвращает статистику бота."""
    return await bot_controller.get_statistics()

if __name__ == "__main__":
    # Пример использования
    async def main():
        print("Тестирование контроллера бота...")
        
        # Запуск
        result = await start_bot_analysis()
        print(f"Запуск: {result}")
        
        # Статус
        status = get_bot_status()
        print(f"Статус: {status}")
        
        # Ждем
        await asyncio.sleep(5)
        
        # Статистика
        stats = await get_bot_statistics()
        print(f"Статистика: {stats}")
        
        # Остановка
        result = await stop_bot_analysis()
        print(f"Остановка: {result}")
    
    asyncio.run(main())
  
