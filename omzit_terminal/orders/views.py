from datetime import datetime
import asyncio

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.db.models import Window, Count, ProtectedError
from django.db.models.functions import RowNumber
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView, ListView, DeleteView
from django.forms.models import model_to_dict
from django.core.handlers.wsgi import WSGIRequest
from django.utils.timezone import make_aware


from m_logger_settings import logger
from scheduler.filters import get_filterset
from orders.report import create_order_report


from orders.models import Orders, Equipment, Shops
from orders.forms import (
    AddEquipmentForm,
    AddOrderForm,
    StartRepairForm,
    EditEquipmentForm,
    RepairProgressForm,
    ConfirmMaterialsForm,
    RepairFinishForm,
    RepairRevisionForm,
    OrderEditForm,
    RepairCancelForm,
    AddShop,
)
from orders.utils.common import (
    OrdStatus,
)
from orders.utils.roles import Position, get_employee_position, custom_login_check, PERMITED_USERS
from orders.utils.utils import (
    create_flash_message,
    pop_flash_messages,
    get_doers_list,
    convert_name,
    orders_get_context,
    orders_record_to_dict,
    get_order_verbose_names,
    get_order_edit_context,
    process_repair_expect_date,
    apply_order_status,
    create_extra_materials,
)
from orders.utils.telegram import order_telegram_notification


@login_required(login_url="/scheduler/login/")
def equipment(request: WSGIRequest) -> HttpResponse:
    custom_login_check(request)
    context = {}
    if request.method == "POST":
        new_equipment_name = AddEquipmentForm(request.POST)
        if new_equipment_name.is_valid():
            try:
                eq_params = new_equipment_name.cleaned_data
                eq_params.update(
                    {"unique_name": f"{eq_params['name']} ({eq_params['inv_number'][-4:]})"}
                )
                x = Equipment(**eq_params)
                x.save()
                alert_message = "Новое оборудование добавлено!"
                create_flash_message(alert_message)
                eq_name = new_equipment_name.cleaned_data["name"]
                logger.info(f'Новое оборудование "{eq_name}" добавлено в таблицу Equipment')
                # TODO отправка сообщения в телеграм
            except Exception as e:
                alert_message = "Ошибка добавления оборудования"
                create_flash_message(alert_message)
                logger.error("Ошибка записи в таблицу Equipment.")
                logger.exception(e)
        return redirect("equipment")

    # cols = ["id", "name", "inv_number", "category__name"]
    cols = ["id", "name", "inv_number", "shop__name"]
    table_data = (
        Equipment.objects.annotate(
            row_number=Window(expression=RowNumber(), order_by="unique_name")
        )
        .annotate(history=Count("repairs"))
        .values("row_number", "history", *cols)
    )

    query_fields = ["id", "name", "inv_number", "shop__name"]
    equipment_filter = get_filterset(request.GET, queryset=table_data, fields=query_fields)
    context["equipment_filter"] = equipment_filter
    context["table"] = table_data
    context["alerts"] = pop_flash_messages()
    context["add_equipment_form"] = AddEquipmentForm()
    context.update(
        {
            "button_conditions": {
                "create": [Position.Admin, Position.Engineer, Position.HoRT],
            },
            "role": get_employee_position(request.user.username),
            "permitted_users": PERMITED_USERS,
        }
    )
    return render(request, "orders/equipment.html", context=context)


