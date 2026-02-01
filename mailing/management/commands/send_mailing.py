from django.core.management.base import BaseCommand

from mailing.models import Mailing
from mailing.views import send_mailing_now


class Command(BaseCommand):
    help = "Отправить рассылку по ID"

    def add_arguments(self, parser):
        parser.add_argument("mailing_id", type=int, help="ID рассылки для отправки")

    def handle(self, *args, **options):
        mailing_id = options["mailing_id"]
        try:
            mailing = Mailing.objects.get(pk=mailing_id)
            send_mailing_now(mailing)
            self.stdout.write(
                self.style.SUCCESS(f"Рассылка {mailing_id} успешно отправлена.")
            )
        except Mailing.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Рассылка с ID {mailing_id} не найдена.")
            )
