
from decimal import Decimal
from datetime import date

from django.test import TestCase

from reconcile.models import (
    Location,
    SystemARecord,
    SystemBEntry
)


class TenantIsolationAPITests(TestCase):

    def setUp(self):

        # Create two organizations
        self.loc_a = Location.objects.create(
            location_id="LOC-101",
            org_id="ORG-A",
            location_name="Branch A"
        )

        self.loc_b = Location.objects.create(
            location_id="LOC-201",
            org_id="ORG-B",
            location_name="Branch B"
        )

        # A record owned by ORG-A
        SystemARecord.objects.create(
            record_id="REC-1001",
            location=self.loc_a,
            location_id_raw="LOC-101",
            event_date=date(2026, 3, 1),
            total_value=Decimal("100.00"),
            state="CONFIRMED"
        )

        # Corresponding B entry is at ORG-B location
        SystemBEntry.objects.create(
            entry_id="ENTRY-1",
            record_ref_raw="REC-1001",
            record_ref="REC-1001",
            location=self.loc_b,
            location_id_raw="LOC-201",
            recorded_on=date(2026, 3, 1),
            value=Decimal("100.00")
        )

        # A normal record owned by ORG-B
        SystemARecord.objects.create(
            record_id="REC-2001",
            location=self.loc_b,
            location_id_raw="LOC-201",
            event_date=date(2026, 3, 2),
            total_value=Decimal("200.00"),
            state="CONFIRMED"
        )

        SystemBEntry.objects.create(
            entry_id="ENTRY-2",
            record_ref_raw="REC-2001",
            record_ref="REC-2001",
            location=self.loc_b,
            location_id_raw="LOC-201",
            recorded_on=date(2026, 3, 2),
            value=Decimal("200.00")
        )

        # An orphan belonging to ORG-B
        SystemBEntry.objects.create(
            entry_id="ENTRY-3",
            record_ref_raw="REC-9999",
            record_ref="REC-9999",
            location=self.loc_b,
            location_id_raw="LOC-201",
            recorded_on=date(2026, 3, 3),
            value=Decimal("50.00")
        )

    def test_org_a_cannot_see_org_b_location(self):

        response = self.client.get(
            "/api/disagreements/?org=ORG-A"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        # Cross-org record should be a location mismatch
        cross_record = [
            item for item in data
            if item["record_id"] == "REC-1001"
        ]

        self.assertEqual(len(cross_record), 1)

        self.assertEqual(
            cross_record[0]["reason"],
            "LOCATION_MISMATCH"
        )

        # ORG-B location must not be exposed
        self.assertEqual(
            cross_record[0]["location"],
            "LOC-101"
        )

        self.assertNotIn(
            "LOC-201",
            str(data)
        )

    def test_org_b_cannot_see_org_a_record(self):

        response = self.client.get(
            "/api/disagreements/?org=ORG-B"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        record_ids = [
            item["record_id"] for item in data
        ]

        # ORG-B must not see ORG-A's record
        self.assertNotIn("REC-1001", record_ids)

        # A clean matching record should not appear as a disagreement
        self.assertNotIn("REC-2001", record_ids)

        # ORG-A location must not be exposed
        self.assertNotIn("LOC-101", str(data))

    def test_orphan_belongs_to_its_own_location_org(self):

        response_a = self.client.get(
            "/api/disagreements/?org=ORG-A"
        )

        response_b = self.client.get(
            "/api/disagreements/?org=ORG-B"
        )

        data_a = response_a.json()
        data_b = response_b.json()

        # ORG-A must not see ORG-B's orphan
        self.assertNotIn(
            "REC-9999",
            [item["record_id"] for item in data_a]
        )

        # ORG-B should see its own orphan
        orphan = [
            item for item in data_b
            if item["record_id"] == "REC-9999"
        ]

        self.assertEqual(len(orphan), 1)

        self.assertEqual(
            orphan[0]["reason"],
            "ORPHAN_IN_B"
        )

    def test_missing_org_returns_400(self):

        response = self.client.get(
            "/api/disagreements/"
        )

        self.assertEqual(response.status_code, 400)
