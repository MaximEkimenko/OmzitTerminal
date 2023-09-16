import os
from aiogram import Bot, Dispatcher
TOKEN = os.getenv('RSU_TOKEN')

admin_id = int(os.getenv('ADMIN_TELEGRAM_ID'))
users = (admin_id,)  # админ
masters = (admin_id,)  # мастера

bot = Bot(token=TOKEN)  # инициализация бота
dp = Dispatcher(bot)  # инициализация диспетчера


async def send_call_master(message_to_master):
    """ Функция вызова мастера. Импортируется в terminal_listener"""
    await bot.send_message(chat_id=admin_id, text=message_to_master)
