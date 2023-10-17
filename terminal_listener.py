import time

from pynput import keyboard
from pynput.keyboard import Key, Controller
keyboard_class = Controller()  # управление клавиатурой

print("waiting for browser...")
time.sleep(30)
keyboard_class.press(Key.f11)
keyboard_class.release(Key.f11)
print("keyboard listener started!")


def on_press(key):
    """
    Программа перевода сигналов от нажимаемых кнопок пульта в нужные действия
    :param key:
    :return:
    """

    try:
        if key.char == 's' or key.char == 'ы':  # кнопка вверх
            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)
            keyboard_class.press(Key.up)
            keyboard_class.release(Key.up)

        if key.char == 'b' or key.char == 'и':  # кнопка вправо
            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)
            keyboard_class.press(Key.right)
            keyboard_class.release(Key.right)

        if key.char == 'e' or key.char == 'у':  # кнопка вниз
            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)
            keyboard_class.press(Key.down)
            keyboard_class.release(Key.down)

        if key.char == 'd' or key.char == 'в':  # кнопка влево
            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)
            keyboard_class.press(Key.left)
            keyboard_class.release(Key.left)

        if key.char == 'v' or key.char == 'м':  # кнопка '+'

            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)

            keyboard_class.press(Key.ctrl_l)
            keyboard_class.press('=')

            keyboard_class.release(Key.ctrl_l)
            keyboard_class.release('=')

        if key.char == 'z' or key.char == 'я':  # кнопка '-'
            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)

            keyboard_class.press(Key.ctrl_l)
            keyboard_class.press('-')

            keyboard_class.release(Key.ctrl_l)
            keyboard_class.release('-')

        print('CHAR:', key.char)
    except AttributeError:
        print('KEY:', key)


with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

