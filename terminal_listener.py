
from pynput import keyboard
from pynput.keyboard import Key, Controller
keyboard_class = Controller()  # управление клавиатурой
WS_NUMBER = '109'
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
        # TODO удалить при рефекторинге:
        # в переводе кнопки вызова мастера нет необходимости, как и в кнопке перехода на чертеж
        # if key.char == ';' or key.char == 'ж':  # кнопка вызов мастера
        #    pass
        print('CHAR:', key.char)
    except AttributeError:
        print('KEY:', key)


with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

