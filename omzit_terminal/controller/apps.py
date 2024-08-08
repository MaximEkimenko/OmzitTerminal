from pathlib import Path
from django.apps import AppConfig


class ControllerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'controller'
    verbose_name = 'Акты о браке'
    # папка, гле создаются все подпапки для файлов, прикрепленных к актам о браке
    DEFECTS_BASE_PATH = Path(r'controller_acts')
