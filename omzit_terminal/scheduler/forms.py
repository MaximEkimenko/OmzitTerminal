import datetime

from django import forms
from django.contrib.admin import widgets
from django.utils.timezone import make_aware

# from tehnolog.models import ProductModel
from .models import ShiftTask, WorkshopSchedule, Doers, model_pattern, model_error_text, order_pattern, order_error_text
from django.forms import ModelChoiceField
from django.db.models import Q
from tehnolog.models import ProductCategory
from constructor.forms import QueryAnswerForm, MultipleFileField, MultipleFileInput


class SchedulerWorkshop(forms.Form):
    """
    Форма для ввода графика цеха
    """

    query_set = WorkshopSchedule.objects.filter(td_status='утверждено', order_status='не запланировано')

    model_order_query = QueryAnswerForm(query_set, empty_label='выберите заказ-модель', label='Заказ-модель')

    workshop = forms.ChoiceField(choices=((1, 'Цех 1'), (2, 'Цех 2'), (3, 'Цех 3'), (4, 'Цех 4')),
                                 label='Цех', required=True)
    query_set = ProductCategory.objects.all()
    category = forms.ModelChoiceField(queryset=query_set, empty_label='Категория не выбрана',
                                      label='Категория заказа', required=True)  # выбор категории
    datetime_done = forms.DateField(label='Планируемая дата готовности', required=True,
                                    widget=forms.SelectDateWidget(empty_label=("год", "месяц", "день"),
                                                                  years=(datetime.datetime.now().year,
                                                                         datetime.datetime.now().year + 1)))


class QueryDraw(forms.Form):
    """
    Форма запроса чертежа
    """
    # model_query = forms.CharField(max_length=50, label='Модель запроса КД', required=False)
    model_query = forms.CharField(max_length=50, label='Модель запроса КД',
                                  widget=forms.TextInput(attrs={'pattern': model_pattern, 'title': model_error_text}))
    order_query = forms.CharField(max_length=50, label='Заказ запроса КД',
                                  widget=forms.TextInput(attrs={'pattern': order_pattern, 'title': order_error_text}))
    query_prior = forms.ChoiceField(choices=((1, 1), (2, 2), (3, 3), (4, 4)), label='Приоритет', initial=1,
                                    required=False)


class SchedulerWorkplaceLabel(ModelChoiceField):  # переопределение метода отображения строки результатов для РЦ
    """
    Класс для переопределения вывода ModelChoiceField для номера РЦ
    """

    def label_from_instance(self, obj):
        return obj.ws_number


class SchedulerWorkplaceLabelDate(ModelChoiceField):  # переопределение метода отображения строки результатов для даты
    """
    Класс для переопределения вывода ModelChoiceField для datetime_done
    """

    def label_from_instance(self, obj):
        return obj.model_order_query


class SchedulerWorkplace(forms.Form):
    """
    Форма для ввода графика РЦ
    """
    query_set_wp = ShiftTask.objects.exclude(ws_number="").distinct('ws_number')
    ws_number = SchedulerWorkplaceLabel(queryset=query_set_wp, empty_label='Терминал не выбран', label='Терминал')
    model_order_query_set = WorkshopSchedule.objects.filter(Q(order_status='запланировано') |
                                                            Q(order_status='в работе'))
    model_order_query = SchedulerWorkplaceLabelDate(queryset=model_order_query_set,
                                                    empty_label='Не выбрано',
                                                    label='Заказ-модель')


class FiosLabel(ModelChoiceField):  # переопределение метода отображения строки результатов для ФИО
    """
    Класс для переопределения вывода ModelChoiceField
    """

    def label_from_instance(self, obj):
        return (f"{obj.id}. Заказ - {obj.order}. №T-{obj.ws_number}. Изделие - {obj.model_name}. "
                f"Статус - {obj.st_status}")


class FioDoer(forms.Form):
    """
    Форма для ввода ФИО
    """

    # Создание поля в классе формы с отфильтрованными данными по РЦ и дате
    def __init__(self, *args, **kwargs):
        if 'ws_number' in kwargs and kwargs['ws_number'] is not None:
            ws_number = kwargs.pop('ws_number')
            model_order_query = kwargs.pop('model_order_query')
            # query_set запроса СЗ
            qs_st_number = (ShiftTask.objects.filter  # выбор "не распределено", "брак", "не принято"
                            (Q(fio_doer='не распределено') | Q(st_status='брак') | Q(st_status='не принято'))
                            ).filter(ws_number=ws_number, model_order_query=model_order_query, next_shift_task=None)
        else:
            qs_st_number = None
        # Вызов супер класса для создания поля st_number
        super(FioDoer, self).__init__(*args, **kwargs)
        try:
            self.fields['st_number'].queryset = qs_st_number
        except NameError:
            pass

    empty_qs = None  # запрос заглушка для создания переменной st_number в нужном виде
    st_number = FiosLabel(empty_qs, label='Сменное задание', empty_label='СЗ не выбрано')
    qs_st_fio = Doers.objects.all()
    fio_1 = forms.ModelChoiceField(qs_st_fio, label='ФИО исполнителя 1', empty_label='ФИО не выбрано')
    fio_2 = forms.ModelChoiceField(qs_st_fio, label='ФИО исполнителя 2', empty_label='ФИО не выбрано', initial='',
                                   required=False)
    fio_3 = forms.ModelChoiceField(qs_st_fio, label='ФИО исполнителя 3', empty_label='ФИО не выбрано', initial='',
                                   required=False)
    fio_4 = forms.ModelChoiceField(qs_st_fio, label='ФИО исполнителя 4', empty_label='ФИО не выбрано', initial='',
                                   required=False)


