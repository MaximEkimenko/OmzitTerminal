import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from scheduler.views import shift_tasks_auto_report
from worker.views import pause_work, resume_work
from scheduler.services.schedule_handlers import days_report_create, report_json_create_schedule, report_merger_schedule

logger = logging.getLogger(__name__)


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.

    :param max_age: The maximum length of time to retain historical job execution records.
                    Defaults to 7 days.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs APScheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE, job_defaults={'misfire_grace_time': 1 * 60})
        scheduler.add_jobstore(DjangoJobStore(), "default")
        print("Scheduler запущен")
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
        logger.info(
            "Запущена еженедельная задача: 'delete_old_job_executions'."
        )

        # scheduler.add_job( # TODO ФУНКЦИОНАЛ ОТЧЁТОВ законсервировано пока не понадобится
        #     shift_tasks_auto_report,
        #     trigger=CronTrigger(hour="07", minute="30"),
        #     id="Получение отчета по СЗ",
        #     max_instances=1,
        #     replace_existing=True,
        #     misfire_grace_time=1 * 60,
        # )
        # scheduler.add_job(
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

        logger.info("Запущена объединения отчётов")
        # report_merger_schedule
        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
