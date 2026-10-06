import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

if not BOT_TOKEN:
    logger.warning("BOT_TOKEN environment variable topilmadi!")

bot = None


def _setup_bot():
    """
    BOT_TOKEN mavjud bo'lganda faqat bot ob'ekti yaratadi.
    Token yo'q bo'lsa bot `None` qoldi va Flask ilovasi qiyinlashmasdan ishlaydi.
    """
    global bot
    import telebot
    from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

    if BOT_TOKEN:
        bot = telebot.TeleBot(BOT_TOKEN)


if BOT_TOKEN:
    _setup_bot()


def _ensure_bot():
    if bot is None:
        raise RuntimeError("Bot tokeni yo'q, @bot.message_handler decoratorlari qo'llanilmaydi")


def bot_message_handler(*args, **kwargs):
    """Guard that raises only if bot is None when decorator is invoked."""
    def decorator(func):
        _ensure_bot()
        return bot.message_handler(*args, **kwargs)(func)
    return decorator


def send_welcome(message):
    """
    /start buyrug'i kelganda foydalanuvchiga salomlashish xabari
    va WebApp tugmasini ko'rsatish.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    if WEBAPP_URL:
        web_app_btn = KeyboardButton("📱 Yangiliklar Portali", web_app=WebAppInfo(WEBAPP_URL))
        markup.add(web_app_btn)
    
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        f"Yangiliklar portalimiz botiga xush kelibsiz. "
        f"Eng so'nggi yangiliklar va mahsulotlarni ko'rish uchun pastdagi tugmani bosing."
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


def send_help(message):
    """
    /help buyrug'i uchun javob
    """
    help_text = (
        "Bot imkoniyatlari:\n"
        "- /start - Botni ishga tushirish va menyuni ochish\n"
        "- /help - Yordam xabarini ko'rsatish\n\n"
        "Shuningdek, yangi yangiliklar e'lon qilinganda ushbu bot orqali bildirishnoma olasiz."
    )
    bot.send_message(message.chat.id, help_text)


if BOT_TOKEN:
    bot.message_handler(commands=["start"])(send_welcome)
    bot.message_handler(commands=["help"])(send_help)


def start_bot():
    """
    Botni cheksiz polling rejimida ishga tushirish funksiyasi
    """
    if not bot:
        logger.error("Bot tokeni yo'qligi sababli bot ishga tushmadi!")
        return
    
    logger.info("Telegram bot ishga tushdi...")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    start_bot()