@login_required(login_url="/scheduler/login/")
def orders(request) -> HttpResponse:
    """
    Главная страница, на которой демонстрируется таблица с заявками на ремонт.
    На этой странице проходит управление всем циклом заявок: от создания заявки до завершения ремонта.
    """
    custom_login_check(request)
    if request.method == "POST":
        add_order_form = AddOrderForm(request.POST)
        if add_order_form.is_valid():
            order_parameters = {key: val for key, val in add_order_form.cleaned_data.items()}
            # поле shops нужно только для фильтрации названий, поэтому удаляем, иначе будет ошибка создания записи
            order_parameters.pop("shops")
            # добавляем сотрудника, который создал заявку
            order_parameters.update(
                {
                    "identified_employee": " ".join(
                        [request.user.last_name, request.user.first_name]
                    ),
                }
            )
            try:
                new_order = Orders(**order_parameters)  # создаем заявку
                new_order.save()
            except Exception as e:
                alert_message = "Ошибка добавления в заявки"
                create_flash_message(alert_message)
                logger.error("Ошибка записи в таблицу Orders.")
                logger.exception(e)
            else:
                alert_message = "Новая заявка на ремонт добавлена!"
                create_flash_message(alert_message)
                logger.info(f"Заявка № {new_order.id} добавлена в таблицу Orders")
                order_telegram_notification(OrdStatus.DETECTED, new_order)
        else:
            print("ошибка валидации при добавлении заявки")
        return redirect("orders")
    context = orders_get_context(request)
    return render(request, "orders/orders.html", context=context)


@login_required(login_url="/scheduler/login/")
def order_start_repair(request, pk):
    context = {}
    order: Orders = Orders.objects.prefetch_related("equipment", "equipment__shop", "status").get(
        pk=pk
    )
    if request.method == "POST":
        form = StartRepairForm(request.POST)
        if form.is_valid():
            fios = get_doers_list(form)
            if len(fios) == len(set(fios)):  # если нет повторений в списке fios, добавляем запись
                applied_status = OrdStatus.START_REPAIR
                order.doers_fio = ", ".join(sorted(fios))
                order.inspection_date = make_aware(datetime.now())
                order.inspected_employee = " ".join(
                    [request.user.last_name, request.user.first_name]
                )
                apply_order_status(order, applied_status)
                alert_message = (
                    f"Начат ремонт оборудования {order.equipment} по заявке № {order.id}."
                )
                create_flash_message(alert_message)
                logger.info(alert_message)
                order_telegram_notification(applied_status, order)

                return redirect("orders")
            else:
                alert_message = f"Исполнители дублируются. Измените исполнителей."
                create_flash_message(alert_message)
                logger.error(alert_message)
                form = StartRepairForm(form.cleaned_data)
                context.update({"object": order, "form": form, "alerts": pop_flash_messages()})
                return render(request, "orders/repair_start.html", context)

    form = StartRepairForm()
    context.update({"object": order, "form": form, "permitted_users": PERMITED_USERS})
    return render(request, "orders/repair_start.html", context)


@login_required(login_url="/scheduler/login/")
def order_clarify_repair(request, pk):
    order: Orders = Orders.objects.prefetch_related("equipment", "equipment__shop", "status").get(
        pk=pk
    )
    if request.method == "POST":
        form = RepairProgressForm(request.POST)
        if form.is_valid():
            material_correct = False
            matl = form.cleaned_data["materials"]  # объект Materials
            # строка на основе которой будет создан новый объект Materials
            # она имеет приоритетное значение. Если она заполнена, материалы из списка перестают учитываться
            exma = form.cleaned_data["extra_materials"]
            # по умолчанию сооздается первая секунда дня. Но когда люди указывают дату производства,
            # они вряд ли думают, что все будет сделано в первую секунду указанного дня
            # поэтому пускай будет последняя секунда дня
            # et = datetime.combine(form.cleaned_data["expected_repair_date"], datetime.max.time())
            # order.expected_repair_date = make_aware(et)

            order.expected_repair_date = process_repair_expect_date(
                form.cleaned_data["expected_repair_date"]
            )
            if exma:
                m = create_extra_materials(exma)
                material_correct = m is not None
            else:
                if matl:
                    m = matl
                    material_correct = True
            if material_correct:
                order.materials = m
                applied_status = OrdStatus.WAIT_FOR_MATERIALS
                order.clarify_date = make_aware(datetime.now())
                apply_order_status(order, applied_status)
                alert_message = "Данные по ремонту уточнены"
                create_flash_message(alert_message)
                order_telegram_notification(applied_status, order)
            else:
                alert_message = f"Некорректно указаны материалы"
                create_flash_message(alert_message)
                logger.error(alert_message)
            return redirect("orders")

    form = RepairProgressForm(model_to_dict(order))
    context = {"object": order, "form": form, "permitted_users": PERMITED_USERS}
    return render(request, "orders/repair_clarify.html", context)


