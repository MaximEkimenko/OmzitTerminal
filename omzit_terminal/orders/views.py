from datetime import datetime
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import StringAgg
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from django.db import transaction
from django.db.models import Window, Count, ProtectedError, Subquery, OuterRef, F
from django.db.models.functions import RowNumber
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView, ListView, DeleteView
from django.forms.models import model_to_dict
from django.core.handlers.wsgi import WSGIRequest
from django.utils import timezone
from django.utils.timezone import make_aware


from m_logger_settings import logger
from scheduler.filters import get_filterset
from orders.report import create_order_report


from orders.models import Orders, Equipment, Shops, Repairmen, OrdersWorkers
from orders.forms import (
    AddEquipmentForm,
    AddOrderForm,
    AssignWorkersForm,
    EditEquipmentForm,
    RepairProgressForm,
    ConfirmMaterialsForm,
    RepairFinishForm,
    RepairRevisionForm,
    OrderEditForm,
    RepairCancelForm,
    AddShop,
    AssignRepairman,
    UploadPDFFile,
)
from orders.utils.common import (
    OrdStatus,
    MAX_DAYWORKERS_PER_ORDER,
    can_edit_workers,
    MATERIALS_NOT_REQUIRED,
)
from orders.utils.roles import Position, get_employee_position, custom_login_check, PERMITED_USERS
from orders.utils.utils import (
    create_flash_message,
    pop_flash_messages,
    get_doers_list,
    orders_record_to_dict,
    get_order_verbose_names,
    get_order_edit_context,
    process_repair_expect_date,
    apply_order_status,
    create_extra_materials,
    check_order_suspend,
    orders_get_context,
    clear_dayworkers,
    check_order_resume,
    ORDER_CARD_COLUMNS,
    remove_old_file_if_exist,
    create_ppr_orders,
)
from orders.utils.telegram import order_telegram_notification


@login_required(login_url="/scheduler/login/")
def equipment(request: WSGIRequest) -> HttpResponse:
    custom_login_check(request)
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

    # столбцы, которые будут выводиться в таблице оборудования
    cols = ["id", "name", "inv_number", "shop__name", "ppr_plan_day"]
    table_data = (
        Equipment.objects.annotate(
            row_number=Window(expression=RowNumber(), order_by="unique_name")
        )
        .annotate(history=Count("repairs"))
        .values("row_number", "history", *cols)
    )

    context = {
        "table_data": table_data,
        "alerts": pop_flash_messages(),
        "add_equipment_form": AddEquipmentForm(),
        "button_conditions": {"create": [Position.Admin, Position.Engineer, Position.HoRT]},
        "role": get_employee_position(request.user.username),
    }
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
                    "breakdown_date": make_aware(datetime.now()),
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

    create_ppr_orders()
    context = orders_get_context(request)

    return render(request, "orders/orders.html", context=context)


class OrdersArchive(LoginRequiredMixin, ListView):
    """
    Отображает все заявки на ремонт, которые были завершены (приняты или отменены).
    """

    template_name = "orders/orders_archive.html"

    def get_queryset(self):
        return Orders.archived_orders()


