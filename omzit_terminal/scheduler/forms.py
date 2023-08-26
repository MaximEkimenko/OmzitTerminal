from django import forms
from tehnolog.models import ProductModel
from .models import ShiftTask


class SchedulerWorkshop(forms.Form):
    order = forms.CharField(max_length=50, label='Номер заказа')
    query_set = ProductModel.objects.all()
    model_name = forms.ModelChoiceField(queryset=query_set, empty_label='Модель не выбрана',
                                        label='Модель заказа')
    workshop = forms.ChoiceField(choices=((1, 'Цех 1'), (2, 'Цех 2'), (3, 'Цех 3'), (4, 'Цех 4')), label='Цех')
    datetime_done = forms.DateField(label='Планируемая дата готовности')


class SchedulerWorkplace(forms.Form):
    query_set = ShiftTask.objects.all().distinct('ws_number')
    workplace = forms.ModelChoiceField(queryset=query_set, empty_label='РЦ не выбран', label='Рабочий центр')

# .objects.filter(stuff).values("ip_address").annotate(n=models.Count("pk"))
