import os
import sys
from env_settings import utils

from django.core.management import BaseCommand
from django.template.loader import render_to_string

from django.conf import settings

env_settings_dict = {}

basic_settings = {
    "DEBUG": "1",
    "SECRET_KEY": 'very-secret',
    "INITIAL_ADMIN_EMAIL": "example@email.com",
    "INITIAL_ADMIN_PASSWORD": "password123",
    "ALLOWED_HOSTS": ["*"],
}

db_settings = {
    "USE_SQLITE": "0",
    "DATABASE_NAME": "postgres",
    "DATABASE_USER": "postgres",
    "DATABASE_PASSWORD": "superstrongpassword123",
    "DATABASE_HOST": "127.0.0.1",
    "DATABASE_PORT": "5432",
}

start_string = "# { start } generated using python manage.py populate_settings\n"
end_string = "# { end }\n"


class Command(BaseCommand):

    @staticmethod
    def get_default_settings():
        # get the defaults from the project settings if possible, and if not from the desired_settings above
        return {setting: utils.quoted_string(getattr(settings, setting, default)) for setting, default in env_settings_dict.items()}

    @staticmethod
    def locate_setting_line(setting, settings_lines):
        for i, line in enumerate(settings_lines):
            if line.startswith(setting) and not f"ENV.{setting}" in line:
                return i
        return -1

    @staticmethod
    def remove_setting(setting, settings_lines):
        setting_line = Command.locate_setting_line(setting, settings_lines)
        if setting_line != -1:
            return settings_lines[:setting_line] + settings_lines[setting_line + 1:]
        return settings_lines

    @staticmethod
    def dict_bounds(indicator, lines):
        bounds_start, bounds_end = -1, -1
        for i, line in enumerate(lines):
            if line.startswith(indicator):
                bounds_start, bounds_end = i, i
                brace_count, cont, curent_line = 0, True, bounds_start
                while True:
                    if "{" in lines[curent_line]:
                        brace_count += 1
                    if "}" in lines[curent_line]:
                        brace_count -= 1
                        if brace_count < 1:
                            break
                    curent_line += 1
                bounds_end = curent_line
                break
        return bounds_start, bounds_end

    @staticmethod
    def update_database_setting(settings_lines, postgres=False, gae=False):
        db_settings_start, db_settings_end = Command.dict_bounds("DATABASE", settings_lines)
        if db_settings_start == -1:
            raise Exception("Could not find DATABASE setting in settings.py. "
                            "This script is only capable of finding DATABASE setting defined "
                            "as a dictionary in the root settings module.")
        new_db_setting_string = render_to_string("db_settings_template", context={"gae": gae, "postgres": postgres})
        db_setting_as_lines = [f'{line}\n' for line in new_db_setting_string.split("\n")]
        return settings_lines[:db_settings_start] + db_setting_as_lines + settings_lines[db_settings_end + 1:]

    @staticmethod
    def update_logging_settings(settings_lines):
        new_logging_settings_string = render_to_string("logging_settings_template")
        logging_settings_as_lines = [f'{line}\n' for line in new_logging_settings_string.split("\n")]
        logging_settings_start, logging_settings_end = Command.dict_bounds("LOGGING", settings_lines)
        if logging_settings_start == -1:
            return settings_lines + logging_settings_as_lines
        return settings_lines[:logging_settings_start] + logging_settings_as_lines + settings_lines[logging_settings_end + 1:]

    @staticmethod
    def update_static_settings(settings_lines):
        new_static_settings_string = render_to_string("static_settings_template")
        static_settings_as_lines = [f'{line}\n' for line in new_static_settings_string.split("\n")]
        static_url_line = Command.locate_setting_line("STATIC_URL", settings_lines)
        if static_url_line != -1:
            return settings_lines[:static_url_line] + static_settings_as_lines + settings_lines[static_url_line + 1:]
        return settings_lines

    @staticmethod
    def update_environment_defaults(settings_lines):
        imports_end = 0
        for i, line in enumerate(settings_lines):
            if line.startswith("import os"):
                imports_end = i + 1
                break

        if not any("from env_settings import utils" in line for line in settings_lines):
            settings_lines = settings_lines[:imports_end] + ["from env_settings import utils"] + settings_lines[
                                                                                                 imports_end:]

        try:
            environment_defaults_start = settings_lines.index(start_string)
        except:
            environment_defaults_start = 0

        if environment_defaults_start:
            try:
                environment_defaults_end = settings_lines.index(end_string)
            except:
                environment_defaults_end = environment_defaults_start
            settings_lines = settings_lines[:environment_defaults_start] + settings_lines[environment_defaults_end:]

        for i, line in enumerate(settings_lines):
            if line.startswith("BASE_DIR"):
                environment_defaults_start = i + 1
                break

        default_settings = Command.get_default_settings()
        for setting in default_settings:
            settings_lines = Command.remove_setting(setting, settings_lines)

        environment_defaults_string = render_to_string('env_settings_template',
                                                       context={'env': default_settings, "start_string": start_string,
                                                       "end_string": end_string})
        defaults_as_settings_lines = [f'{line}\n' for line in environment_defaults_string.split("\n")]
        settings_lines = settings_lines[:environment_defaults_start] + defaults_as_settings_lines + settings_lines[environment_defaults_start:]
        return settings_lines

    @staticmethod
    def generate(settings_file, should_write, postgres, gae, static, logging):
        with open(os.path.abspath(settings_file), 'r') as f:
            settings_lines = f.readlines()

        settings_lines = Command.update_database_setting(settings_lines, postgres, gae)
        settings_lines = Command.update_environment_defaults(settings_lines)
        if logging:
            settings_lines = Command.update_logging_settings(settings_lines)
        if static:
            settings_lines = Command.update_static_settings(settings_lines)

        settings_str = "".join(settings_lines)

        if should_write:
            with open(settings_file, 'w') as f:
                f.write(settings_str)
        else:
            sys.stdout.write(settings_str)

    def add_arguments(self, parser):
        parser.add_argument('-y', action='store_true')
        parser.add_argument('--settings-file')
        parser.add_argument('--postgres', action='store_true')
        parser.add_argument('--gae', action='store_true')
        parser.add_argument('--static', action='store_true')
        parser.add_argument('--logging', action='store_true')

    def handle(self, *args, **options):
        settings_file = options.get("settings-file", None)
        if not settings_file:
            settings_file = os.path.join(settings.BASE_DIR, settings.BASE_DIR.split("/")[-1], "settings.py")

        if options.get('y', False):
            should_write = True
        else:
            # confirm = input("Are you sure you want to generate settings.py in the project root?"
            #                 " This will override any existing version of that file. [y/N] ")
            # should_write = confirm.lower() in ('y', 'yes')
            should_write = False

        gae = options.get('gae', False)
        postgres = gae if gae else options.get("postgres", False)

        env_settings_dict.update(basic_settings)
        if postgres:
            env_settings_dict.update(db_settings)
        if gae:
            env_settings_dict["GAE_APPLICATION"] = False
        static = options.get('static', False)
        logging = options.get('logging', False)

        self.generate(settings_file, should_write, postgres, gae, static, logging)
