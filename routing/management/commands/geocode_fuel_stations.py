import csv
import io
import requests

from django.core.management.base import BaseCommand

from routing.models import FuelStation


CENSUS_URL = (
    "https://geocoding.geo.census.gov/"
    "geocoder/locations/addressbatch"
)

BENCHMARK = "Public_AR_Current"
BATCH_SIZE = 250


class Command(BaseCommand):
    help = "Geocode fuel stations in batches using Census Geocoder"

    def handle(self, *args, **options):

        stations = list(
            FuelStation.objects.filter(
                latitude__isnull=True,
                longitude__isnull=True,
            )
        )

        total = len(stations)

        if total == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "All fuel stations already have coordinates."
                )
            )
            return

        self.stdout.write(
            f"Total stations to geocode: {total}"
        )

        total_updated = 0
        total_unmatched = 0

        for start in range(0, total, BATCH_SIZE):

            batch = stations[start:start + BATCH_SIZE]

            batch_number = (start // BATCH_SIZE) + 1
            total_batches = (
                (total + BATCH_SIZE - 1) // BATCH_SIZE
            )

            self.stdout.write(
                f"\nProcessing batch "
                f"{batch_number}/{total_batches} "
                f"({len(batch)} stations)..."
            )

            batch_file = io.StringIO()
            writer = csv.writer(batch_file)

            for station in batch:
                writer.writerow([
                    station.id,
                    station.address,
                    station.city,
                    station.state,
                    "",
                ])

            batch_file.seek(0)

            files = {
                "addressFile": (
                    "fuel_stations.csv",
                    batch_file.getvalue(),
                    "text/csv",
                )
            }

            params = {
                "benchmark": BENCHMARK,
            }

            try:
                response = requests.post(
                    CENSUS_URL,
                    params=params,
                    files=files,
                    timeout=60,
                )

                response.raise_for_status()

            except requests.exceptions.RequestException as error:
                self.stdout.write(
                    self.style.ERROR(
                        f"Batch {batch_number} failed: {error}"
                    )
                )
                continue

            reader = csv.reader(
                io.StringIO(response.text)
            )

            updated = 0
            unmatched = 0

            for row in reader:

                if len(row) < 6:
                    continue

                try:
                    station_id = int(row[0])
                except ValueError:
                    continue

                match_status = row[2]

                if match_status != "Match":
                    unmatched += 1
                    continue

                coordinates = row[5]

                if not coordinates:
                    unmatched += 1
                    continue

                try:
                    longitude, latitude = coordinates.split(",")

                    station = FuelStation.objects.get(
                        id=station_id
                    )

                    station.latitude = float(latitude)
                    station.longitude = float(longitude)

                    station.save(
                        update_fields=[
                            "latitude",
                            "longitude",
                        ]
                    )

                    updated += 1

                except (
                    ValueError,
                    FuelStation.DoesNotExist,
                ):
                    unmatched += 1

            total_updated += updated
            total_unmatched += unmatched

            self.stdout.write(
                f"Batch {batch_number} completed: "
                f"Updated={updated}, "
                f"Unmatched={unmatched}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\nGeocoding process completed."
            )
        )

        self.stdout.write(
            f"Total updated: {total_updated}"
        )

        self.stdout.write(
            f"Total unmatched: {total_unmatched}"
        )    