# Technical Decisions – DealerOS

## 1. Technology Stack

**Decision:** Use Django REST Framework, SQLite, and React.

**Alternative considered:** Building the entire application using a single framework.

**Reason:** Django provides backend APIs and database management, while React makes it easier to build an interactive reconciliation dashboard. SQLite keeps the setup simple for this assignment.

## 2. Organization Ownership

**Decision:** Determine organization ownership through the Location records imported from `locations.csv`.

**Alternative rejected:** Inferring organization ownership from location IDs or assigning ownership directly from record references.

**Reason:** The location mapping is the source of truth for organization ownership.

## 3. Cross-Organization Record Handling

**Decision:** When a System B entry references a System A record belonging to another organization, show the disagreement only to the organization that owns the System A record.

**Alternative rejected:** Showing the entry as an orphan to the organization owning the System B location.

**Reason:** This avoids exposing another organization's System B location details and prevents the same cross-organization reference from being incorrectly classified as an orphan.

## 4. Blank Values

**Decision:** Store blank numeric values as NULL rather than zero.

**Alternative rejected:** Treating blank values as zero.

**Reason:** A blank value means the source system did not provide a value. It should not be interpreted as an actual zero amount.

## 5. Record Reference Normalization

**Decision:** Normalize System B references into the `REC-XXXX` format while retaining the original reference in a separate raw-value field.

**Alternative rejected:** Comparing unnormalized references directly.

**Reason:** Different formatting styles can refer to the same record. Normalization makes comparison consistent while retaining the original input for reference.

## 6. Import Idempotency

**Decision:** Use Django's `update_or_create()` method with unique identifiers for imported records.

**Alternative rejected:** Blindly inserting every CSV row on each import.

**Reason:** Repeated imports should update existing records instead of creating duplicates.

## 7. Value Comparison

**Decision:** Compare System B's `value` against System A's `total_value`.

**Alternative rejected:** Comparing System B's value against System A's `base_value`.

**Reason:** The reconciliation requirement specifies that the total value is the corresponding comparison field.
