import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging
from datetime import datetime
import os
from globals import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PAIRS, TIME_FRAMES
from core import main_loop, get_system_status
from telegram import start_telegram_bot, stop_telegram_bot, send_telegram_message
from database import init_db, get_daily_statistics
from bot_control import (
    start_bot_analysis, stop_bot_analysis, restart_bot_analysis,
    get_bot_status, get_bot_statistics
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('binary_options_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Binary Options Bot - Quantum Precision V3",
    description="Высокоточный бот для анализа бинарных опционов с ИИ-предсказаниями",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Глобальные переменные для отслеживания состояния
app_start_time = None
telegram_bot_task = None

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения."""
    global app_start_time, telegram_bot_task
    
    app_start_time = datetime.now()
    logger.info("🚀 Запуск Binary Options Bot - Quantum Precision V3")
    
    try:
        # Инициализация базы данных
        init_db()
        logger.info("✅ База данных инициализирована")
        
        # Запуск Telegram бота
        telegram_bot_task = asyncio.create_task(start_telegram_bot())
        logger.info("✅ Telegram бот запущен")
        
        # Отправка уведомления о запуске
        if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID != "":
            startup_message = f"""
🚀 **Binary Options Bot запущен!**

**Время запуска:** {app_start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC

**Конфигурация:**
• Пары: {len(PAIRS)} ({', '.join([p.replace('USDT', '') for p in PAIRS[:3]])}...)
• Таймфреймы: {len(TIME_FRAMES)} ({', '.join(TIME_FRAMES)})
• Интервал обновления: 5 секунд
• Минимальная точность: 85%

**Доступные команды:**
• `/run_analysis` - Запуск анализа
• `/stop_analysis` - Остановка анализа
• `/stats` - Статистика
• `/help` - Справка

Готов к работе! 🎯
            """
            await send_telegram_message(startup_message)
        
        logger.info("🎯 Binary Options Bot готов к работе!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке приложения."""
    global telegram_bot_task
    
    logger.info("🛑 Остановка Binary Options Bot...")
    
    try:
        # Остановка анализа
        await stop_bot_analysis()
        
        # Остановка Telegram бота
        if telegram_bot_task:
            telegram_bot_task.cancel()
            try:
                await telegram_bot_task
            except asyncio.CancelledError:
                pass
        
        await stop_telegram_bot()
        
        # Уведомление об остановке
        if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID != "":
            shutdown_message = "🛑 Binary Options Bot остановлен"
            await send_telegram_message(shutdown_message)
        
        logger.info("✅ Binary Options Bot остановлен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке: {e}")

# API Endpoints

@app.get("/")
async def root():
    """Главная страница API."""
    uptime = datetime.now() - app_start_time if app_start_time else None
    
    return {
        "message": "Binary Options Bot - Quantum Precision V3",
        "status": "running",
        "version": "3.0.0",
        "uptime_seconds": uptime.total_seconds() if uptime else 0,
        "start_time": app_start_time.isoformat() if app_start_time else None,
        "endpoints": {
            "status": "/status",
            "statistics": "/statistics",
            "start": "/start",
            "stop": "/stop",
            "restart": "/restart"
        }
    }

@app.get("/status")
async def get_status():
    """Возвращает текущий статус бота."""
    try:
        bot_status = get_bot_status()
        system_status = get_system_status()
        
        return {
            "bot_active": bot_status["bot_active"],
            "initialized": bot_status["initialized"],
            "websocket_running": bot_status["websocket_running"],
            "uptime_seconds": bot_status["uptime"],
            "pairs_count": len(PAIRS),
            "timeframes_count": len(TIME_FRAMES),
            "system_status": system_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_statistics():
    """Возвращает статистику работы бота."""
    try:
        bot_stats = await get_bot_statistics()
        total_signals, wins = get_daily_statistics()
        
        return {
            "daily_signals": total_signals,
            "successful_signals": wins,
            "win_rate": bot_stats["win_rate"],
            "target_win_rate": 85.0,
            "performance_rating": bot_stats["performance"],
            "pairs_analyzed": len(PAIRS),
            "timeframes_analyzed": len(TIME_FRAMES),
            "total_combinations": len(PAIRS) * len(TIME_FRAMES),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start")
async def start_analysis():
    """Запускает анализ бота."""
    try:
        result = await start_bot_analysis()
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Ошибка запуска анализа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop")
async def stop_analysis():
    """Останавливает анализ бота."""
    try:
        result = await stop_bot_analysis()
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Ошибка остановки анализа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/restart")
async def restart_analysis():
    """Перезапускает анализ бота."""
    try:
        result = await restart_bot_analysis()
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Ошибка перезапуска анализа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Проверка здоровья системы."""
    try:
        # Проверяем основные компоненты
        db_ok = True
        try:
            get_daily_statistics()
        except:
            db_ok = False
        
        telegram_ok = TELEGRAM_BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN"
        
        system_status = get_system_status()
        
        overall_health = "healthy" if (db_ok and telegram_ok) else "unhealthy"
        
        return {
            "status": overall_health,
            "components": {
                "database": "ok" if db_ok else "error",
                "telegram": "ok" if telegram_ok else "not_configured",
                "websocket": "ok" if system_status["websocket_running"] else "disconnected",
                "bot_engine": "ok" if system_status["bot_active"] else "stopped"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Конфигурация для запуска
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Запуск сервера на {host}:{port}")
    
    # Для разработки
    if os.getenv("ENVIRONMENT") == "development":
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    else:
        # Для продакшена
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
      
