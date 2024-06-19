from django.contrib import admin
from .models import Orders, Equipment, OrderStatus, Shops, Repairmen, Materials


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
    list_display = ("id", "name", "inv_number", "shop")
    search_fields = ["name", "inv_number"]
    list_editable = ["name", "shop"]
    ordering = ["id"]


class OrderStatusAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ["id", "name"]
    search_fields = ["name"]
    list_editable = ["name"]
    ordering = ["id"]


class ShopsAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ["id", "name"]
    search_fields = ["name"]
    list_editable = ["name"]
    ordering = ["id"]


class RepairmenAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ["id", "fio", "position", "phone", "telegram_id", "active", "assignable"]
    search_fields = ["fio", "phone", "telegram_id"]
    list_editable = ["fio", "telegram_id", "active", "assignable"]
    ordering = ["id"]


class MaterialsAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = [
        "id",
        "name",
    ]
    search_fields = ["name"]
    list_editable = ["name"]
    ordering = ["id"]


admin.site.register(Orders, OrdersAdmin)
admin.site.register(OrderStatus, OrderStatusAdmin)
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(Shops, ShopsAdmin)
admin.site.register(Repairmen, RepairmenAdmin)
admin.site.register(Materials, MaterialsAdmin)
