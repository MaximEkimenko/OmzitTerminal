from django import forms
from scheduler.models import ShiftTask
from django.forms import ModelChoiceField


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







