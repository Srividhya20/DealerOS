
from decimal import Decimal


def compare(a_rows, b_rows):
    """
    Compare System A records with System B entries.

    a_rows:
        {
            "REC-1001": {
                "total": Decimal("100.00"),
                "location": "LOC-101",
                "date": "2026-03-01",
                "state": "CONFIRMED"
            }
        }

    b_rows:
        [
            {
                "entry_id": "E1",
                "ref": "REC-1001",
                "value": Decimal("100.00"),
                "location": "LOC-101",
                "date": "2026-03-01"
            }
        ]
    """

    disagreements = []
    by_ref = {}

    # Group B entries by their cleaned reference
    for entry in b_rows:
        by_ref.setdefault(entry["ref"], []).append(entry)

    # Helper to create a consistent disagreement result
    def add_issue(reason, record_id, a=None, entries=None):
        entries = entries or []

        disagreements.append({
            "reason": reason,
            "record_id": record_id,
            "entry_ids": [e["entry_id"] for e in entries],
            "a_value": a["total"] if a else None,
            "b_values": [e["value"] for e in entries],
            "a_location": a["location"] if a else None,
            "b_locations": [e["location"] for e in entries],
            "a_date": a["date"] if a else None,
            "b_dates": [e["date"] for e in entries],
        })

    # 1. Find orphan entries in B
    for entry in b_rows:
        if entry["ref"] not in a_rows:
            add_issue(
                "ORPHAN_IN_B",
                entry["ref"],
                entries=[entry]
            )

    # 2. Compare every A record
    for record_id, a in a_rows.items():

        entries = by_ref.get(record_id, [])

        # Missing entry in B
        if not entries:
            add_issue(
                "MISSING_IN_B",
                record_id,
                a=a
            )
            continue

        # Voided record still present in B
        if a["state"] == "VOIDED":
            add_issue(
                "VOIDED_RECORD_IN_B",
                record_id,
                a=a,
                entries=entries
            )

        # Check whether any B value is blank
        if any(e["value"] is None for e in entries):
            add_issue(
                "VALUE_MISMATCH",
                record_id,
                a=a,
                entries=entries
            )

        # Check multiple B entries
        elif len(entries) > 1:

            total_b = sum(
                (e["value"] for e in entries),
                Decimal("0")
            )

            if a["total"] is None or total_b != a["total"]:
                add_issue(
                    "DUPLICATE_IN_B",
                    record_id,
                    a=a,
                    entries=entries
                )

            # A valid split is not a disagreement.
            # Continue checking its dates and locations.

        # Check a single B entry
        elif a["total"] is None or entries[0]["value"] != a["total"]:
            add_issue(
                "VALUE_MISMATCH",
                record_id,
                a=a,
                entries=entries
            )

        # Check date and location for every entry
        for entry in entries:

            if entry["location"] != a["location"]:
                add_issue(
                    "LOCATION_MISMATCH",
                    record_id,
                    a=a,
                    entries=[entry]
                )

            if entry["date"] != a["date"]:
                add_issue(
                    "DATE_MISMATCH",
                    record_id,
                    a=a,
                    entries=[entry]
                )

    return disagreements
