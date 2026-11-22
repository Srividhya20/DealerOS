
from decimal import Decimal
from reconcile.compare import compare


def make_a(total="100.00", location="LOC-101",
           date="2026-03-01", state="CONFIRMED"):
    return {
        "REC-1": {
            "total": Decimal(total) if total is not None else None,
            "location": location,
            "date": date,
            "state": state
        }
    }


def make_b(value="100.00", ref="REC-1",
           location="LOC-101", date="2026-03-01",
           entry_id="E1"):
    return [{
        "entry_id": entry_id,
        "ref": ref,
        "value": Decimal(value) if value is not None else None,
        "location": location,
        "date": date
    }]


def test_clean_matching_record():
    assert compare(make_a(), make_b()) == []


def test_missing_in_b():
    result = compare(make_a(), [])

    assert result[0]["reason"] == "MISSING_IN_B"


def test_orphan_in_b():
    result = compare({}, make_b(ref="REC-999"))

    assert result[0]["reason"] == "ORPHAN_IN_B"


def test_value_mismatch():
    result = compare(
        make_a(total="100.00"),
        make_b(value="150.00")
    )

    assert any(x["reason"] == "VALUE_MISMATCH" for x in result)


def test_blank_value():
    result = compare(
        make_a(),
        make_b(value=None)
    )

    assert any(x["reason"] == "VALUE_MISMATCH" for x in result)


def test_duplicate_in_b():
    entries = make_b(value="100.00")
    entries.append({
        **entries[0],
        "entry_id": "E2"
    })

    result = compare(make_a(), entries)

    assert any(x["reason"] == "DUPLICATE_IN_B" for x in result)


def test_valid_split_is_not_duplicate():
    entries = make_b(value="40.00")
    entries.append({
        **entries[0],
        "entry_id": "E2",
        "value": Decimal("60.00")
    })

    result = compare(make_a(total="100.00"), entries)

    assert not any(x["reason"] == "DUPLICATE_IN_B" for x in result)
    assert not any(x["reason"] == "VALUE_MISMATCH" for x in result)


def test_location_mismatch():
    result = compare(
        make_a(),
        make_b(location="LOC-201")
    )

    assert any(x["reason"] == "LOCATION_MISMATCH" for x in result)


def test_date_mismatch():
    result = compare(
        make_a(),
        make_b(date="2026-03-05")
    )

    assert any(x["reason"] == "DATE_MISMATCH" for x in result)


def test_voided_record_in_b():
    result = compare(
        make_a(state="VOIDED"),
        make_b()
    )

    assert any(x["reason"] == "VOIDED_RECORD_IN_B" for x in result)
