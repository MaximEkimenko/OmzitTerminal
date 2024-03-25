from django import forms
from scheduler.models import ShiftTask
from django.forms import ModelChoiceField


# TODO ЗАКОНСЕРВИРОВАНО Функционал простоев
# from django.forms import ChoiceField

class WorkplaceChooseLabel(ModelChoiceField):  # переопределение метода отображения строки результатов для ФИО
    """
    Класс для переопределения вывода ModelChoiceField для формы WorkplaceChoose
    """

    def label_from_instance(self, obj):
        return obj.ws_number


class WorkplaceChoose(forms.Form):
    """
    Форма для выбора РЦ
    """
    query_set = ShiftTask.objects.all().distinct('ws_number')
    ws_number = WorkplaceChooseLabel(queryset=query_set, empty_label='РЦ не выбран',
                                     label='Выберите номер РЦ')

# class ShiftTaskChoose(forms.Form):
#     query_set = ShiftTask.objects.all().distinct('ws_number')
#     ws_number = WorkplaceChooseLabel(queryset=query_set, empty_label='РЦ не выбран',
#                                      label='Выберите номер РЦ')

# TODO ЗАКОНСЕРВИРОВАНО Функционал простоев
# class DowntimeReasonForm(forms.Form):
#     """
#     Форма для выбора причины простоя
#     """
#     REASONS = (
#         ("", 'Выберите причину простоя'),
#         ("Вызов диспетчера", "Вызов диспетчера"),
#         ("Вызов конструктора", "Вызов конструктора"),
#         ("Вызов технолога", "Вызов технолога"),
#     )
#
#     reason = ChoiceField(
#         choices=REASONS,
#         label='',
#         required=False,
#         widget=forms.SelectMultiple(attrs={'class': 'reason_select', 'size': '10'})
#     )
