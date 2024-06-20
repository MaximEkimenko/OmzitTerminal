from typing import NewType

TelegramID = NewType("TelegramID", int)

orders_telegram_group_id = TelegramID(-4280998525)
# orders_telegram_group_id = TelegramID(177201205)  # в целях тестирования

# номера начальников цехов
# ключ - идентификатор цеха
shop_chief_telegram_ids = {
    "Цех № 1": [TelegramID(2051721470), TelegramID(522102996)],
    "Цех № 2": [TelegramID(6424114889), TelegramID(1377896858)],
    "Цех № 3": [TelegramID(1148106959), TelegramID(1293843639)],
}
