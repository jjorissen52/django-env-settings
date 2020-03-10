from django.core.management import BaseCommand
from django.conf import settings


class Command(BaseCommand):

    def handle(self, *args, **options):
        for key, value in settings.ENV.__dict__.items():
            print(f'{key:25} {value}')