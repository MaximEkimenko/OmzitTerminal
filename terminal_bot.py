import datetime
import logging
import os
import re
import time

from aiogram import Bot, Dispatcher, executor, types, filters
# работа с БД
from terminal_db import (ws_list_get, status_change_to_otk, st_list_get, master_id_get, control_man_id_set,
                         decision_data_set)

logging.basicConfig(filename="log.log", level=logging.DEBUG, filemode='w',
                    format=' %(levelname)s - %(asctime)s; файл - %(filename)s; сообщение - %(message)s')
TOKEN = os.getenv('RSU_TOKEN')

# ids
admin_id = int(os.getenv('ADMIN_TELEGRAM_ID'))
posohov_id = 2051721470  # цех 1
ermishkin_id = 5221029965
gordii_id = 6374431046
kondratiev_id = 6125791135
achmetov_id = 1153114403

savchenko_id = 2131171377  # ПДО
pavluchenkova_id = 1151694995

averkina_id = 1563020113  # ОТК
donskaya_id = 6359131276

mhitaryan_id = 413559952  # ПКО
saks_id = 1366631138  # ОГТ
# groups
omzit_otk_group_id = -981440150
terminal_group_id = -908012934
omzit_master_group1_id = -4005524766
# fios
id_fios = {admin_id: 'Екименко М.А.',
           posohov_id: 'Посохов О.С.',
           ermishkin_id: 'Ермишкин В.М.',  # Мастера
           gordii_id: 'Гордий В.В.',
           kondratiev_id: 'Кондратьев П.В.',
           achmetov_id: 'Ахметов К.',
           savchenko_id: 'Савченко Е.Н.',  # ПДО
           pavluchenkova_id: 'Павлюченкова Н. Л.',
           donskaya_id: 'Донская Ю.Г.',  # ОТК
           averkina_id: 'Аверкина О.В.',
           mhitaryan_id: 'Мхитарян К.',  # ПКО
           saks_id: 'Сакс В.И.'  # ОГТ

           }

# пользователи имеющие доступ
users = (admin_id,  # root
         posohov_id, ermishkin_id, gordii_id, kondratiev_id, achmetov_id,  # производство
         savchenko_id, pavluchenkova_id,  # ПДО
         donskaya_id, averkina_id,  # ОТК
         mhitaryan_id,  # ПКО
         saks_id,  # ОГТ
         )

masters = (admin_id, ermishkin_id, posohov_id, gordii_id, kondratiev_id, achmetov_id)  # производство

dispatchers = (admin_id, savchenko_id, pavluchenkova_id,)  # диспетчеры

control_mans_list = (admin_id, donskaya_id, averkina_id)  # контролёры

bot = Bot(token=TOKEN)  # инициализация бота
dp = Dispatcher(bot)  # инициализация диспетчера

# шаблоны re для callback
pattern_call_otk = r'(call)\d\d'  # шаблон для вызова ОТК
pattern_answ_otk = r'(answ)\d\d'  # шаблон для ответа ОТК
pattern_dcgo_otk = r'(dcgo)\d\d'  # шаблон запуска решения
pattern_stid_otk = r'(stid)\d'  # шаблон для вызова вариантов решений ОТК
pattern_dscn_otk = r'(dcsn)\d'  # шаблон принятого решения ОТК


async def on_startup(_):  # функция выполняется при запуске бота
    # await bot.send_message(admin_id, "Бот РСУ вышел в онлайн.")
    print(f'Terminal_bot вышел онлайн в {datetime.datetime.now().strftime("%H:%M:%S")}.')


def call_get_re(pattern: str, call: str) -> str:
    """
    Функция получения строки из pattern re. Используется в lambda в call_back_handler вместо фильтра regexp
    :param pattern: шаблон re
    :param call: строка для проверки
    :return: string
    """
    try:
        result_string = re.match(pattern, call).string
        # print(result_string)
    except Exception as e:
        result_string = ''
        print('ошибка определения RegExp', e)

    return result_string


@dp.message_handler(commands=['start'])
async def start_rsu_bot(message: types.Message):
    await message.reply(text='Вас приветствует бот для работы с терминалами ЗАО ОмЗиТ! Чтобы воспользоваться ботом '
                             'используйте меню.')


@dp.message_handler(commands=['help'])
async def help_rsu_bot(message: types.Message):
    if message.from_user.id in users:
        await message.reply(text='Здесь будет инструкция.')


