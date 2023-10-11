import os
from aiogram import Bot, Dispatcher
TOKEN = os.getenv('RSU_TOKEN')

admin_id = int(os.getenv('ADMIN_TELEGRAM_ID'))
users = (admin_id,)  # админ
masters = (admin_id,)  # мастера

bot = Bot(token=TOKEN)  # инициализация бота
dp = Dispatcher(bot)  # инициализация диспетчера

master_list = [admin_id]
dispatcher_list = [admin_id]


async def send_call_master(message_to_master):
    await bot.send_message(chat_id=admin_id, text=message_to_master)


async def send_call_dispatcher(message_to_master):
    await bot.send_message(chat_id=admin_id, text=message_to_master)


async def terminal_message_to_id(to_id, text_message_to_id):
    """
    Отправляет сообщение для id
    :param to_id: получатель
    :param text_message_to_id: текст сообщения
    :return:
    """
    await bot.send_message(chat_id=to_id, text=text_message_to_id)
