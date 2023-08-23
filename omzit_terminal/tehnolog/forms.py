from django import forms
from .models import ProductCategory, TechData


class GetTehDataForm(forms.Form):
    excel_file = forms.FileField()  # файл Excel
    list_names = forms.CharField(max_length=255)  # список имен листов книги для чтения
    exception_names = forms.CharField(max_length=255)  # список исключений

    query_set = ProductCategory.objects.all()

    category = forms.ModelChoiceField(queryset=query_set, empty_label="")  # выбор категории