@login_required(login_url="/scheduler/login/")
def order_confirm_materials(request, pk):
    order: Orders = Orders.objects.prefetch_related("equipment", "equipment__shop", "status").get(
        pk=pk
    )
    if request.method == "POST":
        # добавлена заявка на оборудование
        if "materials_request" in request.POST:
            # отрпавлена форма с номером заявки на материалы
            # состояние ремонта не меняем
            form = ConfirmMaterialsForm(request.POST)
            if form.is_valid():
                order.materials_request = form.cleaned_data["materials_request"]
                order.materials_request_date = make_aware(datetime.now())
                apply_order_status(order, OrdStatus.WAIT_FOR_MATERIALS)
                alert_message = "Наличие материалов для ремонта подтверждено."
                create_flash_message(alert_message)

        else:
            # нажата кнопка "материалы в наличии"
            # состояние заявки меняем на "в ремонте"
            order.confirm_materials_date = make_aware(datetime.now())
            order.material_dispatcher = " ".join([request.user.last_name, request.user.first_name])
            applied_status = OrdStatus.REPAIRING
            apply_order_status(order, applied_status)
            alert_message = f"Наличие материалов для ремонта по заявке {order.id} подтверждено."
            create_flash_message(alert_message)
            logger.info(alert_message)
            order_telegram_notification(applied_status, order)
        return redirect("orders")
    form = ConfirmMaterialsForm({"materials_request": order.materials_request})
    context = {"object": order, "form": form, "permitted_users": PERMITED_USERS}
    return render(request, "orders/repair_confirm_materials.html", context)


@login_required(login_url="/scheduler/login/")
def order_finish_repair(request, pk):
    order: Orders = Orders.objects.prefetch_related("equipment", "equipment__shop", "status").get(
        pk=pk
    )
    if request.method == "POST":
        form = RepairFinishForm(request.POST)
        if form.is_valid():
            try:
                order.breakdown_cause = form.cleaned_data["breakdown_cause"]
                order.solution = form.cleaned_data["solution"]
                order.repair_date = make_aware(datetime.now())
                order.repaired_employee = " ".join(
                    [request.user.last_name, request.user.first_name]
                )
                applied_status = OrdStatus.FIXED
                apply_order_status(order, applied_status)
            except Exception as e:
                alert_message = f"Ошибка записи при завершении ремонта оборудования {order.equipment} по заявке {order.id}"
                create_flash_message(alert_message)
                logger.error(alert_message)
                logger.exception(e)
            else:
                alert_message = (
                    f"Ремонт оборудования {order.equipment} по заявке {order.id} закончен"
                )
                create_flash_message(alert_message)
                logger.info(alert_message)
                order_telegram_notification(applied_status, order)

        return redirect("orders")

    form = RepairFinishForm(model_to_dict(order))
    context = {"object": order, "form": form, "permitted_users": PERMITED_USERS}

    return render(request, "orders/repair_finish.html", context)


@login_required(login_url="/scheduler/login/")
def order_accept_repair(request, pk):
    if request.method == "POST":
        order: Orders = Orders.objects.prefetch_related(
            "equipment", "equipment__shop", "status"
        ).get(pk=pk)
        order.acceptance_date = make_aware(datetime.now())
        order.accepted_employee = " ".join([request.user.last_name, request.user.first_name])
        applied_status = OrdStatus.ACCEPTED
        apply_order_status(order, applied_status)
        alert_message = "Отремонтированное оборудование принято"
        create_flash_message(alert_message)
        order_telegram_notification(applied_status, order)
        return redirect("orders")

    order_object = Orders.objects.get(pk=pk)
    context = {"object": order_object, "permitted_users": PERMITED_USERS}
    return render(request, "orders/repair_accept.html", context)


