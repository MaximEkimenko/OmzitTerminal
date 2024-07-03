import os
from m_logger_settings import logger
from asyncio import sleep

from aiogram import Bot, Dispatcher

TOKEN = os.getenv('RSU_TOKEN')

bot = Bot(token=TOKEN)  # инициализация бота
dp = Dispatcher(bot)  # инициализация диспетчера

# группа мастеров
omzit_master_group1_id = -4005524766
omzit_master_group2_id = -4109421151
# test groups
# omzit_master_group1_id = os.getenv('ADMIN_TELEGRAM_ID')
# omzit_master_group2_id = os.getenv('ADMIN_TELEGRAM_ID')


async def send_call_master(message_to_master, ws_number):
    """
    Отправка сообщения в группу мастерам
    :param message_to_master:
    :param ws_number: номер терминала
    :return:
    """
    ws_numbers_c1 = ('11', '12', '13', '14', '15', '16')
    ws_numbers_c2 = ('22', '23', '24', '25', '26', '27', '28', '29', '210', '211')
    if str(ws_number) in ws_numbers_c1:
        await bot.send_message(chat_id=omzit_master_group1_id, text=message_to_master)
    elif str(ws_number) in ws_numbers_c2:
        await bot.send_message(chat_id=omzit_master_group2_id, text=message_to_master)
    else:
        logger.error(f'Ошибка отправки сообщения мастеру в цехе №{ws_number}, {message_to_master}')


async def send_call_dispatcher(message_to_master, ws_number):
    """
    #TODO разделено с send_call_master для дальнейшего добавления функционала
    Отправка сообщения в группу мастерам для диспетчера
    :param message_to_master:
    :param ws_number: номер терминала
    :return:
    """
    ws_numbers_c1 = ('11', '12', '13', '14', '15', '16')
    ws_numbers_c2 = ('22', '23', '24', '25', '26', '27', '28', '29', '210', '211')
    if str(ws_number) in ws_numbers_c1:
        await bot.send_message(chat_id=omzit_master_group1_id, text=message_to_master)
    elif str(ws_number) in ws_numbers_c2:
        await bot.send_message(chat_id=omzit_master_group2_id, text=message_to_master)
    else:
        logger.error(f'Ошибка отправки сообщения мастеру в цехе №{ws_number}, {message_to_master}')


async def terminal_message_to_id(to_id, text_message_to_id):
    """
    TODO не используется
    Отправляет сообщение для id
    :param to_id: получатель
    :param text_message_to_id: текст сообщения
    :return:
    """
    await bot.send_message(chat_id=to_id, text=text_message_to_id)


def get_client_ip(request):
    """
    Получение IP из запроса
    :param request:
    :return: None
    """
    # print('\nCOMPUTERNAME = ', request.META['COMPUTERNAME'])
    # print('\nSERVER_NAME = ', request.META['SERVER_NAME'])
    # print('\nREMOTE_ADDR = ', request.META['REMOTE_ADDR'])
    # print('\nHTTP_USER_AGENT = ', request.META['HTTP_USER_AGENT'])
    # print('\nUSERNAME = ', request.META['USERNAME'])
    return request.META.get('REMOTE_ADDR')


