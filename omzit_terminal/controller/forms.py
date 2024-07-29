from django import forms
from controller.models import DefectAct

class EditDefectForm(forms.ModelForm):
    class Meta:
        model = DefectAct
        fields = [
            "datetime_fail", "act_number", "workshop", "operation", "processing_object",
            "control_object","quantity", "inconsistencies", "remark", "fixable"
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["datetime_fail"].widget = forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
        self.fields["operation"].widget = forms.Textarea(attrs=({"cols": 30, "rows": 4}))
        self.fields["processing_object"].widget = forms.Textarea(attrs=({"cols": 30, "rows": 4}))
        self.fields["control_object"].widget = forms.Textarea(attrs=({"cols": 30, "rows": 4}))
        self.fields["remark"].widget = forms.Textarea(attrs=({"cols": 30, "rows": 4}))
        self.fields["inconsistencies"].widget = forms.Textarea(attrs=({"cols": 30, "rows": 4}))
        self.fields["remark"].widget = forms.Textarea(attrs=({"cols": 30, "rows": 4}))
