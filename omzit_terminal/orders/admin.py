from django.contrib import admin
from .models import Orders, Equipment, OrderStatus


# Register your models here.
class OrdersAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        "id",
        "equipment",
        "status",
        "breakdown_date",
        "breakdown_description",
        "priority",
    )
    search_fields = ("equipment", "breakdown_description")
    ordering = ["id"]


class EquipmentAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ("id", "name", "inv_number")
    search_fields = ["name", "inv_number"]
    list_editable = ["name", "inv_number"]
    ordering = ["id"]


class OrderStatusAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ["id", "name"]
    search_fields = ["name"]
    list_editable = ["name"]
    ordering = ["id"]


admin.site.register(Orders, OrdersAdmin)
admin.site.register(OrderStatus, OrderStatusAdmin)
admin.site.register(Equipment, EquipmentAdmin)
