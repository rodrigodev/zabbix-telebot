import logging
from telebot.bot import TelegramBot

logger = logging.getLogger()
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

telegram_bot = TelegramBot()
