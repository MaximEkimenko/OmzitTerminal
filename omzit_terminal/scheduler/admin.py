from django.contrib import admin

from .models import ShiftTask, WorkshopSchedule, Doers


class SchedulerShiftTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'model_name', 'datetime_done', 'order',
                    'op_number', 'op_name_full', 'ws_number', 'fio_doer', 'st_status')
    search_fields = ('id', 'model_name', 'datetime_done', 'order',
                     'op_number', 'op_name_full', 'ws_number', 'fio_doer', 'st_status')
    ordering = ['id']


class SchedulerWorkshopScheduleAdmin(admin.ModelAdmin):
    list_display = ('workshop', 'model_name', 'datetime_done', 'order', 'order_status', 'done_rate', 'td_status')
    search_fields = ('workshop', 'model_name', 'datetime_done', 'order', 'order_status', 'done_rate', 'td_status')
    list_filter = ('workshop', 'model_name', 'datetime_done', 'order', 'order_status', 'done_rate', 'td_status')
    ordering = ['datetime_done']


class SchedulerDoersAdmin(admin.ModelAdmin):
    list_display = ('doers',)
    search_fields = ('doers',)
    # fields = ('doers',)


admin.site.register(WorkshopSchedule, SchedulerWorkshopScheduleAdmin)
admin.site.register(ShiftTask, SchedulerShiftTaskAdmin)
admin.site.register(Doers, SchedulerDoersAdmin)

admin.site.site_title = 'Управление терминалами ОмЗиТ'
admin.site.site_header = 'Управление терминалами ОмЗиТ'
admin.site.empty_value_display = ""
