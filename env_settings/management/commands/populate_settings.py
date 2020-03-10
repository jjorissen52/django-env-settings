import os
import re

from django.core.management import BaseCommand
from django.template.loader import render_to_string

from django.conf import settings

desired_settings = {
    "DEBUG": "1",
    "SECRET_KEY": 'very-secret',
    "USE_SQLITE": "0",
    "DATABASE_NAME": "postgres",
    "DATABASE_USER": "postgres",
    "DATABASE_PASSWORD": "superstrongpassword123",
    "DATABASE_HOST": "127.0.0.1",
    "DATABASE_PORT": "5432",
    "INITIAL_ADMIN_EMAIL": "example@email.com",
    "INITIAL_ADMIN_PASSWORD": "password123",
    "ALLOWED_HOSTS": ["*"],
}


class Command(BaseCommand):

    @staticmethod
    def get_default_settings():
        # get the defaults from the project settings if possible, and if not from the desired_settings above
        return {setting: getattr(settings, setting, default) for setting, default in desired_settings.items()}

    @staticmethod
    def render_template():
        _settings = Command.get_default_settings()
        environment_defaults = render_to_string('env_settings_template',
                                                context={'env': _settings})
        return environment_defaults

    @staticmethod
    def generate(settings_file, should_write):
        with open(os.path.abspath(settings_file), 'r') as f:
            settings_lines = f.readlines()

        imports_end = 0
        for i, line in enumerate(settings_lines):
            if line.startswith("import os"):
                imports_end = i + 1
                break

        if not any("from env_settings import utils" in line for line in settings_lines):
            settings_lines = settings_lines[:imports_end] + ["from env_settings import utils"] + settings_lines[imports_end:]

        try:
            environment_defaults_start = settings_lines.index("# { start } generated using python manage.py populate_settings\n")
        except:
            environment_defaults_start = 0

        if environment_defaults_start:
            try:
                environment_defaults_end = settings_lines.index("# { end }\n")
            except:
                environment_defaults_end = environment_defaults_start
            settings_lines = settings_lines[:environment_defaults_start] + settings_lines[:environment_defaults_end]

        for i, line in enumerate(settings_lines):
            if line.startswith("BASE_DIR"):
                environment_defaults_start = i + 1
                break

        environment_defaults = Command.render_template()
        settings_str = "".join(settings_lines[:environment_defaults_start]) + f'\n{environment_defaults}\n' + "".join(settings_lines[environment_defaults_start:])
        if should_write:
            with open(settings_file, 'w') as f:
                f.write(settings_str)
        else:
            print(settings_str)

    def add_arguments(self, parser):
        parser.add_argument('-y', action='store_true')
        parser.add_argument('--settings-file')

    def handle(self, *args, **options):
        settings_file = options.get("settings-file", None)
        if not settings_file:
            settings_file = os.path.join(settings.BASE_DIR, settings.BASE_DIR.split("/")[-1], "settings.py")

        if options.get('y', False):
            print(self.get_default_settings())
        else:
            confirm = input("Are you sure you want to generate settings.py in the project root?"
                            " This will override any existing version of that file. [y/N] ")
            should_write = confirm.lower() in ('y', 'yes')
            self.generate(settings_file, should_write)