@login_required(login_url="/scheduler/login/")
def order_revision(request, pk):
    order: Orders = Orders.objects.prefetch_related("equipment", "equipment__shop", "status").get(
        pk=pk
    )
    if request.method == "POST":
        form = RepairRevisionForm(request.POST)
        if form.is_valid():
            try:
                d = make_aware(datetime.now())
                date_string = d.strftime(format="%d.%m.%Y %H:%M")
                order.revision_date = d
                string = f"[{date_string}] {form.cleaned_data['revision_cause']}"
                if order.revision_cause:
                    order.revision_cause = f"{order.revision_cause}<br>{string}"
                else:
                    order.revision_cause = string
                order.revised_employee = " ".join([request.user.last_name, request.user.first_name])
                applied_status = OrdStatus.REPAIRING
                apply_order_status(order, applied_status)
            except Exception as e:
                alert_message = f"Ошибка записи при возвращении оборудования {order.equipment} по заявке {order.id} на доработку"
                create_flash_message(alert_message)
                logger.error(alert_message)
                logger.exception(e)
            else:
                alert_message = (
                    f"Оборудовани {order.equipment} по заявке {order.id} возвращено на доработку"
                )
                create_flash_message(alert_message)
                logger.info(alert_message)
                order_telegram_notification(
                    applied_status,
                    order,
                    "Оборудование '{equipment}' ({shop}) по заявке № {id} возвращено на доработку.",
                )
        return redirect("orders")

    form = RepairRevisionForm()
    context = {"object": order, "form": form, "permitted_users": PERMITED_USERS}
    return render(request, "orders/repair_revision.html", context)


@login_required(login_url="/scheduler/login/")
def order_cancel_repair(request, pk):
    order: Orders = Orders.objects.prefetch_related("equipment", "equipment__shop", "status").get(
        pk=pk
    )
    if request.method == "POST":
        form = RepairCancelForm(request.POST)
        if form.is_valid():
            try:
                order.cancel_cause = form.cleaned_data["cancel_cause"]
                # так или иначе ремонт завершен, поэтому использую поля для принятия оборудования в работу
                order.acceptance_date = make_aware(datetime.now())
                order.accepted_employee = " ".join(
                    [request.user.last_name, request.user.first_name]
                )
                applied_status = OrdStatus.CANCELLED
                apply_order_status(order, applied_status)

            except Exception as e:
                alert_message = f"Ошибка записи при отмене ремонта оборудования {order.equipment} по заявке {order.id}"
                create_flash_message(alert_message)
                logger.error(alert_message)
                logger.exception(e)
            else:
                alert_message = (
                    f"Ремонт оборудования {order.equipment} по заявке {order.id} отменен"
                )
                create_flash_message(alert_message)
                logger.info(alert_message)
                order_telegram_notification(applied_status, order)
        return redirect("orders")

    form = RepairCancelForm()
    context = {"object": order, "form": form, "permitted_users": PERMITED_USERS}
    return render(request, "orders/repair_cancel.html", context)


@login_required(login_url="/scheduler/login/")
def order_info(request, pk):
    order: Orders = Orders.objects.prefetch_related("equipment", "equipment__shop", "status").get(
        pk=pk
    )
    verbose_header = get_order_verbose_names()
    vd = orders_record_to_dict(order, list(verbose_header))
    vhd = {verbose_header[i]: vd[i] for i in verbose_header}
    context = {
        "object": order,
        "order_params": vhd,
        "status": OrdStatus,
        "permitted_users": PERMITED_USERS,
    }
    return render(request, "orders/repair_info.html", context)


