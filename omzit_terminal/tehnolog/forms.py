from django import forms
from .models import ProductCategory
from scheduler.models import WorkshopSchedule, model_pattern, model_error_text, order_pattern, order_error_text
from constructor.forms import QueryAnswerForm


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
    model_query = forms.CharField(max_length=50, label='Новое имя модели',
                                  widget=forms.TextInput(attrs={'pattern': model_pattern, 'title': model_error_text}))
    order_query = forms.CharField(max_length=50, label='Новое имя заказа',
                                  widget=forms.TextInput(attrs={'pattern': order_pattern, 'title': order_error_text}))


class SendDrawBack(forms.Form):
    """Отправка чертежей на доработку"""
    query_set = WorkshopSchedule.objects.all().exclude(td_status='завершено').exclude(td_status='запрошено')
    model_order_query = QueryAnswerForm(query_set, empty_label='выберите заказ-модель',
                                        label='Заказ модель', required=False)
    td_remarks = forms.CharField(widget=forms.Textarea, label='Содержание замечания')

