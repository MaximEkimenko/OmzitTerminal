from datetime import timedelta

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormMixin
from django.contrib import messages

from controller.forms import EditDefectForm
from controller.models import DefectAct
from controller.utils.edit_permissions import FIELD_EDIT_PERMISSIONS
from orders.utils.roles import get_employee_position, PERMITTED_USERS, menu_items
from m_logger_settings import logger


class RoleMixin(ContextMixin):
    """
    Добавляет в представления, основанные на классах, переменные, нужные в шаблонах для
    отрисовки списка страничек в главном меню. Для разных ролей список страниц будет разный.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "role": get_employee_position(self.request.user.username),
            "permitted_users": PERMITTED_USERS,
            "menu_items": menu_items
        })
        return context


class DisableFieldsMixin(FormMixin):
    """
    Миксин, выполняющий две задачи:
    1) отключает отдельные поля формы в зависимости от роли пользователя.
    2) Переводит число во временной интервал при сохранении в базу срока исправления брака.
    А так же содержит необходимые переменные для создания и редактирования актов о браке
    """

    model = DefectAct
    form_class = EditDefectForm
    template_name = "controller/create_defect.html"
    login_url = "/scheduler/login/"
    success_url = reverse_lazy("controller:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']
        for permission in FIELD_EDIT_PERMISSIONS:
            if context["role"] not in FIELD_EDIT_PERMISSIONS[permission]:
                form.fields[permission].disabled = True
        return context


    def form_valid(self, form):
        # нужно преобразовать время в часах(float), поступивший из формы, и в интервал времени и в таком виде сохранять
        if fix_time := form.cleaned_data["manual_fixing_time"]:
            form.instance.fixing_time = timedelta(hours=1) * fix_time
        try:
            act = form.instance.act_number
            form.save()
        except Exception as e:
            operation = "изменении" if form.initial else "создании"
            alert_message = f"Ошибка при при {operation} акта о браке № {act}"
            messages.add_message(self.request, messages.ERROR, alert_message)
            logger.error(alert_message)
            logger.exception(e)
        else:
            operation = "Изменен" if form.initial else "Сохранен"
            alert_message = f"{operation} акт о браке № {act}"
            messages.add_message(self.request, messages.SUCCESS, alert_message)
            logger.info(alert_message)
        return redirect(self.success_url)
