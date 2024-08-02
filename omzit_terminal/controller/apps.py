from pathlib import Path
from django.apps import AppConfig


class ControllerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "controller"
    # папка, гле создаются все подпапки для файлов, прикрепленных к актам о браке
    DEFECTS_BASE_PATH = Path(r"D:\upload")
