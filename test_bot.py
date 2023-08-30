import datetime
import logging
import os
from aiogram import Bot, Dispatcher, executor, types, filters

TOKEN = os.getenv('RSU_TOKEN')
admin_id = int(os.getenv('ADMIN_TELEGRAM_ID'))
users = (admin_id,  # админ
         )
bot = Bot(token=TOKEN)  # инициализация бота
# scheduler = AsyncIOScheduler()
dp = Dispatcher(bot)  # инициализация диспетчера


async def send_call_master(message_to_master):  # функция вызова мастера
    await bot.send_message(chat_id=admin_id, text=message_to_master)


async def on_startup(_):  # функция выполняется при запуске бота
    # await bot.send_message(admin_id, "Бот РСУ вышел в онлайн.")
    print(f'ТЕСТ БОТ онлайн в {datetime.datetime.now().strftime("%H:%M:%S")}.')


@dp.message_handler(commands=['start'])
async def start_rsu_bot(message: types.Message):
    await message.reply(text=""" """)


@dp.message_handler(commands=['help'])
async def help_rsu_bot(message: types.Message):
    if message.from_user.id in users:
        await message.reply(text='')



# handler для команды вызова ОТК
@dp.message_handler(commands=['otk_send'])
async def report_send(message: types.Message):
    if message.from_user.id in users:
        # создание inline keyboard СЗ на РЦ со статусом ожидание мастера
        inline_buttons_months = types.InlineKeyboardMarkup()  # объект
        # TODO получение списка shift_task_list = [] запросом к БД
        # TODO добавление каждой кнопки
        # for task in shift_task_list:
        #     month_b = types.InlineKeyboardButton(text='', callback_data='')
        #     inline_buttons_months.insert(month_b)
        # TODO отображение каждой кнопки
        # await message.answer('Выберите месяц', reply_markup=inline_buttons_months)
        # сообщение для тестов
        # print()

# TODO handler для команды ответа

# TODO handler для команды решения

#  handler для обработки callback_query.data
@dp.callback_query_handler(lambda callback_query: True)
async def month_select_handler(callback_query: types.CallbackQuery):
     pass






async def on_shutdown(_):  # функция выполняется при завершении работы бота
    # await bot.send_message(admin_id, "Bot is offline!")
    print('Бот офлайн.')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown, timeout=10)
