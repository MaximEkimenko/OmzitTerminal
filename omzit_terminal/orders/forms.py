from django import forms
from django.forms import ModelForm, SelectDateWidget
from django.utils.timezone import make_aware
from django.contrib.admin import widgets

from .models import Equipment, Orders, Materials, Shops
from scheduler.forms import Doers
from datetime import date, datetime


class AddEquipmentForm(ModelForm):
    class Meta:
        model = Equipment
        fields = ["name", "inv_number", "shop"]


class EditEquipmentForm(ModelForm):
    class Meta:
        model = Equipment
        fields = [
            "name",
            "inv_number",
            "shop",
            "vendor",
            "model",
            "serial_number",
            "characteristics",
            "description",
        ]


class AddOrderForm(ModelForm):
    class Meta:
        model = Orders
        fields = ["equipment", "priority", "breakdown_description"]

    class Media:
        js = [
            "/static/orders/js/dummy.js",
        ]


# class StartRepairForm(forms.ModelForm):
class StartRepairForm(forms.Form):
    qs_st_fio = Doers.objects.all().order_by("doers")
    fio_1 = forms.ModelChoiceField(
        qs_st_fio,
        label="Исполнитель 1",
        empty_label="ФИО не выбрано",
        widget=forms.Select(attrs={"class": "fio_select"}),
    )
    fio_2 = forms.ModelChoiceField(
        qs_st_fio,
        label="Исполнитель 2",
        empty_label="ФИО не выбрано",
        initial="",
        required=False,
        widget=forms.Select(attrs={"class": "fio_select"}),
    )
    fio_3 = forms.ModelChoiceField(
        qs_st_fio,
        label="Исполнитель 3",
        empty_label="ФИО не выбрано",
        initial="",
        required=False,
        widget=forms.Select(attrs={"class": "fio_select"}),
    )
    fio_4 = forms.ModelChoiceField(
        qs_st_fio,
        label="Исполнитель 4",
        empty_label="ФИО не выбрано",
        initial="",
        required=False,
        widget=forms.Select(attrs={"class": "fio_select"}),
    )


class RepairProgressForm(forms.Form):
    expected_repair_date = forms.DateField(
        label="Ожидаемая дата окончания ремонта",
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d", attrs={"type": "date", "value": date.today().strftime("%Y-%m-%d")}
        ),
        input_formats=["%Y-%m-%d"],  # для календаря срабатывает только такой формат даты
    )

    materials = forms.ModelChoiceField(
        queryset=Materials.objects.all().order_by("name"),
        label="Выбрать пункт с материалами из списка",
    )
    extra_materials = forms.CharField(
        max_length=255, required=False, label="Или указать материалы вручную"
    )


class ConfirmMaterialsForm(forms.ModelForm):
    class Meta:
        model = Orders
        fields = ["materials_request"]


class RepairFinishForm(forms.ModelForm):
    class Meta:
        model = Orders
        fields = [
            "breakdown_cause",
            "solution",
        ]


class RepairCancelForm(forms.ModelForm):
    class Meta:
        model = Orders
        fields = [
            "cancel_cause",
        ]


class RepairRevisionForm(forms.ModelForm):
    class Meta:
        model = Orders
        fields = [
            "revision_cause",
        ]


#
# class OrderEditForm(forms.ModelForm):
#     class Meta:
#         model = Orders
#         fields = [
#             "priority",
#             "breakdown_description",
#             "expected_repair_date",
#             "revision_cause",
#             "materials",
#             "materials_request",
#             "breakdown_cause",
#             "solution",
#         ]


def current_time():
    return make_aware(datetime.now()).strftime("%d.%m.%Y %H:%M")


class OrderEditForm(forms.Form):

    breakdown_description = forms.CharField(
        label="Описание поломки",
        widget=forms.Textarea(attrs={"class": "sz_textarea"}),
        required=False,
    )

    expected_repair_date = forms.DateField(
        label="Ожидаемая дата окончания ремонта",
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )

    materials = forms.ModelChoiceField(
        queryset=Materials.objects.all().order_by("name"), label="Материалы"
    )
    extra_materials = forms.CharField(
        max_length=255, required=False, label="Материалы, которых нет в списке"
    )
    materials_request = forms.CharField(
        max_length=255, required=False, label="№ заявки на материалы"
    )

    breakdown_cause = forms.CharField(
        label="Причина поломки",
        widget=forms.Textarea(attrs={"class": "sz_textarea"}),
        required=False,
    )
    solution = forms.CharField(
        label="Способ устранения",
        widget=forms.Textarea(attrs={"class": "sz_textarea"}),
        required=False,
    )


class AddShop(forms.ModelForm):
    class Meta:
        model = Shops
        fields = ["name"]

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "новое местонахождение", "class": "btn-like"},
        ),
        label="Местонахождение",
    )
