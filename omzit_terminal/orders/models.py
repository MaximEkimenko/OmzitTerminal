from datetime import date, datetime

from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models import OuterRef, Subquery, QuerySet
from django.urls import reverse_lazy
from django.utils.timezone import now, make_aware
from orders.utils.common import OrdStatus


class Assignable(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(assignable=True)


class Repairmen(models.Model):
    fio = models.CharField(max_length=255, null=False, blank=False, verbose_name="ФИО")
    position = models.CharField(max_length=255, null=True, verbose_name="Должность")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    telegram_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="telegram_id")
    active = models.BooleanField(default=True, verbose_name="Работает")
    assignable = models.BooleanField(default=True, verbose_name="можно назначить на ремонт")

    objects = models.Manager()
    assignable_workers = Assignable()

    def __str__(self):
        return self.fio

    class Meta:
        verbose_name = "Ремонтник"
        verbose_name_plural = "Ремонтники"


class Shops(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Местонахождение")
    # для сортировки по востребованности
    qty = models.IntegerField(default=0, verbose_name="Количество приписанного оборудования")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy("shops_edit", kwargs={"pk": self.pk})

    class Meta:
        verbose_name = "Цех"
        verbose_name_plural = "Цеха"
        ordering = ["name"]


class FlashMessage(models.Model):
    """
    Таблица, содержащая всплывающие сообщения.
    Сделана для того, чтобы можно было передавать сообщения между эндпоинтами.
    После того, как сообщения отобразятся, они должны быть удалены из таблицы.
    """

    name = models.CharField(
        max_length=255, null=True, blank=False, verbose_name="Всплывающее сообщение"
    )

    class Meta:
        verbose_name = "Категория оборудования"
        verbose_name_plural = "Категории оборудования"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Equipment(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название оборудования")
    vendor = models.CharField(max_length=255, blank=True, null=True, verbose_name="Производитель")
    model = models.CharField(max_length=255, blank=True, null=True, verbose_name="Модель")
    inv_number = models.CharField(
        max_length=255, blank=False, null=True, verbose_name="Инвентарный номер"
    )
    serial_number = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Серийный номер"
    )

    # поле для определения оборудования внутри заявок на ремонт
    # состоит из названия оборудования и последних 4 цифр инветарника
    # на самом деле оно не уникальное, инвентарники могут повторяться, просто поможет отличить одно от другого
    unique_name = models.CharField(max_length=255, verbose_name="Уникальное название оборудования")

    shop = models.ForeignKey(
        Shops, on_delete=models.PROTECT, null=True, verbose_name="Местонахождение"
    )

    registration_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата добавления в базу"
    )

    characteristics = models.TextField(blank=True, null=True, verbose_name="ТТХ")
    description = models.TextField(blank=True, null=True, verbose_name="Описание оборудования")
    ppr_plan_day = models.IntegerField(
        blank=True, null=True, db_index=True, verbose_name="День планового ремонта"
    )
    in_operation = models.BooleanField(default=True, verbose_name="Находится эксплуатации")
    make_ppr_order = models.BooleanField(default=True, verbose_name="Формировать заявки ППР каждый месяц")

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
        ordering = ["unique_name"]

    def get_absolute_url(self):
        return reverse_lazy("equipment_card", kwargs={"equipment_id": self.pk})

    @classmethod
    def equipment_with_PPR(cls) -> QuerySet["Equipment"]:
        equipment = cls.objects.exclude(ppr_plan_day__isnull=True).order_by('ppr_plan_day', 'name').all()
        return equipment

    def __str__(self):
        return self.unique_name


class OrderStatus(models.Model):
    name = models.CharField(max_length=50, verbose_name="Статус")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Состояние ремонта"
        verbose_name_plural = "Состояния ремонта"
        ordering = ["pk"]


