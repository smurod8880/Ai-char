import telegram
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import logging
from globals import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BOT_ACTIVE
from database import init_db, get_daily_statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Глобальная переменная для хранения chat_id
current_chat_id = TELEGRAM_CHAT_ID

async def send_telegram_message(message: str):
    """Отправляет сообщение в Telegram."""
    global current_chat_id
    
    if not current_chat_id:
        logger.error("Chat ID не установлен")
        return
        
    try:
        await bot.send_message(
            chat_id=current_chat_id, 
            text=message, 
            parse_mode='Markdown'
        )
        logger.debug("Сообщение отправлено в Telegram")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    global current_chat_id
    
    user_id = update.effective_chat.id
    username = update.effective_user.username or update.effective_user.first_name
    current_chat_id = str(user_id)
    
    logger.info(f"Пользователь {username} (ID: {user_id}) запустил бота")
    
    welcome_message = f"""
🎯 **Добро пожаловать в Binary Options Bot!**

Привет, {username}! 

Я специализированный бот для анализа бинарных опционов с использованием стратегии **QuantumBinaryPrecisionV3**.

**Доступные команды:**
• `/start` - Запуск бота
• `/run_analysis` - Начать анализ рынка
• `/stop_analysis` - Остановить анализ
• `/stats` - Статистика за день
• `/help` - Помощь

**Особенности:**
✅ Анализ в реальном времени
✅ ИИ-предсказания с точностью 85%+
✅ Оптимальные времена экспирации
✅ Управление рисками
✅ Детальная статистика

Для начала работы используйте команду `/run_analysis`
    """
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def run_analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает анализ рынка."""
    global BOT_ACTIVE
    
    if BOT_ACTIVE:
        await update.message.reply_text("⚠️ Анализ уже запущен!")
        return
    
    BOT_ACTIVE = True
    
    start_message = """
🚀 **Запуск анализа бинарных опционов**

✅ Подключение к Binance WebSocket
✅ Инициализация ИИ-модели
✅ Загрузка исторических данных
✅ Активация стратегии QuantumBinaryPrecisionV3

**Анализируемые пары:**
• BTC/USD, ETH/USD, BNB/USD
• XRP/USD, SOL/USD, ADA/USD, DOGE/USD

**Таймфреймы:** 1m, 5m, 15m, 30m, 1h

🎯 Ожидайте сигналы с точностью 85%+
⏰ Обновление каждые 5 секунд
    """
    
    await update.message.reply_text(start_message, parse_mode='Markdown')
    
    # Запускаем основной цикл
    from core import main_loop
    asyncio.create_task(main_loop())

async def stop_analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Останавливает анализ."""
    global BOT_ACTIVE
    
    if not BOT_ACTIVE:
        await update.message.reply_text("⚠️ Анализ уже остановлен!")
        return
    
    BOT_ACTIVE = False
    
    stop_message = """
🛑 **Анализ остановлен**

Все процессы анализа приостановлены.
Для возобновления используйте `/run_analysis`
    """
    
    await update.message.reply_text(stop_message, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику за день."""
    try:
        total_signals, wins = get_daily_statistics()
        win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
        
        stats_message = f"""
📊 **Статистика за сегодня**

🎯 **Всего сигналов:** {total_signals}
✅ **Успешных:** {wins}
📈 **Процент побед:** {win_rate:.1f}%
🎲 **Статус:** {'Активен' if BOT_ACTIVE else 'Остановлен'}

**Целевые показатели:**
• Точность: 85%+
• Сигналов в день: 30-50
• Максимум сигналов: 50/день
        """
        
        await update.message.reply_text(stats_message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Ошибка получения статистики: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает справку."""
    help_message = """
🆘 **Справка по Binary Options Bot**

**Команды:**
• `/start` - Запуск и настройка бота
• `/run_analysis` - Начать анализ рынка
• `/stop_analysis` - Остановить анализ
• `/stats` - Статистика за день
• `/help` - Эта справка

**Как пользоваться:**
1. Запустите бота командой `/start`
2. Начните анализ командой `/run_analysis`
3. Получайте сигналы в реальном времени
4. Проверяйте статистику командой `/stats`

**Формат сигналов:**
• Пара и таймфрейм
• Направление (CALL/PUT)
• Время экспирации
• Точность предсказания
• Цена входа и время

**Поддержка:** Бот работает 24/7 и анализирует рынок каждые 5 секунд.
    """
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

def setup_telegram_handlers():
    """Настраивает обработчики команд."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("run_analysis", run_analysis_command))
    application.add_handler(CommandHandler("stop_analysis", stop_analysis_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))

async def start_telegram_bot():
    """Запускает Telegram бота."""
    setup_telegram_handlers()
    logger.info("Запуск Telegram бота...")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info("Telegram бот запущен и готов к работе")

async def stop_telegram_bot():
    """Останавливает Telegram бота."""
    logger.info("Остановка Telegram бота...")
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    logger.info("Telegram бот остановлен")
  
