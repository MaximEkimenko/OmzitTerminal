from datetime import datetime

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from orders.utils.tasks import (
    create_ppr_at_first_run,
    create_ppr_for_next_month,
    CREATE_NEXT_MONTH_PPR_DAY, suspend_orders_end_of_day,
)
from orders.utils.workers_process import clear_all_dayworkers
from worker.views import pause_work, resume_work  # noqa

from m_logger_settings import logger, json_log_refactor_and_xlsx  # noqa
from scheduler.services.sz_reports import shift_tasks_auto_report  # noqa
from scheduler.services.create_fio_report import create_fio_report_schedule  # noqa


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs APScheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(
            timezone=settings.TIME_ZONE, job_defaults={"misfire_grace_time": 1 * 60}
        )
        scheduler.add_jobstore(DjangoJobStore(), "default")

        logger.info("Команда runscheduler выполнена успешно.")
        """
        scheduler.add_job(
            pause_work,
            kwargs={'is_lunch': True, },
            trigger=CronTrigger(hour="12"),
            id="Приостановка работы в обед",
            max_instances=1,
            replace_existing=True,
            misfire_grace_time=1 * 60,
        )
        logger.info("Запущена задача 'Приостановка работы в обед' каждый день в 12:00.")

        scheduler.add_job(
            pause_work,
            trigger=CronTrigger(hour="20"),
            id="Приостановка работы в конце смены",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Запущена задача 'Приостановка работы в конце смены' каждый день в 20:00.")

        scheduler.add_job(
            resume_work,
            kwargs={'is_lunch': True, },
            trigger=CronTrigger(hour="13"),
            id="Возобновление работы после обеда",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Запущена задача 'Возобновление работы после обеда' каждый день в 13:00.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Запущена еженедельная задача: 'delete_old_job_executions'.")

        scheduler.add_job(
            shift_tasks_auto_report,
            trigger=CronTrigger(hour="07", minute="30"),
            id="Получение отчета по СЗ",
            max_instances=1,
            replace_existing=True,
            misfire_grace_time=1 * 60,
        )
        logger.info('Запущена задача: "Получение отчета по СЗ"')

        # scheduler.add_job(
        #     json_log_refactor_and_xlsx,
        #     trigger=CronTrigger(hour="00", minute="05"),
        #     id="Формирование log файлов json и xlsx",
        #     max_instances=1,
        #     replace_existing=True,
        #     misfire_grace_time=1 * 60,
        # )
        # logger.info('Запущена задача: "Формирование log файлов json и xlsx"')

        scheduler.add_job(
            create_fio_report_schedule,
            trigger=CronTrigger(hour="20", minute="00"),
            id="Формирование отчётов для рабочих",
            max_instances=1,
            replace_existing=True,
            misfire_grace_time=1 * 60,
        )
        logger.info('Запущена задача: "Формирование отчётов для рабочих"')

        """
        scheduler.add_job(
            suspend_orders_end_of_day,
            # trigger=CronTrigger(hour="20", minute="0"),
            trigger=CronTrigger(minute="*/4"),
            id="Снятие ремонтников с заявок в конце смены",
            max_instances=1,
            replace_existing=True,
            misfire_grace_time=1 * 60,
        )
        logger.info("Запущена задача: Снятие ремонтников с заявок в конце смены")

        # запускаем задание два дня подряд, на случай, если в первый раз не отработало
        ppr_run_days = f"{CREATE_NEXT_MONTH_PPR_DAY},{CREATE_NEXT_MONTH_PPR_DAY + 1}"
        scheduler.add_job(
            create_ppr_for_next_month,
            trigger=CronTrigger(day=ppr_run_days, hour=22),
            id="Создание заданий ППР на следующий месяц",
            max_instances=1,
            replace_existing=True,
            misfire_grace_time=1 * 60,
        )
        logger.info("Запущена задача по созданию заявок ППР на следующий месяц")

        scheduler.add_job(
            create_ppr_at_first_run,
            "date",
            id="Создание заявок ППР при первой запуске",
            max_instances=1,
            replace_existing=True,
            misfire_grace_time=1 * 60,
        )
        logger.info("Запущена задача по первоначальному созданию заявок ППР")

        # scheduler.add_job( # TODO ФУНКЦИОНАЛ ОТЧЁТОВ законсервировано пока не понадобится
        #     days_report_create,
        #     trigger=CronTrigger(day="01", hour="00", minute="01"),
        #     id="Заполнение дней следующего месяца",
        #     max_instances=1,
        #     replace_existing=True,
        #     misfire_grace_time=1 * 60,
        # )
        # # словарь для множественного запуска report_json_create_schedule
        # run_times = {
        #     "Чтение данных дуги": {"hour": "06", "minute": "05"},
        #     "Чтение данных дуги, ОТК и ОТПБ 1": {"hour": "08", "minute": "30"},
        #     "Чтение данных дуги, ОТК и ОТПБ 2": {"hour": "08", "minute": "44"},
        #     "Чтение данных дуги, ОТК и ОТПБ 3": {"hour": "08", "minute": "53"},
        # }
        # # множественный запуск report_json_create_schedule
        # for _id in run_times:
        #     scheduler.add_job(
        #         report_json_create_schedule,
        #         trigger=CronTrigger(**run_times[_id]),
        #         id=_id,
        #         max_instances=1,
        #         replace_existing=True,
        #         misfire_grace_time=2 * 60,
        #     )
        # scheduler.add_job(
        #     report_merger_schedule,
        #     trigger=CronTrigger(hour="08", minute="56"),
        #     id="Объединение отчётов цехов",
        #     max_instances=1,
        #     replace_existing=True,
        #     misfire_grace_time=1 * 60,
        # )
        # logger.info("Запущена объединения отчётов")
        # report_merger_schedule
        try:
            scheduler.start()
        except Exception as e:
            logger.error("Ошибка запуска команды runscheduler.")
            logger.exception(e)
