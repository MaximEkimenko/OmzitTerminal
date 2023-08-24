from django import forms
from .models import ProductCategory, TechData


class GetTehDataForm(forms.Form):
    # список имен листов книги для чтения
    list_names = forms.CharField(max_length=255, label='Список листов для расчёта')
    exception_names = forms.CharField(max_length=255, label='Список листов исключений')  # список исключений
    query_set = ProductCategory.objects.all()
    category = forms.ModelChoiceField(queryset=query_set, empty_label='Категория не выбрана',
                                      label='Категория заказа')  # выбор категории
    excel_file = forms.FileField(label='Файл excel трудоемкости')  # файл Excel


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()

