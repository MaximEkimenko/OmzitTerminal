from datetime import date, datetime
from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm, SelectDateWidget
from django.utils.timezone import make_aware
from django.contrib.admin import widgets

from orders.models import Equipment, Orders, Materials, Shops, Repairmen


class AddEquipmentForm(ModelForm):
    shop = forms.ModelChoiceField(
        Shops.objects, label="Местонажождение", required=False, empty_label=None
    )
    days = [(None, "--")]
    days.extend([(i, i) for i in range(1, 32)])
    ppr_plan_day = forms.ChoiceField(choices=days, label="День планового ремонта", required=False)

    class Meta:
        model = Equipment
        fields = ["name", "inv_number", "shop", "ppr_plan_day"]


class EditEquipmentForm(ModelForm):
    shop = forms.ModelChoiceField(
        Shops.objects, label="Местонахождение", required=False, empty_label=None
    )
    days = [(None, "--")]
    days.extend([(i, i) for i in range(1, 32)])
    ppr_plan_day = forms.ChoiceField(choices=days, label="День планового ремонта", required=False)

    class Meta:
        model = Equipment
        fields = [
            "name",
            "inv_number",
            "shop",
            "ppr_plan_day",
            "in_operation",
            "vendor",
            "model",
            "serial_number",
            "characteristics",
            "description",
        ]


class AddOrderForm(ModelForm):
    """
    Форма создания новой заявки на ремонт
    """

    # Для добавления заявки поле shops не требуется, они нужно только для фильтрации оборудования
    # перед созданием объекта из данных формы поле shops удаляется
    shops_qs = Shops.objects.all()
    shops = forms.ModelChoiceField(
        shops_qs,
        label="Фильтр по местоположению",
        required=False,
        widget=forms.Select(attrs={"class": "input_like"}),
    )

    class Meta:
        model = Orders
        fields = ["equipment", "priority", "breakdown_description", "worker"]

class ChangePPRForm(forms.Form):
    pk = forms.IntegerField(widget=forms.HiddenInput())
    days = [(None, "--")]
    days.extend([(i, i) for i in range(1, 32)])
    ppr_plan_day = forms.ChoiceField(choices=days, label="День планового ремонта", required=False)

class AssignWorkersForm(forms.Form):
    # qs_st_fio = Repairmen.assignable_workers.all().order_by("fio")
    qs_st_fio = Repairmen.assignable_workers.all().order_by("fio").only("pk", "fio")
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


class RepairProgressForm(forms.Form):
    expected_repair_date = forms.DateField(
        initial=date.today().strftime("%Y-%m-%d"),
        label="Ожидаемая дата окончания ремонта",
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],  # для календаря срабатывает только такой формат даты
    )

    materials = forms.ModelChoiceField(
        queryset=Materials.objects.all().order_by("name"),
        label="Выбрать пункт с материалами из списка",
    )
    extra_materials = forms.CharField(
        max_length=255, required=False, label="Или указать материалы вручную"
    )

    # Для того, чтобы в форме каждый раз отображалась актуальная дата, нужно применять дату
    # при создании формы, а не при объявлении класса (то есть при запуске сервера)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today().strftime("%Y-%m-%d")
        self.fields["expected_repair_date"].widget.attrs["value"] = today
        self.fields["expected_repair_date"].widget.attrs["min"] = today


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


def current_time():
    return make_aware(datetime.now()).strftime("%d.%m.%Y %H:%M")


class OrderEditForm(forms.Form):

    worker = forms.CharField(max_length=255, required=False, label="Работник")

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
        queryset=Materials.objects.all().order_by("name"),
        required=False,
        empty_label=None,
        label="Материалы",
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


class AssignRepairman(forms.Form):
    qs_st_fio = Repairmen.assignable_workers.all().order_by("fio")
    fio = forms.ModelChoiceField(
        qs_st_fio,
        label="Исполнитель",
        empty_label="ФИО не выбрано",
        widget=forms.Select(attrs={"class": "fio_select"}),
    )


class UploadPDFFile(forms.ModelForm):
    class Meta:
        model = Orders
        fields = ("material_request_file",)

    def clean_material_request_file(self):
        filename = self.cleaned_data["material_request_file"]
        p = Path(filename.name).suffix
        if p.lower() != ".pdf":
            raise ValidationError("Допускается загружать только pdf-файлы.")
        return filename

class ConvertExcelForm(forms.Form):
    # file = forms.CharField(widget=forms.ClearableFileInput())
    file = forms.FileField()

