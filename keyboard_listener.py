from pynput import keyboard
from pynput.keyboard import Key, Controller
keyboard_class = Controller()


print("keyboard listener started!")
def on_press(key):
    try:
        if key.char == 'j' or key.char == 'о':
            keyboard_class.press(Key.backspace)
            keyboard_class.press(Key.down)
        if key.char == 'a' or key.char == 'ф':
            keyboard_class.press(Key.backspace)
            keyboard_class.press(Key.up)
        if key.char == 's' or key.char == 'ы':
            keyboard_class.press(Key.backspace)
            keyboard_class.press(Key.enter)
        if key.char == 'k' or key.char == 'л':
            keyboard_class.press(Key.backspace)
            keyboard_class.press(Key.tab)
        if key.char == ';' or key.char == 'ж':
            print('Вызов мастера')



        print(key.char)
    except AttributeError:
        print(key)
    pass


def win32_event_filter(msg, data):
    # if data.vkCode == 0x4A:
    #     keyboard_class.press(Key.down)
    #     listener.suppress_event()
    pass

# def on_release(key):
#     print('{0} released'.format(key))
#     if key == keyboard.Key.esc:
#         # Stop listener
#         return False


# with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
with keyboard.Listener(on_press=on_press, win32_event_filter=win32_event_filter, on_release=None) as listener:
    listener.join()

# listener = keyboard.Listener(on_press=on_press)
# listener.start()
# listener.wait()