@login_required(login_url="/scheduler/login/")
def order_edit(request, pk):
    order: Orders = Orders.objects.prefetch_related("equipment", "equipment__shop", "status").get(
        pk=pk
    )
    if request.method == "POST":
        form = OrderEditForm(request.POST)
        if form.is_valid():
            cd = {}
            for i in form.cleaned_data:
                if form.cleaned_data[i]:
                    cd[i] = form.cleaned_data[i]
            # обрабатываем ожидаемую дату если она введена
            if erd := cd.get("expected_repair_date"):
                cd["expected_repair_date"] = process_repair_expect_date(erd)
            # обрабатываем требуемые материалы, если они введены вручную, а не выбраны из списка
            # их нужно вставить в модель материалов, а уже потом вставить в заявку
            if cd.get("extra_materials"):
                extra_materials: str = cd.pop("extra_materials").strip()
                em = create_extra_materials(extra_materials)
                if em:
                    cd["materials"] = em
            try:
                Orders.objects.filter(pk=pk).update(**cd)
            except Exception as e:
                alert_message = f"Ошибка редактирования заявки № {order.id}"
                create_flash_message(alert_message)
                message = f"Ошибка при редактировании заявки № {order.id} пользователем {request.user.username}\n"
                message += f"Попытка внести данные: {cd}"
                logger.info(message)
                logger.exception(e)
            else:
                alert_message = f"Заявка № {order.id} успешно отредактирована"
                create_flash_message(alert_message)
                message = (
                    f"Заявка № {order.id} отредактирована пользователем {request.user.username}\n"
                )
                message += f"Были внесены данные: {cd}"
                logger.info(message)

        return redirect("orders")

    form = OrderEditForm(model_to_dict(order))
    context = {
        "object": order,
        "form": form,
    }
    conditions = get_order_edit_context(request)
    for key, field in form.fields.items():
        if (
            order.status_id not in conditions["stages"][key]
            or conditions["role"] not in conditions["employees"][key]
        ):
            x = dict(field.widget.attrs)
            x["disabled"] = "disabled"
            field.widget.attrs = x
    context.update({"permitted_users": PERMITED_USERS})
    return render(request, "orders/repair_edit.html", context)


@login_required(login_url="/scheduler/login/")
def order_delete_proc(request: WSGIRequest):
    if request.method == "POST":
        pk = request.POST.get("delete_button")
        try:
            pk = int(pk)
        except Exception:
            logger.info("Не получилось переконвертить индекс оборудования")
        else:
            order: Orders = Orders.objects.prefetch_related(
                "equipment", "equipment__shop", "status"
            ).get(pk=pk)
            # убеждаемся, что пользователю можно удалить заявку
            if (
                get_employee_position(request.user.username) in [Position.Admin, Position.HoS]
                and order.status_id == OrdStatus.DETECTED
            ):
                try:
                    Orders.objects.filter(pk=pk).delete()
                    alert_message = f"Заявка на ремонт удалена"
                    create_flash_message(alert_message)
                    message = f"Удалена заявка id {pk}.Удалил пользователь {request.user.username}"
                    logger.info(message)
                except Exception as e:
                    alert_message = f"Ошибка при удалении заявки"
                    create_flash_message(alert_message)
                    message = (
                        f"Ошибка при удалении заявки id {pk} "
                        f"пользователем {request.user.username}"
                    )
                    logger.error(message)
                    logger.exception(e)
            else:
                alert_message = f"Нельзя удалить заявку"
                create_flash_message(alert_message)
                message = (
                    f"Попытка удалить заявку id {pk} при некорректном статусе {order.status} "
                    f"пользователем {request.user.username}"
                )
                logger.error(message)

    return redirect("orders")