# TODO docstring для всх обработчиков
# TODO разграничить права доступа
# TODO переводчик всех id в ФИО
# ------------------------------------------------ Мастер вызывает контролёра
# отображение inline ws_number для мастера при вызове ОТК. Обработка команды otk_send
@dp.message_handler(commands=['otk_send'])
async def master_otk_send(message: types.Message):
    # TODO если вызовов мастера нет, то ответ, что вызовов для контролёра делать не откуда
    if message.from_user.id in masters:
        # создание inline keyboard РЦ со статусом ожидание мастера
        inline_ws_buttons = types.InlineKeyboardMarkup()  # объект
        ws_list = ws_list_get("ожидание мастера")
        for ws in ws_list:
            btn = types.InlineKeyboardButton(text=f'{ws}', callback_data=f'call{ws}{message.from_user.id}')
            inline_ws_buttons.insert(btn)
        await message.answer('Выбор терминала', reply_markup=inline_ws_buttons)
    else:
        await message.reply('У вас нет доступа к этому функционалу.')


# обработчик callback otk_send вызова контролёра МАСТЕРОМ на РЦ
@dp.callback_query_handler(lambda callback: call_get_re(pattern_call_otk, callback.data[:-10]))
async def otk_call(callback_query: types.CallbackQuery):
    master_id = callback_query.data[-10:]  # id мастера
    ws_number = callback_query.data[4:-10]  # номер РЦ
    print(ws_number, len(ws_number), type(ws_number))
    print(master_id, len(master_id), type(master_id))
    # print(callback_query.data)
    # print(ws_number, master_id)
    # отправка сообщения о заявке на контролёра в группу ОТК
    await bot.send_message(chat_id=omzit_otk_group_id, text=f"Контролёра ожидают на Т{ws_number}. Запрос от "
                                                            f"{id_fios[int(master_id)]}")
    # Обратная связь мастеру
    await bot.send_message(chat_id=master_id, text="Запрос в отк отправлен.")
    # Статус ожидание контролёра
    status_change_to_otk(ws_number=ws_number, initiator_id=master_id)
    await callback_query.answer()  # закрытие inline кнопок


# ------------------------------------------------


# ------------------------------------------------ Контролёр отвечает мастеру
# отображение inline ws_number для контролёра при ответе на запрос. Обработка команды otk_answer.
@dp.message_handler(commands=['otk_answer'])
async def otk_answer_master_send(message: types.Message):
    # TODO если запросов на контролёра  нет, то ответ - нет запросов на контролёра не было
    if message.from_user.id in control_mans_list:
        # создание inline keyboard РЦ со статусом ожидание контролёра
        inline_ws_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок РЦ
        ws_list = ws_list_get("ожидание контролёра")
        for ws in ws_list:
            btn = types.InlineKeyboardButton(text=f'{ws}', callback_data=f'answ{ws}{message.from_user.id}')
            inline_ws_buttons.insert(btn)
        await message.answer('Выбор терминала', reply_markup=inline_ws_buttons)
    else:
        await message.reply('У вас нет доступа к этому функционалу.')


# обработчик callback otk_answer ответа контролёра МАСТЕРУ на РЦ
@dp.callback_query_handler(lambda callback: call_get_re(pattern_answ_otk, callback.data[:-10]))
async def otk_call(callback_query: types.CallbackQuery):
    controlman_id = callback_query.data[-10:]  # id контролёра
    ws_number = callback_query.data[4:-10]  # номер РЦ
    # TODO Получить статус по номеру РЦ, если ожидание контролёра, то ответ, что нет
    # запрос в БД на id мастера
    master_id = master_id_get(ws_number=ws_number)[0]
    # отправка сообщения о заявке на контролёра в группу ОТК
    await bot.send_message(chat_id=omzit_otk_group_id,
                           text=f"Контролёр {id_fios[int(controlman_id)]} ответил на запрос Т{ws_number}.")
    # обратная связь мастеру
    await bot.send_message(chat_id=master_id, text=f"Контролёр {id_fios[int(controlman_id)]} ответил "
                                                   f"на запрос Т{ws_number}.")
    # сообщение в личку контролёру
    await bot.send_message(chat_id=controlman_id, text=f"Вы ответили на запрос Т{ws_number}.")
    # Запись в БД информации об ответе контролёра
    control_man_id_set(ws_number, controlman_id)
    await callback_query.answer()


# ------------------------------------------------


# ------------------------------------------------ Контролёр принимает решение
# отображение inline для решения отк. Обработка команды otk_decision
@dp.message_handler(commands=['otk_decision'])
async def otk_answer_master_send(message: types.Message):
    # TODO если статуса ожидания нет, то ответ, что контролёра не ждут
    if message.from_user.id in control_mans_list:
        # создание inline keyboard РЦ со статусом ожидание контролёра
        inline_ws_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок РЦ
        ws_list = ws_list_get("ожидание контролёра")
        for ws in ws_list:
            btn = types.InlineKeyboardButton(text=f'{ws}', callback_data=f'dcgo{ws}{message.from_user.id}')
            inline_ws_buttons.insert(btn)
        await message.answer('Выбор терминала для принятия решения:', reply_markup=inline_ws_buttons)
    else:
        await message.reply('У вас нет доступа к этому функционалу.')


