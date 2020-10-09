import os
from pathlib import Path

from django.core.management import BaseCommand

from django.conf import settings


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('new-project-name')
        parser.add_argument('-y', action='store_true')

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR if isinstance(settings.BASE_DIR, Path) else Path(settings.BASE_DIR)
        base_app_dirname = os.path.basename(settings.BASE_DIR)
        base_app_dir = base_dir / base_app_dirname

        new_project_name = options.get('new-project-name')
        new_base_dir = base_dir.parent / new_project_name
        new_base_app_dir = base_dir / new_project_name

        files_to_refactor = \
            [base_dir / file_name for file_name in os.listdir(base_dir) if file_name.endswith('.py')] + \
            [base_app_dir / file_name for file_name in os.listdir(base_app_dir) if file_name.endswith('.py')]

        print("The following changes will be made:")
        print(f"Any instance of the word {base_app_dirname} will be changed to {new_project_name} in these files:")
        for file in files_to_refactor:
            print(file)
        print(f"The base app directory {base_app_dir} will become {new_base_app_dir}")
        print(f"The project directory {base_dir} will become {new_base_dir}")

        if not options.get('y', False):
            confirm = input(f"Are you sure you want make the changes listed above? [y/N]")
            if confirm.lower() not in {'y', 'yes'}:
                print("Cancelling rename.")
                exit(0)

        for file in files_to_refactor:
            if os.path.isfile(file):
                with open(file, 'r+') as f:
                    new = f.read().replace(base_app_dirname, new_project_name)
                    f.seek(0)
                    f.write(new)
                    f.truncate()

        os.rename(base_app_dir, new_base_app_dir)  # project_name/project_name -> project_name/new_project_name
        os.rename(base_dir, new_base_dir)  # project_name/new_project_name -> new_project_name/new_project_name
