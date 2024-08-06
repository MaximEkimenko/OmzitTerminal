from datetime import timedelta
from django import forms
from controller.models import DefectAct
from constructor.forms import MultipleFileField

class EditDefectForm(forms.ModelForm):
    """
    Форма для заполнения акта о браке.
    """
    #  В модели есть поле fixing time, но оно имеет тип временного интервала, а нам нужно чтобы пользователь
    #  вводил данные в виде числа - количества часов, ушедших на ремонт. Потм это число преобразуется
    #  во временной интервал.
    manual_fixing_time = forms.FloatField(
        widget=forms.NumberInput(attrs={'placeholder': "Время в часах, например 1.5"}),
        label="Время исправления", required=False
    )
    field_order = [
        "datetime_fail", "workshop", "operation", "processing_object", "control_object",
        "quantity", "inconsistencies", "remark", "tech_service", "tech_solution",
        "cause", "fixable", "fio_failer", "master_finish_wp", "manual_fixing_time",
    ]

    textarea_fields = ["operation", "processing_object", "control_object", "remark", "inconsistencies", "tech_solution"]

    class Meta:
        model = DefectAct
        fields = [
            "datetime_fail", "workshop", "operation", "processing_object",
            "control_object", "quantity", "inconsistencies", "remark", "tech_service",
            "tech_solution", "fixable", "fio_failer", "master_finish_wp", "cause"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["datetime_fail"].widget = forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
        for field in self.textarea_fields:
            self.fields[field].widget = forms.Textarea()

        # отключаем поле, если время исправнения было импортировано из ShiftTask, руками его редактировать не надо
        if self.instance.fixing_time:
            float_hours = round(self.instance.fixing_time/timedelta(hours=1), 4)
            self.initial.update({"manual_fixing_time": float_hours})
        if self.instance.shift_task and self.instance.fixing_time:
            self.fields["manual_fixing_time"].widget.attrs = {"disabled": "disabled"}

    def is_valid(self):
        """
        На случай редактирования записи: datetime_fail обязательное, но при редактировании оно
        для некоторых пользователей может быть отключено. А отключенные поля не попадают в измененные
        данные, соответственно форма не проходит валидацию.
        Я проверяю, что поле изначально было заполнено, и в этом случае помечаю поле как необязательное.
        Тогда валидация формы проходит.
        """
        if self.initial.get("datetime_fail"):
            self.fields["datetime_fail"].required = False
        return super().is_valid()


class FilesUploadForm(forms.Form):
    """
    Форма выбора файлов для загрузки в акт о браке.
    """
    files = MultipleFileField()
