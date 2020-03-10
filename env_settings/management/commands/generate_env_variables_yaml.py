import os

from django.core.management import BaseCommand
from django.template.loader import render_to_string

from django.conf import settings


class Command(BaseCommand):

    @staticmethod
    def generate():
        params = settings.ENV
        allowed_hosts = ','.join(params.ALLOWED_HOSTS) if isinstance(params.ALLOWED_HOSTS, list) else params.ALLOWED_HOSTS
        params.ALLOWED_HOSTS = allowed_hosts
        env_variables = render_to_string('env_variables_template.yaml',
                                        {"parameters": params.__dict__})
        with open(os.path.join(settings.BASE_DIR, 'env_variables.yaml'), 'w') as f:
            f.write(env_variables)

    def add_arguments(self, parser):
        parser.add_argument('-y', action='store_true')

    def handle(self, *args, **options):
        if options.get('y', False):
            self.generate()
        else:
            confirm = input("Are you sure you want to generate env_variables.yaml the project root?"
                            " This will override the existing version of that file. [y/N] ")
            if confirm.lower() in ('y', 'yes'):
                self.generate()
            else:
                print("cancelled.")
