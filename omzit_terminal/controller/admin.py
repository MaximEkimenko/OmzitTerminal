
from django.contrib import admin
from .models import DefectAct

class DefectsAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        "id",
        "act_number",
        "workshop",
        "operation",
        "quantity",
        "fixable",
        "media_ref",
        "media_count"
    )
    list_editable = ["workshop", "quantity", "fixable"]
    search_fields = ("act_number",)
    ordering = ["id"]


admin.site.register(DefectAct, DefectsAdmin)
