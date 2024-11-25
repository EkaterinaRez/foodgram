import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredients


class Command(BaseCommand):
    help = "Импорт данных из CSV"

    def handle(self, *args, **kwargs):
        imports = {
            "ingredients": {
                "file_path": "/data/ingredients.csv",
                "model": Ingredients,
                "process_row": self.process_ingridient_row,
            },
        }

        for key, value in imports.items():
            self.import_data(
                value["file_path"], value["model"], value["process_row"]
            )

    def import_data(self, file_path, model, process_row):
        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                process_row(row, model)

    def process_ingridient_row(self, row, model):
        model.objects.create(
            name=row["name"],
            measurement_unit=row["measurement_unit"]
        )
