from collections import OrderedDict

import django_filters
from django import forms
from django_filters import ChoiceFilter
from django_filters.constants import ALL_FIELDS


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
