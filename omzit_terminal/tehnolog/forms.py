from django import forms


from .models import ProductCategory
from scheduler.models import WorkshopSchedule, model_pattern, model_error_text, order_pattern, order_error_text
from constructor.forms import QueryAnswerForm

# TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
# from django.forms import ModelChoiceField, formset_factory, ChoiceField
# from scheduler.models import Doers, ShiftTask
# from constructor.forms import MultipleFileField, MultipleFileInput


class GetTehDataForm(forms.Form):
    """
    Запись технологических данных из Excel
    """
    # список имен листов книги для чтения

    query_set = WorkshopSchedule.objects.exclude(td_status__in=('завершено', 'запрошено'))
    model_order_query = QueryAnswerForm(query_set, empty_label='выберите заказ-модель',
                                        label='Заказ модель', required=False)

    list_names = forms.CharField(max_length=255, label='Имя листа Excel для загрузки')
    # список исключений
    # exception_names = forms.CharField(max_length=255, label='Список листов исключений', required=False)
    excel_file = forms.FileField(label='Файл excel трудоемкости')  # файл Excel


class ChangeOrderModel(forms.Form):
    """
    Изменение заказ-модели
    """
    query_set = WorkshopSchedule.objects.filter(order_status='не запланировано').exclude(td_status='завершено')
    model_order_query = QueryAnswerForm(query_set, empty_label='выберите заказ-модель',
                                        label='Заказ модель', required=False)

    order_query = forms.CharField(max_length=50, label='Новое имя заказа',
                                  widget=forms.TextInput(attrs={'pattern': order_pattern, 'title': order_error_text}))
    model_query = forms.CharField(max_length=50, label='Новое имя модели',
                                  widget=forms.TextInput(attrs={'pattern': model_pattern, 'title': model_error_text}))


class SendDrawBack(forms.Form):
    """Отправка чертежей на доработку"""
    query_set = WorkshopSchedule.objects.all().exclude(td_status='завершено').exclude(td_status='запрошено')
    model_order_query = QueryAnswerForm(query_set, empty_label='выберите заказ-модель',
                                        label='Заказ модель', required=False)
    td_remarks = forms.CharField(widget=forms.Textarea, label='Содержание замечания')

# TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
# class TehnologChoice(forms.Form):
#     """Выбор технолога для распределения (Плазма)"""
#     fios_tehnolog = Doers.objects.filter(job_title="Технолог")
#     fio = ModelChoiceField(
#         fios_tehnolog,
#         label='Технолог',
#         required=False,
#         empty_label='Не распределено',
#         widget=forms.Select(attrs={'class': 'name_select_option tehnolog_select'})
#     )
#
#
# class DoerChoice(forms.Form):
#     """Выбор исполнителя для распределения (Плазма)"""
#     fios_doer = Doers.objects.exclude(job_title="Технолог")
#     fio = ModelChoiceField(
#         fios_doer,
#         label='Исполнитель',
#         required=False,
#         widget=forms.Select(attrs={'class': 'name_select_option doer_select'})
#     )
#
#
# WS_PLASMA_CHOICES = (("", 'Не определен'), ("102", 1), ("202", 2))
#
#
# class WorkshopPlasmaChoice(forms.Form):
#     """Выбор цеха плазмы"""
#     ws = ChoiceField(
#         choices=WS_PLASMA_CHOICES,
#         label='Цех плазмы',
#         required=False,
#         widget=forms.Select(attrs={'class': 'name_select_option plasma_select'})
#     )
#
#
# class LayoutUpload(forms.Form):
#     """
#     Загрузка раскладки
#     """
#
#     file = MultipleFileField(label='Файл раскладки (cnc/csv)',
#                              widget=MultipleFileInput(attrs={'accept': ".cnc,.csv"}))
