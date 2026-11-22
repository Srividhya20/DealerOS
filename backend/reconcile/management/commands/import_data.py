
import csv
import re

from pathlib import Path
from datetime import date
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.management.base import BaseCommand

from reconcile.models import Location, SystemARecord, SystemBEntry


def clean_text(value):
    """Remove unwanted spaces from CSV text."""
    return (value or "").strip()


def normalize_ref(raw):
    """Convert different reference formats into REC-XXXX."""
    match = re.search(r"\d+", clean_text(raw))

    if not match:
        return None

    return f"REC-{match.group()}"


def parse_amount(raw):
    """Convert CSV amount into Decimal. Invalid values become None."""
    value = clean_text(raw).replace(",", "")

    if not value:
        return None

    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def parse_date(raw):
    """Convert date text into a Python date."""
    value = clean_text(raw)

    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def read_csv(file_path):
    """Read CSV without automatically converting values."""
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            yield {
                key: clean_text(value)
                for key, value in row.items()
                if key is not None
            }


class Command(BaseCommand):

    help = "Import locations, System A and System B CSV data"

    def handle(self, *args, **options):

        data_dir = Path(settings.BASE_DIR) / "data"

        locations_file = data_dir / "locations.csv"
        system_a_file = data_dir / "system_a.csv"
        system_b_file = data_dir / "system_b.csv"

        files = [
            locations_file,
            system_a_file,
            system_b_file
        ]

        for file_path in files:
            if not file_path.exists():
                self.stderr.write(
                    self.style.ERROR(f"File not found: {file_path}")
                )
                return

        # Import locations first
        location_stats = self.import_locations(locations_file)

        # Import System A records
        a_stats = self.import_system_a(system_a_file)

        # Import System B entries
        b_stats = self.import_system_b(system_b_file)

        self.stdout.write("\n========== IMPORT SUMMARY ==========")

        self.stdout.write(
            f"Locations: {location_stats['read']} read, "
            f"{location_stats['saved']} saved"
        )

        self.stdout.write(
            f"System A: {a_stats['read']} read, "
            f"{a_stats['saved']} saved"
        )

        self.stdout.write(
            f"System B: {b_stats['read']} read, "
            f"{b_stats['saved']} saved"
        )

        self.stdout.write(
            f"Rows with errors: "
            f"{location_stats['errors'] + a_stats['errors'] + b_stats['errors']}"
        )

        self.stdout.write(self.style.SUCCESS("Import completed."))

    def import_locations(self, file_path):

        stats = {"read": 0, "saved": 0, "errors": 0}

        for row in read_csv(file_path):
            stats["read"] += 1

            try:
                Location.objects.update_or_create(
                    location_id=row["location_id"],
                    defaults={
                        "org_id": row["org_id"],
                        "location_name": row.get("location_name", "")
                    }
                )

                stats["saved"] += 1

            except Exception as error:
                stats["errors"] += 1
                self.stderr.write(
                    f"Location row {stats['read']}: {error}"
                )

        return stats

    def import_system_a(self, file_path):

        stats = {"read": 0, "saved": 0, "errors": 0}

        for row in read_csv(file_path):
            stats["read"] += 1

            try:
                location_id = row["location_id"]

                location = Location.objects.filter(
                    location_id=location_id
                ).first()

                actor_id = row.get("actor_id") or None

                SystemARecord.objects.update_or_create(
                    record_id=row["record_id"],
                    defaults={
                        "location": location,
                        "location_id_raw": location_id,
                        "event_date": parse_date(row.get("event_date")),
                        "event_date_raw": row.get("event_date", ""),
                        "category_code": row.get("category_code", ""),
                        "actor_id": actor_id,
                        "base_value": parse_amount(row.get("base_value")),
                        "base_value_raw": row.get("base_value", ""),
                        "adjustment": parse_amount(row.get("adjustment")),
                        "adjustment_raw": row.get("adjustment", ""),
                        "total_value": parse_amount(row.get("total_value")),
                        "total_value_raw": row.get("total_value", ""),
                        "state": row.get("state", "")
                    }
                )

                stats["saved"] += 1

            except Exception as error:
                stats["errors"] += 1
                self.stderr.write(
                    f"System A row {stats['read']}: {error}"
                )

        return stats

    def import_system_b(self, file_path):

        stats = {"read": 0, "saved": 0, "errors": 0}

        for row in read_csv(file_path):
            stats["read"] += 1

            try:
                location_id = row["location_id"]

                location = Location.objects.filter(
                    location_id=location_id
                ).first()

                SystemBEntry.objects.update_or_create(
                    entry_id=row["entry_id"],
                    defaults={
                        "record_ref_raw": row.get("record_ref", ""),
                        "record_ref": normalize_ref(
                            row.get("record_ref", "")
                        ),
                        "location": location,
                        "location_id_raw": location_id,
                        "recorded_on": parse_date(
                            row.get("recorded_on")
                        ),
                        "recorded_on_raw": row.get("recorded_on", ""),
                        "value": parse_amount(row.get("value")),
                        "value_raw": row.get("value", ""),
                        "label": row.get("label", "")
                    }
                )

                stats["saved"] += 1

            except Exception as error:
                stats["errors"] += 1
                self.stderr.write(
                    f"System B row {stats['read']}: {error}"
                )

        return stats
