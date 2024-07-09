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

    @classmethod
    def busy_workers(cls, repairmen_ids: list[int]) -> QuerySet["Repairmen"]:
        sq = OrdersWorkers.objects.filter(worker=OuterRef("pk"), end_date__isnull=True).values(
            "order"
        )
        busy_workers: QuerySet["Repairmen"] = (
            cls.assignable_workers.filter(pk__in=repairmen_ids)
            .annotate(order=Subquery(sq))
            .filter(
                order__isnull=False
            )  # нужно, чтобы не выдавались сотрудники, не приписанные к заданию
            .all()
        )
        return busy_workers


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
    ppr_plan_day = models.IntegerField(blank=True, null=True, verbose_name="День планового ремонта")
    in_operation = models.BooleanField(default=True, verbose_name="В эксплуатации")

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
        ordering = ["unique_name"]

    def get_absolute_url(self):
        return reverse_lazy("equipment_card", kwargs={"equipment_id": self.pk})

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


class OrdersWorkers(models.Model):
    worker = models.ForeignKey(Repairmen, on_delete=models.CASCADE, related_name="assignments")
    order = models.ForeignKey("Orders", on_delete=models.CASCADE, related_name="assignments")
    start_date = models.DateTimeField(default=now)
    end_date = models.DateTimeField(null=True)

    class Meta:
        # unique_together = ["worker", "order", "start_date"]
        pass

    def __str__(self):
        return f"worker: {self.worker.fio}   order:{self.order.id} start_date:{self.start_date}  end_date:{self.end_date} "


def order_directory_path(instance, filename):
    """Формирует путь для сохранения файлов, прикрепленных к заявкам"""
    return f"order_{instance.pk}/{filename}"


class Orders(models.Model):
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
    breakdown_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата поломки")
    breakdown_description = models.TextField(verbose_name="Описание поломки")
    worker = models.CharField(max_length=100, blank=True, null=True, verbose_name="Работник")
    dayworkers = models.ManyToManyField(Repairmen, through=OrdersWorkers, related_name="orders")
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

    acceptance_date = models.DateTimeField(null=True, verbose_name="Дата закрытия заявки")
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

    def assigned_workers(self):
        """
        Возвращает список ремонтников, занимающихся в данный момент этим заданием
        """
        return self.assignments.filter(end_date__isnull=True).all()

    def involved_workers(self):
        """
        Возвращает список ремонтников, принимавших участие в данном ремонте
        """
        return self.dayworkers.all()

    def active_workers_count(self) -> int:
        """
        Возвращает количество работников, приписанных к заявке в данный момент
        """
        return self.assignments.filter(end_date__isnull=True).count()

    @classmethod
    def fresh_orders(cls):
        assigned_workers_subquery = (
            Repairmen.assignable_workers.filter(
                orders=OuterRef("pk"), assignments__end_date__isnull=True
            )
            .values("orders")
            .annotate(assigned_workers_string=StringAgg("fio", delimiter=", ", ordering="fio"))
            .values("assigned_workers_string")
        )
        today_tz = make_aware(datetime.combine(date.today(), datetime.min.time()))
        fresh = (
            cls.objects.exclude(acceptance_date__lt=today_tz)
            .all()
            .annotate(dayworkers_fio=Subquery(assigned_workers_subquery))
            .prefetch_related("equipment", "status", "materials")
        )
        return fresh

    @classmethod
    def archived_orders(cls):
        not_active_order_status = [OrdStatus.ACCEPTED, OrdStatus.CANCELLED, OrdStatus.UNPRPAIRABLE]
        fresh = (
            cls.objects.filter(status__in=not_active_order_status)
            .all()
            .prefetch_related("equipment", "status")
        )
        return fresh
