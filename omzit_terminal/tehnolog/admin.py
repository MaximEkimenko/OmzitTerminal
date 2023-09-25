from django.contrib import admin
from .models import ProductCategory


# class TehnologTechDataAdmin(admin.ModelAdmin):
#     list_display = ('id', 'op_number', 'op_name', 'ws_name', 'op_name_full', 'ws_number', 'norm_tech',
#                     'datetime_create', 'datetime_update', 'product_category')
#     # list_display_links = ()
#     search_fields = ('id', 'op_number', 'op_name', 'ws_name', 'op_name_full', 'ws_number', 'norm_tech',
#                      'datetime_create', 'datetime_update', 'product_category')
#     list_filter = ('op_number', 'op_name', 'ws_name', 'op_name_full', 'ws_number', 'norm_tech',
#                    'datetime_create', 'datetime_update', 'product_category')
#
#
class TehnologProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name')
    # list_display_links = ()
    search_fields = ('id', 'category_name')
    ordering = ['id']


# admin.site.register(TechData, TehnologTechDataAdmin)
admin.site.register(ProductCategory, TehnologProductCategoryAdmin)