class Materials(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Требуемые материалы")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Материалы"
        verbose_name_plural = "Материалы"


class PriorityChoices(models.IntegerChoices):
    RP_1 = 1, "1"
    RP_2 = 2, "2"
    RP_3 = 3, "3"
    RP_4 = 4, "4"

class WorkersLog(models.Model):
    order = models.ForeignKey("Orders", on_delete=models.CASCADE, related_name="workers_log")
    dayworkers_string = models.CharField(max_length=256, verbose_name="Ремонтники")
    start_date = models.DateTimeField(db_index=True)
    end_date = models.DateTimeField(db_index=True)


def order_directory_path(instance, filename):
    """Формирует путь для сохранения файлов, прикрепленных к заявкам"""
    return f"order_{instance.pk}/{filename}"


class Orders(models.Model):
    is_ppr = models.BooleanField(default=False, verbose_name="Заявка на ППР", db_index=True)

    equipment = models.ForeignKey(
        Equipment, on_delete=models.PROTECT, verbose_name="Оборудование", related_name="repairs"
    )

    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.CASCADE,
        default=OrdStatus.DETECTED,
        verbose_name="Статус заявки",
        related_name="orders_with_status",
    )
    previous_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Предыдущий статус",
        related_name="orders_with_previous_status",
    )
    priority = models.IntegerField(
        choices=PriorityChoices.choices, default=PriorityChoices.RP_4, verbose_name="Приоритет"
    )
    breakdown_date = models.DateTimeField(verbose_name="Дата поломки")
    breakdown_description = models.TextField(verbose_name="Описание поломки")
    worker = models.CharField(max_length=100, blank=True, null=True, verbose_name="Работник")

    # dayworkers = models.ManyToManyField(Repairmen, through=OrdersWorkers, related_name="orders")
    dayworkers_string = models.CharField(max_length=256, blank=True, null=True, verbose_name="Ремонтники")
    identified_employee = models.CharField(
        max_length=100, null=True, verbose_name="Работник, создавший заявку"
    )
    inspection_date = models.DateTimeField(null=True, verbose_name="Дата начала ремонта")
    expected_repair_date = models.DateTimeField(
        null=True, verbose_name="Ожидаемая дата окончания ремонта"
    )
    inspected_employee = models.CharField(
        max_length=100, null=True, verbose_name="Работник, запустивший ремонт"
    )
    clarify_date = models.DateTimeField(null=True, verbose_name="Дата уточнения данных по ремонту")

    repair_date = models.DateTimeField(null=True, verbose_name="Дата окончания ремонта")
    repaired_employee = models.CharField(
        max_length=100, null=True, verbose_name="Работник, завершивший ремонт"
    )

    acceptance_date = models.DateTimeField(
        null=True, verbose_name="Дата закрытия заявки", db_index=True
    )
    accepted_employee = models.CharField(
        max_length=100, null=True, verbose_name="Работник, принявший оборудование"
    )
    revision_date = models.DateTimeField(null=True, verbose_name="Дата возврата на доработку")
    revision_cause = models.TextField(null=True, verbose_name="Причина возврата на доработку")
    revised_employee = models.CharField(
        max_length=100, null=True, verbose_name="Работник, отклонивший ремонт"
    )

    cancel_cause = models.TextField(null=True, verbose_name="Причина отмены ремонта")

    materials = models.ForeignKey(
        Materials,
        on_delete=models.PROTECT,
        default=1,
        verbose_name="Требуемые материалы",
    )
    materials_request = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="№ заявки на материалы"
    )
    materials_request_date = models.DateTimeField(
        null=True, verbose_name="Дата создания заявки на материалы"
    )
    material_dispatcher = models.CharField(
        max_length=100, null=True, verbose_name="Работник, подтверждающий наличие материалов"
    )
    material_request_file = models.FileField(
        verbose_name="Pdf заявка на материалы", null=True, upload_to=order_directory_path
    )

    confirm_materials_date = models.DateTimeField(
        null=True, verbose_name="Дата подтверждения материалов"
    )
    supply_request = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="№ заявки снабжения"
    )
    supply_request_date = models.DateTimeField(
        null=True, verbose_name="Дата создания заявки снабжения"
    )

    breakdown_cause = models.TextField(null=True, verbose_name="Причина поломки")
    solution = models.TextField(null=True, verbose_name="Способ устранения")

    class Meta:
        verbose_name = "Заявка на ремонт"
        verbose_name_plural = "Заявки на ремонт"
        ordering = ["pk"]

    def get_absolute_url(self):
        return reverse_lazy("orders_edit", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.pk} {self.equipment} {self.status} {self.breakdown_date}"

    
    def active_workers_count(self) -> int:
        """
        Возвращает количество работников, приписанных к заявке в данный момент
        """
        if self.dayworkers_string:
            count = len(self.dayworkers_string.split(", "))
        else:
            count = 0
        return count


    @classmethod
    def fresh_orders(cls):
        """
        Список свежих заявок - либо находящихся в работе, либо законченных сегодня.
        """
        today_tz = make_aware(datetime.combine(date.today(), datetime.min.time()))
        fresh = (
            cls.objects.exclude(acceptance_date__lt=today_tz)
            .all()
            .prefetch_related("equipment", "status", "materials")
        )


        return fresh

    @classmethod
    def archived_orders(cls):
        """Список завершенных заявок"""
        not_active_order_status = [OrdStatus.ACCEPTED, OrdStatus.CANCELLED, OrdStatus.UNREPAIRABLE]
        fresh = (
            cls.objects.filter(status__in=not_active_order_status)
            .all()
            .prefetch_related("equipment", "status")
        )
        return fresh

    @classmethod
    def busy_workers(cls, repairmen_ids: list[int]) -> QuerySet["Repairmen"]:
        """
        Возвращает список объектов работников, которых выбрал пользователь, но они уже заняты на другой заявке.
        Чтобы не добавлять их повторно к другому заданию.
        """
        # Находим все заявки у которых непустые поля "исполнители"
        orders_with_workers = cls.fresh_orders().exclude(dayworkers_string__isnull=True).values('dayworkers_string')
        all_names_str = set()
        # разрезаем фамилии из заявок, на которых заняты рабочие
        # и получаем список фамилий, которые уже заняты на других заявках
        for order in orders_with_workers:
            all_names_str.update(order['dayworkers_string'].split(", "))
        repaimnen_intesesction = (Repairmen.objects
                                .filter(fio__in=all_names_str, pk__in=repairmen_ids)
                                .all())

        return repaimnen_intesesction



