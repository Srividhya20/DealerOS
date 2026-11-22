
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q

from .models import Location, SystemARecord, SystemBEntry
from .compare import compare


@require_GET
def disagreements_api(request):

    org_id = request.GET.get("org")

    # Validate organization
    if not org_id:
        return JsonResponse(
            {"error": "Please provide an org parameter."},
            status=400
        )

    if not Location.objects.filter(org_id=org_id).exists():
        return JsonResponse(
            {"error": "Invalid organization."},
            status=400
        )

    # Fetch System A records belonging to the requested organization
    a_queryset = SystemARecord.objects.filter(
        location__org_id=org_id
    ).select_related("location")

    a_record_ids = list(
        a_queryset.values_list("record_id", flat=True)
    )

    # Get all System A record IDs for cross-organization checks
    all_a_record_ids = set(
        SystemARecord.objects.values_list("record_id", flat=True)
    )

    # Fetch System B entries belonging to this organization
    # or matching its System A records
    b_queryset = SystemBEntry.objects.filter(
        Q(location__org_id=org_id) |
        Q(record_ref__in=a_record_ids)
    ).select_related("location").distinct()

    # Prepare System A data
    a_rows = {}

    for record in a_queryset:
        a_rows[record.record_id] = {
            "total": record.total_value,
            "location": record.location_id_raw,
            "date": (
                record.event_date.isoformat()
                if record.event_date else None
            ),
            "state": record.state
        }

    # Prepare System B data
    b_rows = []

    for entry in b_queryset:

        # Exclude entries referring to another organization's A record
        if (
            entry.record_ref in all_a_record_ids
            and entry.record_ref not in a_record_ids
        ):
            continue

        b_rows.append({
            "entry_id": entry.entry_id,
            "ref": entry.record_ref,
            "value": entry.value,
            "location": entry.location_id_raw,
            "date": (
                entry.recorded_on.isoformat()
                if entry.recorded_on else None
            )
        })

    # Compare both systems
    results = compare(a_rows, b_rows)

    # Filter by disagreement reason
    reason = request.GET.get("reason")

    if reason:
        results = [
            item for item in results
            if item["reason"] == reason
        ]

    # Calculate difference for sorting
    def get_difference(item):

        a_value = item["a_value"]
        b_values = item["b_values"]

        if a_value is None:
            return None

        if any(value is None for value in b_values):
            return None

        return a_value - sum(b_values, Decimal("0"))

    # Sort by actual difference
    sort = request.GET.get("sort", "value")

    if sort in ("value", "-value"):

        results.sort(
            key=lambda item: (
                get_difference(item) is None,
                (
                    get_difference(item)
                    if sort == "value"
                    else -get_difference(item)
                ) if get_difference(item) is not None
                else Decimal("0")
            )
        )

    # Prepare API response
    response_data = []

    for item in results:

        b_values = item["b_values"]

        if (
            item["a_value"] is not None
            and all(value is not None for value in b_values)
        ):
            difference = item["a_value"] - sum(
                b_values,
                Decimal("0")
            )
        else:
            difference = None

        response_data.append({
            "reason": item["reason"],
            "record_id": item["record_id"],
            "location": item["a_location"],
            "a_value": (
                str(item["a_value"])
                if item["a_value"] is not None else None
            ),
            "b_value": [
                str(value) if value is not None else None
                for value in b_values
            ],
            "difference": (
                str(difference)
                if difference is not None else None
            )
        })

    return JsonResponse(response_data, safe=False)