@login_required(login_url="/scheduler/login/")
def repair_history(request: WSGIRequest, pk):
    equipment: Equipment = Equipment.objects.filter(pk=pk).values(*["id", "name", "unique_name"])[0]
    orders: Orders = Orders.objects.filter(equipment_id=pk).order_by("breakdown_date").all()
    context = {
        "orders": orders,
        "object": equipment,
        "status": OrdStatus,
        "permitted_users": PERMITED_USERS,
    }
    return render(request, "orders/repair_history.html", context)


class EquipmentCardView(LoginRequiredMixin, DetailView):
    login_url = success_url = reverse_lazy("login")
    model = Equipment
    template_name = "orders/equipment_card.html"
    pk_url_kwarg = "equipment_id"
    extra_context = {
        "edit_and_delete": [Position.Admin, Position.Engineer, Position.HoRT],
        "permitted_users": PERMITED_USERS,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"role": get_employee_position(self.request.user.username)})

        return context

    def post(self, request, *args, **kwargs):
        """
        Обрабатывает удаление оборудования
        """
        pk = request.POST.get("delete_pk")
        if pk:
            try:
                Equipment.objects.filter(pk=pk).delete()
                alert_message = f"Оборудование удалено"
                create_flash_message(alert_message)
                message = (
                    f"Удалено оборудование id {pk}.Удалил пользователь {request.user.username}"
                )
                logger.info(message)

            except ProtectedError as e:
                alert_message = (
                    f"Оборудование не может быть удалено, так как к нему привязаны заявки ремонтов"
                )
                create_flash_message(alert_message)
                message = (
                    f" К оборудованию id {pk} привязаны ремонты, поэтому оно не может быть "
                    f"удалено пользователем {request.user.username}"
                )
                logger.error(message)
                logger.exception(e)

            except Exception as e:
                alert_message = f"Ошибка при удалении оборудования"
                create_flash_message(alert_message)
                message = (
                    f"Ошибка при удалении оборудования id {pk} "
                    f"пользователем {request.user.username}"
                )
                logger.error(message)
                logger.exception(e)

        else:
            alert_message = f"Не найден идентификатор оборудования"
            create_flash_message(alert_message)
            message = f"Для удаления поступил пустой идентификатор оборудования {pk}.  Пользователь {request.user.username}"
            logger.error(message)
        return redirect("equipment")


class EquipmentCardEditView(LoginRequiredMixin, UpdateView):
    login_url = success_url = reverse_lazy("login")
    model = Equipment
    form_class = EditEquipmentForm
    template_name = "orders/equipment_edit.html"
    pk_url_kwarg = "equipment_id"
    success_url = reverse_lazy("equipment")

    extra_context = {
        "color": "red",
        "edit_and_delete": [Position.Admin, Position.Engineer, Position.HoRT],
        "permitted_users": PERMITED_USERS,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                # "permitted_users": PERMITED_USERS,
                # "status": OrdStatus,
                "edit_and_delete": [Position.Admin, Position.Engineer, Position.HoRT],
                "test": Position.Admin,
            }
        )
        return context

    def form_valid(self, form):
        form_data = form.cleaned_data
        temp = form.instance
        temp.unique_name = f"{form_data['name']} ({form_data['inv_number'][-4:]})"
        temp.save()
        return HttpResponseRedirect(self.get_success_url())


def repair_orders_reports(request):
    try:
        exel_file = create_order_report()
        logger.info(f"Пользователь {request.user} успешно загрузил отчёт в excel.")
        return FileResponse(open(exel_file, "rb"))
        return redirect("orders")
    except Exception as e:
        logger.info("Ошибка при создании xls-отчета")
        logger.exception(e)
    return redirect("orders")


