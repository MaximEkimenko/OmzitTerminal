import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from worker.views import pause_work, resume_work

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
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE, job_defaults={'misfire_grace_time': 1*60})
        scheduler.add_jobstore(DjangoJobStore(), "default")
        print("Scheduler запущен")
        scheduler.add_job(
            pause_work,
            kwargs={'is_lunch': True, },
            trigger=CronTrigger(hour="12"),
            id="Приостановка работы в обед",
            max_instances=1,
            replace_existing=True,
            misfire_grace_time=1*60,
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

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
