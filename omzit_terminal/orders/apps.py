from django.apps import AppConfig


class TestrepConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"
    verbose_name = 'Заявки на ремонт'
