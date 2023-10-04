from django import forms
# from tehnolog.models import ProductModel
from django.forms import ModelChoiceField
from django.db.models import Q
from scheduler.models import ShiftTask, WorkshopSchedule, Doers
from django.forms import ClearableFileInput, FileField
from django.core.validators import FileExtensionValidator


class QueryAnswerForm(ModelChoiceField):  # переопределение метода отображения строки результатов для ФИО
    """
    Класс для переопределения вывода ModelChoiceField
    """

    def label_from_instance(self, obj):
        return obj.model_order_query


# класс загрузки нескольких файлов
class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True  # установка разрешения на множественную загрузку
    template_name = 'input_file_template.html'  # новый шаблон для тега только pdf


# переопределение класса множественной загрузки
class MultipleFileField(FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class QueryAnswer(forms.Form):
    """
    Форма ответа на заявку КД
    """
    query_set = WorkshopSchedule.objects.all().exclude(td_status='завершено')
    model_order_query = QueryAnswerForm(query_set, empty_label='выберите заказ-модель',
                                        label='Заказ модель', required=False)
    draw_files = MultipleFileField(label='Чертежи pdf')


class DrawsAdding(forms.Form):
    """
    Форма добавления файлов без заявки
    """
    pass