class PlanBid(forms.Form):
    """
    Форма для ввода графика РЦ
    """

    sz_order_query = forms.CharField(max_length=50, label='Имя заказа для служебной',
                                     widget=forms.TextInput(
                                         attrs={'pattern': order_pattern, 'title': order_error_text}))

    sz_model_query = forms.CharField(max_length=50, label='Наименование изделия служебной',
                                     widget=forms.TextInput(
                                         attrs={'pattern': model_pattern, 'title': model_error_text}))

    sz_workshop = forms.ChoiceField(choices=((0, 'Без сборки'), (1, 'Цех 1'), (2, 'Цех 2'), (3, 'Цех 3'), (4, 'Цех 4')),
                                    label='Цех сборщик', required=False)
    query_set_category = ProductCategory.objects.all()
    sz_category = forms.ModelChoiceField(queryset=query_set_category, empty_label='Категория не выбрана',
                                         label='Категория заказа', required=True)  # выбор категории
    sz_datetime_done = forms.DateField(label='Планируемая дата готовности', required=True,
                                       widget=forms.SelectDateWidget(empty_label=("год", "месяц", "день"),
                                                                     years=(datetime.datetime.now().year,
                                                                            datetime.datetime.now().year + 1)))
    sz_order_model_query = forms.CharField(max_length=50,
                                           widget=forms.TextInput(attrs={'hidden': "true"}))


class DailyReportForm(forms.Form):
    """
    Форма для заполнения ежедневного отчёта
    """

    day_plan = forms.DecimalField(min_value=0, max_digits=10, decimal_places=1, label='План день', required=False)
    day_fact = forms.DecimalField(min_value=0, max_digits=10, decimal_places=1, label='Факт день')

    personal_total = forms.IntegerField(min_value=0, label='Всего персонала', initial=0)
    personal_shift = forms.IntegerField(min_value=0, label='Выход в дату персонала', initial=0)
    personal_total_welders = forms.IntegerField(min_value=0, label='Всего сварщиков', initial=0)
    personal_shift_welders = forms.IntegerField(min_value=0, label='Выход в дату сварщиков', initial=0)
    personal_night_welders = forms.IntegerField(min_value=0, label='Всего сварщиков', initial=0)

    personal_total_locksmiths = forms.IntegerField(min_value=0, label='Всего слесарей', initial=0)
    personal_shift_locksmiths = forms.IntegerField(min_value=0, label='Выход в дату слесарей', initial=0)
    personal_night_locksmiths = forms.IntegerField(min_value=0, label='Всего слесарей', initial=0)

    personal_total_painters = forms.IntegerField(min_value=0, label='Всего сварщиков', initial=0)
    personal_shift_painters = forms.IntegerField(min_value=0, label='Выход в дату сварщиков', initial=0)
    personal_night_painters = forms.IntegerField(min_value=0, label='Всего сварщиков', initial=0)

    personal_total_turners = forms.IntegerField(min_value=0, label='Всего слесарей', initial=0)
    personal_shift_turners = forms.IntegerField(min_value=0, label='Выход в дату слесарей', initial=0)
    personal_night_turners = forms.IntegerField(min_value=0, label='Выход в дату слесарей', initial=0)


class ReportForm(forms.Form):
    """
    Форма ответа на заявку КД
    """
    date_start = forms.DateField(
        widget=widgets.AdminDateWidget(attrs={"class": "vDateField report_input"}),
        label='c',
        # initial=datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    )
    date_end = forms.DateField(
        widget=widgets.AdminDateWidget(attrs={"class": "vDateField report_input"}),
        label='по',
        # initial=datetime.datetime.now()
    )

    class Media:
        css = {
            'all': (
                '/static/scheduler/css/widgets.css',
            )
        }
        js = [
            '/admin/jsi18n/',
            '/static/admin/js/core.js',
        ]


class CdwChoiceForm(forms.Form):
    """
    Форма ответа на заявку КД
    """
    cdw_files = MultipleFileField(label='Чертежи cdw',
                                  widget=MultipleFileInput(attrs={'accept': ".cdw"}))


class SendSZForm(forms.Form):
    """
    Форма ответа на заявку КД
    """
    sz_number = forms.CharField(max_length=50, label='Номер заявки',
                                widget=forms.TextInput(attrs={"class": "report_input"}))
    product_name = forms.CharField(max_length=50, label='Изделие',
                                   widget=forms.TextInput(attrs={"class": "report_input"}))
    sz_text = forms.CharField(label='Текст заявки',
                              widget=forms.Textarea(attrs={"class": "sz_textarea"}))
    need_date = forms.DateField(
        widget=widgets.AdminDateWidget(attrs={"class": "vDateField report_input"}),
        label='Дата потребности',
    )

    class Media:
        css = {
            'all': (
                '/static/scheduler/css/widgets.css',
            )
        }
        js = [
            '/admin/jsi18n/',
            '/static/admin/js/core.js',
        ]


class PlanResortHiddenForm(forms.Form):
    day_plan_sum = forms.CharField(widget=forms.HiddenInput(attrs={"id": "id_hidden_input", 'form': "fil_days_form"}),
                                   required=True)
