import re
from collections import OrderedDict

import django_filters
from django import forms
from django.db import models
from django.db.models import Q
from django_filters import ChoiceFilter
from django_filters.constants import ALL_FIELDS

from scheduler.models import ShiftTask


class FieldsFilter(django_filters.FilterSet):
    """
    Переопределение класса для создания фильтров в столбцах таблиц
    """

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None, filter_fields, index=''):
        super().__init__(data, queryset)
        self.filter_fields = filter_fields
        self.index = index

    def get_form_class(self):
        fields_values = {field: set() for field in self.filter_fields}
        rows = self.queryset.values(*self.filter_fields)
        for row in rows:
            for field, value in row.items():
                fields_values[field].add((value, value))

        fields = OrderedDict([
            (
                name,
                ChoiceFilter(
                    choices=fields_values[name],
                    widget=forms.Select(attrs={'onchange': f"onChange{self.index}()",
                                               'form': f'filter_form{self.index}',
                                               'style': "width: 20px; height: 20px;"
                                                        "border-radius: 0;"}),
                    empty_label='',
                ).field
            )
            for name, filter_ in self.filters.items()
        ])
        return type(str("%sForm" % self.__class__.__name__), (self._meta.form,), fields)


def get_filterset(data, queryset, model=None, fields=ALL_FIELDS, index=''):
    """
    Получение filterset для передачи в context
    :param data:
    :param queryset:
    :param model:
    :param fields:
    :param index: индекс после имени функции js 'onChange'
    :return: filterset
    """
    if model is None:
        model = queryset.model
    meta = type(str("Meta"), (object,), {"model": model, "fields": fields})
    # имя класса
    filterset_class = type(str("%sFilterSet" % model._meta.object_name), (FieldsFilter,), {"Meta": meta}, )
    # вызов класса
    filterset = filterset_class(data, queryset=queryset, filter_fields=fields, index=index)
    return filterset


def filterset_plasma(request, queryset):
    fields = [
        'id',
        'model_order_query',
        'workpiece__name',
        'workpiece__material',
        'workpiece__count',
        'workpiece__draw',
        'fio_doer',
        'fio_tehnolog',
        'workshop_plasma',
        'plasma_layout',
        'datetime_done'
    ]
    choices = queryset.values(*fields)

    filter_field_material = Q()
    for field, values in dict(request.GET).items():
        if 'workpiece__material' in field:
            field = 'workpiece__material'
            for value in values:
                filter_field_material = filter_field_material | Q(**{f"{field}__icontains": value})
        else:
            for value in values:
                filter_field = {f"{field}": value}
                choices = choices.filter(**filter_field)
    choices = choices.filter(filter_field_material)

    fields_values = {field: set() for field in fields}
    for choice in choices:
        for field in fields:
            if field == 'workpiece__material':
                pattern = r'^(.*)(ГОСТ\s[\d\-]+)*\s(\S+\sГОСТ\s[\d\-]+).*$'
                match = re.match(pattern, choice[field])
                if match:
                    fields_values["workpiece__material_1"] = fields_values.get("workpiece__material_1", set())
                    fields_values["workpiece__material_2"] = fields_values.get("workpiece__material_2", set())
                    fields_values["workpiece__material_1"].add(match.group(1))
                    fields_values["workpiece__material_2"].add(match.group(3))
            else:
                fields_values[field].add(choice[field])

    class_attrs = {}
    for field, values in fields_values.items():
        lookup_expr = "exact"
        field_name = field
        if 'workpiece__material' in field:
            lookup_expr = "icontains"
            field_name = 'workpiece__material'
        class_attrs[field] = django_filters.MultipleChoiceFilter(
            field_name=field_name,
            choices=zip(values, values),
            lookup_expr=lookup_expr,
            widget=forms.SelectMultiple(attrs={'class': 'name_select_option filter_select'}),
        )
    meta = type(str("Meta"), (object,), {"model": queryset.model, "fields": list(class_attrs.keys())})
    class_attrs['Meta'] = meta
    filterset_class = type("PlasmaFilter", (django_filters.FilterSet,), class_attrs)
    return filterset_class(data=request.GET, queryset=queryset)