@login_required(login_url="/scheduler/login/")
def order_assign_workers(request, pk):
    """
    Добавляем работников к ремонту:
    Или в начале ремонта.
    Или после того, как на предыдущем ремонте работники были удалены
    Или в начала рабочего для, чтобы вновь запустить приостановленную заявку.
    Вызывается при статусах заявки: "требует ремонта" и "приостановлено"
    """
    context = {}
    order: Orders = Orders.objects.prefetch_related("equipment", "equipment__shop", "status").get(
        pk=pk
    )
    if request.method == "POST":
        form = AssignWorkersForm(request.POST)
        if form.is_valid():
            fios = get_doers_list(form)
            if len(fios) == len(set(fios)):  # если нет повторений в списке fios, добавляем запись
                fios_ids = [i.id for i in fios]
                # проверяем, есть ли среди указанных работников те, кто уже назначен на другую заявку
                busy_workers = Repairmen.busy_workers(fios_ids)
                # если есть, оставляем форму без изменения и отправляем сообщение об ошибке
                if busy_workers:
                    for worker in busy_workers:
                        create_flash_message(f"{worker.fio} занят на заявке № {worker.order}")
                    form = AssignWorkersForm(form.cleaned_data)
                    context.update({"object": order, "form": form, "alerts": pop_flash_messages()})
                    return render(request, "orders/repair_start.html", context)

                # добавляем работников к ремонту
                # order.dayworkers.add(*fios)
                for new_worker in fios:
                    OrdersWorkers.objects.create(order=order, worker=new_worker)
                # если мы попали сюда (добавляем работников), значит ремонт либо начат, либо возобновлен
                # если ремонт был приостановлен, возобновляем предыдущую стадию
                if order.previous_status_id in (OrdStatus.START_REPAIR, OrdStatus.REPAIRING):
                    applied_status = order.previous_status_id
                    alert_message = (
                        f"Возобновлен ремонт оборудования {order.equipment} по заявке № {order.id}."
                    )
                # или начинаем новый ремонт
                else:
                    order.inspection_date = make_aware(datetime.now())
                    order.inspected_employee = " ".join(
                        [request.user.last_name, request.user.first_name]
                    )
                    applied_status = OrdStatus.START_REPAIR
                    alert_message = (
                        f"Начат ремонт оборудования {order.equipment} по заявке № {order.id}."
                    )
                success = apply_order_status(order, applied_status)
                if success:
                    create_flash_message(alert_message)
                    logger.info(alert_message)
                    order_telegram_notification(applied_status, order)

                return redirect("orders")
            else:
                alert_message = f"Исполнители дублируются. Измените исполнителей."
                create_flash_message(alert_message)
                logger.error(alert_message)
                form = AssignWorkersForm(form.cleaned_data)
                context.update({"object": order, "form": form, "alerts": pop_flash_messages()})
                return render(request, "orders/repair_start.html", context)

    form = AssignWorkersForm()
    context.update(
        {"object": order, "form": form, "permitted_users": PERMITED_USERS, "status": OrdStatus}
    )
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
            # Строка, на основе которой будет создан новый объект Materials
            # она имеет приоритетное значение. Если она заполнена, материалы из списка перестают учитываться
            exma = form.cleaned_data["extra_materials"]
            # По умолчанию создается первая секунда дня. Но когда люди указывают дату производства,
            # они вряд ли думают, что все будет сделано в первую секунду указанного дня
            # поэтому пускай будет последняя секунда дня
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
                if m.name == MATERIALS_NOT_REQUIRED:
                    applied_status = OrdStatus.REPAIRING
                else:
                    applied_status = OrdStatus.WAIT_FOR_MATERIALS
                order.clarify_date = make_aware(datetime.now())
                apply_order_status(order, applied_status)
                # clear_dayworkers(order)
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
    """
    Здесь совершаются два действия.
    1) Если материалы в наличии или не требуются, происходит переход на этап "в ремонте". И
     онт тут же приостанавливается, так как работники на этапе подтверждения материалов были сняты.
    2) Если материалы нужно ждать, вводится номер заявки на материалы. Статус заявки на ремонт не меняется.
    """

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
                # Нужно сохранить номер заявки и дату, больше ничего не меняется
                # так что вызывает функцию с тем же статусом
                apply_order_status(order, OrdStatus.WAIT_FOR_MATERIALS)
                alert_message = "Номер заявки на материалы внесен."
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
            check_order_suspend(order)
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
                clear_dayworkers(order)
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
        clear_dayworkers(order)
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
                # так как при окончании ремонта все сотрудники снимаются, при возврате на доработку
                # нужно возвращать статус "приостановлено"
                applied_status = OrdStatus.REPAIRING
                apply_order_status(order, applied_status)
                check_order_suspend(order)
            except Exception as e:
                alert_message = (
                    f"Ошибка записи при возвращении оборудования {order.equipment} "
                    f"по заявке {order.id} на доработку"
                )
                create_flash_message(alert_message)
                logger.error(alert_message)
                logger.exception(e)
            else:
                alert_message = (
                    f"Оборудование {order.equipment} по заявке {order.id} возвращено на доработку"
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
                clear_dayworkers(order)
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
def order_card(request, pk):
    """
    Выводит информацию о заявке (показывет все поля из модели, которые можно показать).
    """
    # подзапрос, который сливает исполнителей из mny-to-many-отношения в одну строку
    assigned_workers_subquery = (
        Repairmen.assignable_workers.filter(
            orders=OuterRef("pk"), assignments__end_date__isnull=True
        )
        .values("orders")
        .annotate(assigned_workers_string=StringAgg("fio", delimiter=", ", ordering="fio"))
        .values("assigned_workers_string")
    )

    # подзапрос, считающий сколько всего людей было назначено на ремонт, включая повторные назначения
    assignments_count = (
        OrdersWorkers.objects.filter(order=OuterRef("pk"))
        .values("order")
        # тут можно посчитать все эпизоды назначения либо уникальных сотрудников, которых назначили
        .annotate(assignments=Count("worker", distinct=False))
        .values("assignments")
    )

    order = (
        Orders.objects.filter(pk=pk)
        .annotate(dayworkers_fio=Subquery(assigned_workers_subquery))
        .annotate(workers_count=Subquery(assignments_count))
        .first()
    )

    # получаем подписи к полям таблицы
    verbose_header = get_order_verbose_names()

    # получаем подписи к полям таблицы
    verbose_header.update(
        {"dayworkers_fio": "Исполнители", "workers_count": "Назначений на ремонт"}
    )
    # из записи в базе данных получаем словарь с нужными нам колонками
    vd = orders_record_to_dict(order, ORDER_CARD_COLUMNS)
    vhd = {verbose_header[i]: vd[i] for i in ORDER_CARD_COLUMNS}
    print(vd)
    can_edit = can_edit_workers(order.status_id, get_employee_position(request.user.username))
    context = {
        "object": order,
        "order_params": vhd,
        "status": OrdStatus,
        "can_edit_workers": can_edit,
        "permitted_users": PERMITED_USERS,
        "equipment": order.equipment,
        "special_fields": {
            "pdf_field": verbose_header["material_request_file"],
            "assignments_field": verbose_header["workers_count"],
            "equipment": verbose_header["equipment"],
        },
        "alerts": pop_flash_messages(),
    }
    return render(request, "orders/repair_card.html", context)


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
def order_history(request: WSGIRequest, pk):
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
    success_url = reverse_lazy("login")
    model = Equipment
    template_name = "orders/equipment_card.html"
    pk_url_kwarg = "equipment_id"
    extra_context = {
        "edit_and_delete": [Position.Admin, Position.Engineer, Position.HoRT],
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


# class EquipmentCardEditView(LoginRequiredMixin, UpdateView):
class EquipmentCardEditView(UpdateView):
    success_url = reverse_lazy("login")
    model = Equipment
    form_class = EditEquipmentForm
    template_name = "orders/equipment_edit.html"
    pk_url_kwarg = "equipment_id"

    extra_context = {
        "color": "red",
        "edit_and_delete": [Position.Admin, Position.Engineer, Position.HoRT],
        "permitted_users": PERMITED_USERS,
    }

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "edit_and_delete": [Position.Admin, Position.Engineer, Position.HoRT],
                "equipment_id": self.kwargs.get("equipment_id"),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        print("hello")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form_data = form.cleaned_data
        temp = form.instance
        temp.unique_name = f"{form_data['name']} ({form_data['inv_number'][-4:]})"
        # это ради того, чтобы удалить у оборудования день планового ремонта
        # из формы приходить пустая строка, а в базу нужно записывать None
        if form_data["ppr_plan_day"] == "":
            temp.ppr_plan_day = None
        temp.save()
        return HttpResponseRedirect(self.get_success_url())


def order_report(request):
    try:
        exel_file = create_order_report()
        logger.info(f"Пользователь {request.user} успешно загрузил отчёт в excel.")
        return FileResponse(open(exel_file, "rb"))
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


class RepairmenEdit(ListView):
    """
    Педставление для редактирования (добавления и удаления) работников, приписанных к заявке на ремонт
    """

    # model = Repairmen
    template_name = "orders/repairmen_edit.html"

    def get_queryset(self):
        qs = (
            Orders.objects.get(pk=self.kwargs["pk"])
            .dayworkers.filter(assignments__end_date__isnull=True)
            .order_by("fio")
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "alerts": pop_flash_messages(),
                "add_form": AssignRepairman(),
                "order_id": self.kwargs["pk"],
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        """
        Добавляет работника к заявке
        """
        rw = reverse_lazy("repairmen_edit", args=(self.kwargs["pk"],))
        form = AssignRepairman(request.POST)
        if form.is_valid():
            order = Orders.objects.get(pk=self.kwargs["pk"])
            new_worker = form.cleaned_data["fio"]
            busy_worker = Repairmen.busy_workers([new_worker.pk]).first()
            print("занятый сторудник:", busy_worker)
            if busy_worker:
                create_flash_message(f"{busy_worker.fio} занят на заявке № {busy_worker.order}")
                return redirect(rw)
            # на заявку можно назначить только MAX_DAYWORKERS_PER_ORDER работников
            if order.active_workers_count() >= MAX_DAYWORKERS_PER_ORDER:
                create_flash_message("Назначено слишком много работников.")
            else:
                OrdersWorkers.objects.create(order=order, worker=new_worker)
                check_order_resume(order)
                create_flash_message("Работник добавлен к заявке.")

        else:
            create_flash_message(form.errors["name"][0])

        return redirect(rw)


@login_required(login_url="/scheduler/login/")
def repairmen_delete_proc(request: WSGIRequest):
    if request.method == "POST":
        pk = request.POST.get("commit-delete-button")
        order_id = request.POST.get("order_id")
        try:
            order = Orders.objects.get(pk=order_id)
            OrdersWorkers.objects.filter(order=order_id, worker=pk).all().update(
                end_date=timezone.now()
            )
            check_order_suspend(order)

        except Exception as e:
            alert_message = f"Ошибка при удалении работника из заявки"
            create_flash_message(alert_message)
            message = (
                f"Ошибка при удалении работника id {pk} "
                f"из заявки №  {order_id}. Пользователь {request.user.username}"
            )
            logger.error(message)
            logger.exception(e)
        else:
            alert_message = f"Работник снят с заявки."
            create_flash_message(alert_message)
            message = f"Работник id {pk} снят с заявки № {order_id}. Удалил пользователь {request.user.username}"
            logger.info(message)

    rw = reverse_lazy("repairmen_edit", args=(order_id,))
    return redirect(rw)


class RepairmenHistory(LoginRequiredMixin, ListView):
    template_name = "orders/repairmen_history.html"

    def get_queryset(self):
        dayworkers = (
            OrdersWorkers.objects.filter(order=self.kwargs["pk"])
            .order_by("start_date")
            .annotate(fio=F("worker__fio"))
            .all()
        )
        return dayworkers

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"pk": self.kwargs["pk"]})
        return context


@login_required(login_url="/scheduler/login/")
def clear_workers_proc(request: WSGIRequest, pk):
    order = Orders.objects.get(pk=pk)
    clear_dayworkers(order)
    return redirect("orders")


@login_required(login_url="/scheduler/login/")
def order_upload_pdf(request: WSGIRequest, pk):
    """
    Представление для прикрепления pdf-файлов к заявке на ремонт
    """
    order: Orders = Orders.objects.get(pk=pk)
    if request.method == "POST":
        form = UploadPDFFile(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES.get("material_request_file")
            remove_old_file_if_exist(order.material_request_file)
            order.material_request_file.save(file.name, file)
            return redirect(reverse_lazy("order_info", args=(pk,)))
        else:
            # для вывода ошибок формы
            context = {"form": form}
            return render(request, "orders/upload_pdf.html", context=context)
    else:
        context = {"form": UploadPDFFile(), "pk": pk}
        return render(request, "orders/upload_pdf.html", context=context)


def show_pdf(request, pk):
    order: Orders = Orders.objects.get(pk=pk)
    f = Path(order.material_request_file.path)
    if f.exists():
        pdf_file = order.material_request_file.open()
        return FileResponse(pdf_file)
    else:
        order.material_request_file = None
        order.save()
        create_flash_message("Файл не обнаружен")
        return redirect(reverse_lazy("order_info", args=(pk,)))


def filter_data(request):
    equipment_json = list(Equipment.objects.all().values("id", "unique_name", "shop_id"))
    return JsonResponse({"filter": equipment_json})
