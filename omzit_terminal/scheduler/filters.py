import django_filters
from django import forms
from django_filters import ChoiceFilter

from .models import ShiftTask

SHIFT_TASK_FILTER_FIELDS = ('order', 'model_name', 'datetime_done', 'fio_doer')


class ShiftTaskFilter(django_filters.FilterSet):
    fields_values = {field: set() for field in SHIFT_TASK_FILTER_FIELDS}

    tasks = ShiftTask.objects.values('order', 'model_name', 'datetime_done', 'fio_doer')
    for task in tasks:
        for field, value in task.items():
            print(value)
            if field == 'fio_doer' and ',' in value:
                for fio in value.split(', '):
                    fields_values[field].add((fio, fio))
            else:
                fields_values[field].add((value, value))


    order = ChoiceFilter(
        choices=fields_values['order'],
        widget=forms.Select(attrs={
                'onchange': "onChange()"
        }))
    model_name = ChoiceFilter(
        choices=fields_values['model_name'],
        widget=forms.Select(attrs={
                'onchange': "onChange()"
        }))
    datetime_done = ChoiceFilter(
        choices=fields_values['datetime_done'],
        widget=forms.Select(attrs={
                'onchange': "onChange()"
        }))
    fio_doer = ChoiceFilter(
        choices=fields_values['fio_doer'],
        lookup_expr='icontains',
        widget=forms.Select(attrs={
            'onchange': "onChange()"
        }))

    class Meta:
        model = ShiftTask
        fields = SHIFT_TASK_FILTER_FIELDS