# обработчик callback otk_decision принятия решения по СЗ на РЦ для отображение инлайн СЗ
@dp.callback_query_handler(lambda callback: call_get_re(pattern_dcgo_otk, callback.data[:-10]))
async def otk_answer(callback_query: types.CallbackQuery):
    controlman_id = callback_query.data[-10:]  # id контролёра
    ws_number = callback_query.data[4:-10]  # номер РЦ
    print('call_data=', callback_query.data)
    print(ws_number)
    inline_st_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок номера СЗ
    # получение списка СЗ
    shift_task_list = st_list_get(ws_number)
    # print('shift_task_list = ', shift_task_list)
    for task in shift_task_list:
        print(task)
        print([str(task).find("|") - 1])
        shift_task_id = task[2:str(task).find("|") - 1]  # id СЗ
        # print(shift_task_id)
        btn = types.InlineKeyboardButton(text=f'{task}',
                                         callback_data=f'stid{shift_task_id}{controlman_id}')
        # print(f'stid{shift_task_id}{controlman_id}')
        inline_st_buttons.add(btn)
    await bot.send_message(chat_id=controlman_id, text=f'для Т{ws_number} выберите СЗ:',
                           reply_markup=inline_st_buttons)
    await callback_query.answer()  # закрытие inline кнопок


# обработчик callback otk_decision принятия решения по СЗ на РЦ отображение инлайн кнопок для принятия решения
@dp.callback_query_handler(lambda callback: call_get_re(pattern_stid_otk, callback.data[:-10]))
async def otk_decision(callback_query: types.CallbackQuery):
    controlman_id = callback_query.data[-10:]  # id контролёра
    # print(controlman_id)
    st_id = callback_query.data[4:-10]  # id СЗ
    # print(st_id)
    inline_dcsn_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок решения контролёра
    # получение списка СЗ
    btn_good = types.InlineKeyboardButton(text=f'ПРИНЯТО', callback_data=f'dcsn{st_id}1{controlman_id}')
    btn_bad = types.InlineKeyboardButton(text=f'БРАК', callback_data=f'dcsn{st_id}2{controlman_id}')
    btn_miss = types.InlineKeyboardButton(text=f'НЕ ПРИНЯТО', callback_data=f'dcsn{st_id}3{controlman_id}')
    inline_dcsn_buttons.add(btn_good)
    inline_dcsn_buttons.add(btn_bad)
    inline_dcsn_buttons.add(btn_miss)
    await bot.send_message(chat_id=controlman_id, text=f'Для СЗ №{st_id}:', reply_markup=inline_dcsn_buttons)
    await callback_query.answer()  # закрытие inline кнопок


# обработчик callback записи данных по решению в базу и выдаче обратной связи мастеру
@dp.callback_query_handler(lambda callback: call_get_re(pattern_dscn_otk, callback.data[:-10]))
async def otk_answer(callback_query: types.CallbackQuery):
    st_id = callback_query.data[4:-11]  # id СЗ
    print(st_id)
    controlman_id = callback_query.data[-10:]  # id контролёра
    print(controlman_id)
    if callback_query.data[-11:-10] == '1':  # решение контролёра
        decision = 'принято'
    elif callback_query.data[-11:-10] == '2':
        decision = 'брак'
    else:
        decision = 'не принято'
    print(decision)
    # запрос из базы на РЦ и id мастера
    master_id, ws_number = master_id_get(st_id=st_id)
    # запись в базу
    decision_data_set(st_id, controlman_id, decision)
    # Сообщение в группу
    await bot.send_message(chat_id=omzit_otk_group_id,
                           text=f'Контролёр {id_fios[int(controlman_id)]} определил "{decision}" на Т{ws_number} '
                                f'для СЗ №{st_id}')
    # сообщение в личку
    await bot.send_message(chat_id=controlman_id,
                           text=f'Вы определили "{decision}" на Т{ws_number} для СЗ №{st_id}')
    # сообщение мастеру
    await bot.send_message(chat_id=master_id,
                           text=f'Контролёр {id_fios[int(controlman_id)]} определил "{decision}" на Т{ws_number} '
                                f'для СЗ №{st_id}')
    await callback_query.answer()  # закрытие inline кнопок


# ------------------------------------------------


async def on_shutdown(_):  # функция выполняется при завершении работы бота
    # await bot.send_message(admin_id, "Bot is offline!")
    print('Бот офлайн.')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown, timeout=10)
