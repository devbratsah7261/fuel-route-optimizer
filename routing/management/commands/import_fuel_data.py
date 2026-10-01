import csv
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand

from routing.models import FuelStation


class Command(BaseCommand):
    help = "Import fuel station data from CSV"

    def handle(self, *args, **options):

        csv_path = Path("data/fuel-prices.csv")

        if not csv_path.exists():
            self.stdout.write(
                self.style.ERROR(
                    f"CSV file not found: {csv_path}"
                )
            )
            return

        stations = []

        with csv_path.open(
            mode="r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                stations.append(
                    FuelStation(
                        opis_truckstop_id=int(row["OPIS Truckstop ID"]),
                        truckstop_name=row["Truckstop Name"].strip(),
                        address=row["Address"].strip(),
                        city=row["City"].strip(),
                        state=row["State"].strip(),
                        rack_id=int(row["Rack ID"]),
                        retail_price=Decimal(row["Retail Price"]),
                    )
                )

        FuelStation.objects.all().delete()

        FuelStation.objects.bulk_create(stations)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(stations)} fuel stations."
            )
        )