class ShopsView(ListView):
    model = Shops
    template_name = "orders/shops.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "alerts": pop_flash_messages(),
                "add_form": AddShop(),
                "edit_form": AddShop(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        """
        Обрабатывает удаление оборудования
        """
        form = AddShop(request.POST)
        if form.is_valid():
            form.save()
            create_flash_message("Местонахождение создано.")
        else:
            create_flash_message(form.errors["name"][0])

        return redirect("shops")


class ShopsEdit(UpdateView):
    model = Shops

    form_class = AddShop
    template_name = "orders/shops_edit.html"
    success_url = reverse_lazy("shops")

    extra_context = {}


class ShopsDelete(DeleteView):
    model = Shops
    template_name = "orders/shops_delete.html"
    # success_url = reverse_lazy("orders:shops")
    success_url = reverse_lazy("shops")

    def post(self, request, *args, **kwargs):
        try:
            object: Shops = self.get_object()
            name = object.name
            pk = object.id
            self.get_object().delete()
            alert_message = f'Местонаходжение "{name}" удлено'
            create_flash_message(alert_message)
            message = f"{alert_message}. Удалил пользователь {request.user.username}"
            logger.info(message)
        except ProtectedError as e:

            alert_message = (
                f"Местоположение не может быть удалено, так как нему привязано оборудование"
            )
            create_flash_message(alert_message)
            message = (
                f" К местоположению id {pk} привязано оборудование, поэтому оно не может быть "
                f"удалено пользователем {request.user.username}"
            )
            logger.error(message)
            logger.exception(e)

        return redirect(self.success_url)


@login_required(login_url="/scheduler/login/")
def shop_edit_proc(request: WSGIRequest):
    """
    Техническая функция для изменения названия местоположения оборудования.
    Принимает строку с измененным местоположением, пытается применить это изменение и делает
    редирект на ту же самую страницу, с которой была вызвана

    """
    if request.method == "POST":
        form = AddShop(request.POST)

        pk = request.POST.get("edit-form-button")
        try:
            pk = int(pk)
        except Exception:
            logger.info("Не получилось переконвертить индекс местоположения")
        else:
            if form.is_valid():
                shop = Shops.objects.get(pk=pk)
                shop_name = shop.name
                del shop
                try:
                    Shops.objects.filter(pk=pk).update(**form.cleaned_data)
                    alert_message = (
                        f"местонахождение {shop_name} было изменено на {form.cleaned_data['name']}"
                    )
                    create_flash_message(alert_message)
                    logger.info(
                        f"id {pk} местонахождение {shop_name} было изменено на {form.cleaned_data['name']}. Пользователь {request.user.username}"
                    )
                except Exception as e:
                    alert_message = f"Ошибка при изменении местоположения {shop_name}"
                    create_flash_message(alert_message)
                    logger.error(
                        f"Ошибка при изменении местоположения id {pk}  {shop_name}  на {form.cleaned_data['name']}. "
                        f"Пользователь {request.user.username}"
                    )
                    logger.exception(e)

    return redirect("shops")


@login_required(login_url="/scheduler/login/")
def shop_delete_proc(request: WSGIRequest):
    if request.method == "POST":
        pk = request.POST.get("commit-delete-button")
        try:
            pk = int(pk)
        except Exception:
            logger.info("Не получилось переконвертить индекс оборудования")
        else:
            try:
                Shops.objects.filter(pk=pk).delete()
                alert_message = f"Местоположение удалено"
                create_flash_message(alert_message)
                message = (
                    f"Удалено местпоположение id {pk}.Удалил пользователь {request.user.username}"
                )
                logger.info(message)
            except ProtectedError as e:
                alert_message = (
                    f"Местоположение не может быть удалено, так как нему привязано оборудование"
                )
                create_flash_message(alert_message)
                message = (
                    f" К местоположению id {pk} привязано оборудование, поэтому оно не может быть "
                    f"удалено пользователем {request.user.username}"
                )
                logger.error(message)
                logger.exception(e)

            except Exception as e:
                alert_message = f"Ошибка при удалении местоположения"
                create_flash_message(alert_message)
                message = (
                    f"Ошибка при удалении местоположения id {pk} "
                    f"пользователем {request.user.username}"
                )
                logger.error(message)
                logger.exception(e)

    return redirect("shops")
