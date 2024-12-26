import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Импорт данных из CSV"

    def handle(self, *args, **kwargs):
        imports = {
            "ingredients": {
                "file_path": "./data/ingredients.csv",
                "model": Ingredient,
                "process_row": self.process_ingredient_row,
            },
        }

        for key, value in imports.items():
            self.import_data(
                value["file_path"], value["model"], value["process_row"]
            )

    def import_data(self, file_path, model, process_row):
        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            ingredient_objects = []
            for row in reader:
                obj = process_row(row, model)
                if obj is not None:
                    ingredient_objects.append(obj)

            model.objects.bulk_create(ingredient_objects)

    def process_ingredient_row(self, row, model):
        model.objects.create(
            name=row["name"],
            measurement_unit=row["measurement_unit"]
        )
