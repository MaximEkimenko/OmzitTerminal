from django.contrib import admin

from .models import ShiftTask, WorkshopSchedule, Doers


# from .models import DailyReport, MonthPlans  # TODO ФУНКЦИОНАЛ ОЧТЁТОВ ЗАКОНСЕРВИРОВАНО

# TODO ЗАКОНСЕРВИРОВАНО Функционал простоев
# from .models import Downtime


class SchedulerShiftTaskAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('id', 'model_name', 'datetime_done', 'order',
                    'op_number', 'op_name_full', 'ws_number', 'fio_doer', 'st_status')
    search_fields = ('id', 'model_name', 'datetime_done', 'order',
                     'op_number', 'op_name_full', 'ws_number', 'fio_doer', 'st_status')
    ordering = ['id']
    list_editable = ('ws_number', 'fio_doer', 'st_status')


class SchedulerWorkshopScheduleAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('id', 'workshop', 'model_name', 'datetime_done', 'order', 'order_status', 'done_rate', 'td_status')
    search_fields = ('workshop', 'model_name', 'datetime_done', 'order', 'order_status', 'done_rate', 'td_status')
    list_filter = ('workshop', 'model_name', 'datetime_done', 'order', 'order_status', 'done_rate', 'td_status')
    ordering = ['datetime_done']
    list_editable = ('workshop', 'model_name', 'datetime_done', 'order', 'order_status', 'td_status')


class SchedulerDoersAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('id', 'doers',)
    search_fields = ('doers',)
    ordering = ['doers']
    list_editable = ('doers',)


# TODO ЗАКОНСЕРВИРОВАНО Функционал простоев
# class SchedulerDowntimeAdmin(admin.ModelAdmin):
#     save_on_top = True
#     list_display = (
#         'id',
#         'shift_task',
#         'status',
#         'reason',
#         'description',
#         'datetime_creation',
#         'datetime_start',
#         'datetime_end',
#         'master_decision_fio',
#     )


class SchedulerDailyReportAdmin(admin.ModelAdmin):
    save_on_top = True


class SchedulerMonthPlansAdmin(admin.ModelAdmin):
    save_on_top = True


admin.site.register(WorkshopSchedule, SchedulerWorkshopScheduleAdmin)
admin.site.register(ShiftTask, SchedulerShiftTaskAdmin)
admin.site.register(Doers, SchedulerDoersAdmin)
# TODO ЗАКОНСЕРВИРОВАНО Функционал простоев
# admin.site.register(Downtime, SchedulerDowntimeAdmin)
# TODO ФУНКЦИОНАЛ ОЧТЁТОВ ЗАКОНСЕРВИРОВАНО
# admin.site.register(DailyReport, SchedulerDailyReportAdmin)
# admin.site.register(MonthPlans, SchedulerMonthPlansAdmin)

admin.site.site_title = 'Управление терминалами ОмЗиТ'
admin.site.site_header = 'Управление терминалами ОмЗиТ'
admin.site.empty_value_display = ""
