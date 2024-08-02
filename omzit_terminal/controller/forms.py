from datetime import timedelta
from django import forms
from controller.models import DefectAct
from constructor.forms import MultipleFileField
from controller.utils.edit_permissions import FIELD_EDIT_PERMISSIONS
class EditDefectForm(forms.ModelForm):
    manual_fixing_time = forms.FloatField(
        widget=forms.NumberInput(attrs={'placeholder': "Время в часах, например 1.5"}),
        label="Время исправления", required=False
    )
    field_order = [
        "datetime_fail", "workshop", "operation", "processing_object", "control_object",
        "quantity", "inconsistencies", "remark", "tech_service", "tech_solution",
        "cause", "fixable", "fio_failer", "master_finish_wp", "manual_fixing_time",
    ]

    textarea_attrs = {"cols": 33, "rows": 5}
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
            self.fields[field].widget = forms.Textarea(attrs=self.textarea_attrs)

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
        x = super().is_valid()
        return x


class FilesUploadForm(forms.Form):
    files = MultipleFileField()
