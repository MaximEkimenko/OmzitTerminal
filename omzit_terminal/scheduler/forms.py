from django import forms
from tehnolog.models import ProductModel
from .models import ShiftTask, WorkshopSchedule, Doers
from django.forms import ModelChoiceField


class SchedulerWorkshop(forms.Form):
    """
    Форма для ввода графика цеха
    """
    order = forms.CharField(max_length=50, label='Номер заказа')
    query_set = ProductModel.objects.all()
    model_name = forms.ModelChoiceField(queryset=query_set, empty_label='Модель не выбрана',
                                        label='Модель заказа')
    workshop = forms.ChoiceField(choices=((1, 'Цех 1'), (2, 'Цех 2'), (3, 'Цех 3'), (4, 'Цех 4')), label='Цех')
    datetime_done = forms.DateField(label='Планируемая дата готовности')


class SchedulerWorkplaceLabel(ModelChoiceField):  # переопределение метода отображения строки результатов для ФИО
    """
    Класс для переопределения вывода ModelChoiceField
    """
    def label_from_instance(self, obj):
        return obj.ws_number



class SchedulerWorkplace(forms.Form):  # TODO переопределить вывод!
    """
    Форма для ввода графика РЦ
    """
    query_set_wp = ShiftTask.objects.all().distinct('ws_number')
    ws_number = SchedulerWorkplaceLabel(queryset=query_set_wp, empty_label='РЦ не выбран', label='Рабочий центр', required=False)
    query_set_datetime_done = WorkshopSchedule.objects.all().distinct('datetime_done')
    try:
        datetime_done = forms.ModelChoiceField(queryset=query_set_datetime_done, empty_label='Дата готовности не выбрана',
                                               label='Планируемая дата готовности', required=False)
    except Exception as e:
        print(e)


class FiosLabel(ModelChoiceField):  # переопределение метода отображения строки результатов для ФИО
    """
    Класс для переопределения вывода ModelChoiceField
    """
    def label_from_instance(self, obj):
        return f"{obj.id}. Заказ - {obj.order}. №РЦ- {obj.ws_number}. Изделие - {obj.model_name}"


class FioDoer(forms.Form):
    """
    Форма для ввода ФИО
    """
    qs_st_number = ShiftTask.objects.filter(fio_doer="не распределено")
    st_number = FiosLabel(qs_st_number, label='Сменное задание', empty_label='СЗ не выбрано')
    qs_st_fio = Doers.objects.all()
    fio_1 = forms.ModelChoiceField(qs_st_fio, label='ФИО исполнителя 1', empty_label='ФИО не выбрано')
    fio_2 = forms.ModelChoiceField(qs_st_fio, label='ФИО исполнителя 2', empty_label='ФИО не выбрано', initial=8, required=False)
    fio_3 = forms.ModelChoiceField(qs_st_fio, label='ФИО исполнителя 3', empty_label='ФИО не выбрано', initial=8, required=False)
    fio_4 = forms.ModelChoiceField(qs_st_fio, label='ФИО исполнителя 4', empty_label='ФИО не выбрано', initial=8, required=False)

