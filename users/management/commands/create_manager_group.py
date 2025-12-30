from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создаёт группу "Менеджеры", если её нет'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name="Менеджеры")
        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Менеджеры" успешно создана.'))
        else:
            self.stdout.write(self.style.WARNING('Группа "Менеджеры" уже существует.'))
