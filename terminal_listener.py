import time

from pynput import keyboard
from pynput.keyboard import Key, Controller
from test_bot import send_call_master
from terminal_db import select_master_call
import asyncio

keyboard_class = Controller()  # управление клавиатурой

WS_NUMBER = "109"  # номер рабочего центра к которому привязан терминал

print("keyboard listener started!")
def on_press(key):
    try:
        if key.char == 'j' or key.char == 'о':  # кнопка вниз
            keyboard_class.press(Key.backspace)
            keyboard_class.press(Key.down)
        if key.char == 'a' or key.char == 'ф':  # кнопка вверх
            keyboard_class.press(Key.backspace)
            keyboard_class.press(Key.up)
        if key.char == 's' or key.char == 'ы':  # кнопка сменное задание
            keyboard_class.press(Key.backspace)
            keyboard_class.press(Key.enter)
        if key.char == 'k' or key.char == 'л':  # кнопка +
            keyboard_class.press(Key.backspace)
            keyboard_class.press(Key.tab)
        if key.char is None:  # кнопка чертёж
            keyboard_class.press(Key.f5)

        if key.char == ';' or key.char == 'ж':  # кнопка вызов мастера
            keyboard_class.press(Key.enter)
            # отправка вызова мастеру
            print('Вызов мастера')
            # выборка вызовов мастера на РЦ WS_NUMBER
            time.sleep(5)
            messages = select_master_call(WS_NUMBER)
            print('messages=', messages)
            if messages:
                for message in messages:
                    asyncio.run(send_call_master(message))  # отправка мастеру в телеграм ботом
            print('Окончание вызова')

        print('CHAR:', key.char)
    except AttributeError:
        print('KEY:', key)


def win32_event_filter(msg, data):
    # if data.vkCode == 0xA4:
    #     listener.suppress_event()
    pass



def on_release(key):
    # try:
    #     if Key.alt_l:
    #         keyboard_class.press(Key.f5)
    # except AttributeError:
    #     print('KEY:', key)
    pass

# def on_press(key):
#     try:
#         print('alphanumeric key {0} pressed'.format(
#             key.char))
#     except AttributeError:
#         print('special key {0} pressed'.format(
#             key))


# with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
with keyboard.Listener(on_press=on_press, win32_event_filter=win32_event_filter, on_release=on_release) as listener:
    listener.join()

# listener = keyboard.Listener(on_press=on_press)
# listener.start()
# listener.wait()
from pynput import keyboard


