from django.db.models import Model


def get_model_verbose_names(model: Model) -> dict[str, str]:
    """
    Возвращает словарь подписей к полям таблицы заявок на ремонт (Orders)
    Ключ: название поля (имя переменной, ссылающейся на поле)
    Значение: русское название поля, взятое из атрибута verbose_names поля
    """
    verbose_names = dict()
    # можно использовать такой подход
    for field in model._meta.get_fields():
        if hasattr(field, "verbose_name"):
            verbose_names[field.name] = field.verbose_name
        else:
            verbose_names[field.name] = field.name
    return verbose_names
