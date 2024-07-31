from datetime import timedelta
from django import forms
from controller.models import DefectAct
from constructor.forms import MultipleFileField
class EditDefectForm(forms.ModelForm):
    manual_fixing_time = forms.FloatField(
        widget=forms.NumberInput(attrs={'placeholder': "Время в часах, например 1.5"}),
        label="Время исправления", required=False
    )
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
        self.fields["operation"].widget = forms.Textarea(attrs={"cols": 33, "rows": 5})
        self.fields["processing_object"].widget = forms.Textarea(attrs={"cols": 33, "rows": 5})
        self.fields["control_object"].widget = forms.Textarea(attrs={"cols": 33, "rows": 5})
        self.fields["remark"].widget = forms.Textarea(attrs={"cols": 33, "rows": 5})
        self.fields["inconsistencies"].widget = forms.Textarea(attrs={"cols": 33, "rows": 5})
        self.fields["remark"].widget = forms.Textarea(attrs={"cols": 33, "rows": 5})
        self.fields["tech_solution"].widget = forms.Textarea(attrs={"cols": 33, "rows": 5})

        # отключаем поле, если время исправнения было импортировано из ShiftTask, руками его редактировать не надо
        if self.instance.fixing_time:
            float_hours = round(self.instance.fixing_time/timedelta(hours=1), 4)
            self.initial.update({"manual_fixing_time": float_hours})

        if self.instance.shift_task and self.instance.fixing_time:
            self.fields["manual_fixing_time"].widget.attrs = {"disabled": "disabled"}

    def is_valid(self):
        x = super().is_valid()
        return x


class FilesUploadForm(forms.Form):
    files = MultipleFileField()
