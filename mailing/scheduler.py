import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger("mailing")

# Глобальная переменная для планировщика
scheduler = None


def start_scheduler():
    global scheduler
    if scheduler is not None:
        return  # уже запущен

    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Планируем задачу проверки рассылок каждые 60 секунд
    scheduler.add_job(
        check_and_schedule_mailings,
        "interval",
        seconds=60,
        id="check_mailings",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Планировщик запущен — проверка рассылок каждые 60 секунд")


def check_and_schedule_mailings():
    global scheduler
    if scheduler is None:
        logger.warning("Планировщик не запущен")
        return

    from mailing.models import \
        Mailing  # импорт внутри, чтобы избежать циклического импорта

    now = timezone.now()
    mailings = Mailing.objects.filter(status="created", start_time__lte=now)

    logger.info(f"Проверка рассылок: найдено {mailings.count()} готовых к отправке")

    for mailing in mailings:
        if now > mailing.end_time:
            mailing.status = "completed"
            mailing.save()
            logger.info(f"Рассылка ID={mailing.id} завершена (время окончания прошло)")
            continue

        # Импорт функции отправки внутри функции
        from mailing.views import send_mailing_now

        job_id = f"mailing_{mailing.id}"

        # Если задача ещё не запланирована — добавляем
        if scheduler.get_job(job_id) is None:
            scheduler.add_job(
                send_mailing_now,
                "date",
                run_date=mailing.start_time,
                args=[mailing],
                id=job_id,
                replace_existing=True,
            )
            logger.info(
                f"Запланирована отправка рассылки ID={mailing.id} на {mailing.start_time}"
            )

        # Если время уже наступило — запускаем немедленно
        if now >= mailing.start_time:
            logger.info(f"Моментальная отправка рассылки ID={mailing.id}")
            send_mailing_now(mailing)
