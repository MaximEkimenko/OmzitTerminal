from django import forms
from .models import ProductCategory


class GetTehDataForm(forms.Form):
    # список имен листов книги для чтения
    list_names = forms.CharField(max_length=255, label='Имя модели (листа Excel) для загрузки')
    # список исключений
    exception_names = forms.CharField(max_length=255, label='Список листов исключений', required=False)
    query_set = ProductCategory.objects.all()
    category = forms.ModelChoiceField(queryset=query_set, empty_label='Категория не выбрана',
                                      label='Категория заказа')  # выбор категории
    excel_file = forms.FileField(label='Файл excel трудоемкости')  # файл Excel
