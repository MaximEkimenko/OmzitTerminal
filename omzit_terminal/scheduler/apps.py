from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduler'
    verbose_name = 'Рабочее место диспетчера'

    def ready(self):
        import scheduler.signals  # noqa
