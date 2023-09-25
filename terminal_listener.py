import time

from pynput import keyboard
from pynput.keyboard import Key, Controller
keyboard_class = Controller()  # управление клавиатурой
print("keyboard listener started!")


def on_press(key):
    """
    Программа перевода сигналов от нажимаемых кнопок пульта в нужные действия
    :param key:
    :return:
    """

    try:
        if key.char == 'a' or key.char == 'ф':  # кнопка вверх
            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)
            keyboard_class.press(Key.up)
            keyboard_class.release(Key.up)

        if key.char == 'f' or key.char == 'а':  # кнопка вправо
            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)
            keyboard_class.press(Key.right)
            keyboard_class.release(Key.right)

        if key.char == 'j' or key.char == 'о':  # кнопка вниз
            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)
            keyboard_class.press(Key.down)
            keyboard_class.release(Key.down)

        if key.char == 'l' or key.char == 'д':  # кнопка влево
            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)
            keyboard_class.press(Key.left)
            keyboard_class.release(Key.left)

        if key.char == 'k' or key.char == 'л':  # кнопка '+'

            keyboard_class.press(Key.backspace)
            keyboard_class.release(Key.backspace)

            keyboard_class.press(Key.ctrl_l)
            keyboard_class.press('=')

            keyboard_class.release(Key.ctrl_l)
            keyboard_class.release('=')

        if key.char == 't' or key.char == 'e':  # кнопка '-'
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

