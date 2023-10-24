from collections import OrderedDict

import django_filters
from django import forms
from django_filters import ChoiceFilter
from django_filters.constants import ALL_FIELDS


class FieldsFilter(django_filters.FilterSet):

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None, filter_fields):
        super().__init__(data, queryset)
        self.filter_fields = filter_fields

    def get_form_class(self):
        fields_values = {field: set() for field in self.filter_fields}

        rows = self._meta.model.objects.values(*self.filter_fields)
        for row in rows:
            for field, value in row.items():
                fields_values[field].add((value, value))

        fields = OrderedDict([
            (
                name,
                ChoiceFilter(
                    choices=fields_values[name],
                    widget=forms.Select(attrs={'onchange': "onChange()"})
                ).field
            )
            for name, filter_ in self.filters.items()
        ])
        return type(str("%sForm" % self.__class__.__name__), (self._meta.form,), fields)


def get_filterset(data, queryset, model=None, fields=ALL_FIELDS):
    if model is None:
        model = queryset.model
    meta = type(str("Meta"), (object,), {"model": model, "fields": fields})
    filterset_class = type(
        str("%sFilterSet" % model._meta.object_name), (FieldsFilter,), {"Meta": meta}
    )
    filterset = filterset_class(data, queryset=queryset, filter_fields=fields)
    return filterset



