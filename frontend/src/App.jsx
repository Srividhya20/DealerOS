import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "https://dealeros-9alx.onrender.com/api/disagreements/";

function App() {
  const [org, setOrg] = useState("ORG-A");
  const [reason, setReason] = useState("");
  const [sort, setSort] = useState("value");

  const [allDisagreements, setAllDisagreements] = useState([]);
  const [disagreements, setDisagreements] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  const recordsPerPage = 5;

  // Fetch all records for summary cards
  useEffect(() => {
    const controller = new AbortController();

    const fetchAllDisagreements = async () => {
      setAllDisagreements([]);

      try {
        const params = new URLSearchParams({ org });

        const response = await fetch(`${API_URL}?${params.toString()}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Failed to fetch summary data");
        }

        const data = await response.json();
        setAllDisagreements(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          console.error("Summary fetch error:", err.message);
        }
      }
    };

    fetchAllDisagreements();

    return () => {
      controller.abort();
    };
  }, [org]);

  // Fetch filtered and sorted disagreements
  useEffect(() => {
    const controller = new AbortController();

    const fetchDisagreements = async () => {
      setLoading(true);
      setError("");
      setDisagreements([]);

      try {
        const params = new URLSearchParams({ org, sort });

        if (reason) {
          params.append("reason", reason);
        }

        const response = await fetch(
          `${API_URL}?${params.toString()}`,
          {
            signal: controller.signal,
          }
        );

        if (!response.ok) {
          throw new Error("Failed to fetch disagreements");
        }

        const data = await response.json();
        setDisagreements(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    };

    fetchDisagreements();

    return () => {
      controller.abort();
    };
  }, [org, reason, sort]);

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [org, reason, sort]);

  // Pagination calculations
  const totalPages = Math.ceil(
    disagreements.length / recordsPerPage
  );

  const startIndex = (currentPage - 1) * recordsPerPage;

  const currentRecords = disagreements.slice(
    startIndex,
    startIndex + recordsPerPage
  );

  // Toggle sorting
  const handleSort = () => {
    setSort((current) =>
      current === "value" ? "-value" : "value"
    );
  };

  // Summary statistics
  const countReason = (value) =>
    allDisagreements.filter(
      (item) => item.reason === value
    ).length;

  const summary = {
    total: allDisagreements.length,
    missing: countReason("MISSING_IN_B"),
    mismatches: countReason("VALUE_MISMATCH"),
    duplicates: countReason("DUPLICATE_IN_B"),
    orphan: countReason("ORPHAN_IN_B"),
    locationMismatch: countReason("LOCATION_MISMATCH"),
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div>
          <h1>DealerOS</h1>
          <p>System Reconciliation Dashboard</p>
        </div>

        <select
          value={org}
          onChange={(e) => setOrg(e.target.value)}
          aria-label="Select organization"
        >
          <option value="ORG-A">ORG-A</option>
          <option value="ORG-B">ORG-B</option>
        </select>
      </header>

      <main>
        <h2>Disagreements</h2>

        <p className="subtitle">
          Compare records between System A and System B.
        </p>

        {/* Summary Cards */}
        {!error && (
          <div className="summary-grid">
            <div className="summary-card orphan-card">
              <h3>Orphan in B</h3>
              <p>{summary.orphan}</p>
            </div>

            <div className="summary-card location-card">
              <h3>Location Mismatches</h3>
              <p>{summary.locationMismatch}</p>
            </div>

            <div className="summary-card total-card">
              <h3>Total Disagreements</h3>
              <p>{summary.total}</p>
            </div>

            <div className="summary-card missing-card">
              <h3>Missing in B</h3>
              <p>{summary.missing}</p>
            </div>

            <div className="summary-card mismatch-card">
              <h3>Value Mismatches</h3>
              <p>{summary.mismatches}</p>
            </div>

            <div className="summary-card duplicate-card">
              <h3>Duplicate Records</h3>
              <p>{summary.duplicates}</p>
            </div>
          </div>
        )}

        {/* Filter */}
        <div className="filters">
          <label htmlFor="reason">Filter by reason</label>

          <select
            id="reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          >
            <option value="">All reasons</option>
            <option value="MISSING_IN_B">Missing in B</option>
            <option value="ORPHAN_IN_B">Orphan in B</option>
            <option value="DUPLICATE_IN_B">Duplicate in B</option>
            <option value="VALUE_MISMATCH">Value mismatch</option>
            <option value="LOCATION_MISMATCH">
              Location mismatch
            </option>
            <option value="DATE_MISMATCH">Date mismatch</option>
            <option value="VOIDED_RECORD_IN_B">
              Voided record in B
            </option>
          </select>
        </div>

        {/* Loading and Error */}
        {loading && <p>Loading disagreements...</p>}

        {error && <p className="error">{error}</p>}

        {/* Table and Pagination */}
        {!loading && !error && (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Reason</th>
                    <th>Record ID</th>
                    <th>Location</th>
                    <th>System A Value</th>
                    <th>System B Value</th>
                    <th>
                      <button
                        className="sort-button"
                        onClick={handleSort}
                      >
                        Difference{" "}
                        {sort === "value" ? "↑" : "↓"}
                      </button>
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {currentRecords.length > 0 ? (
                    currentRecords.map((item, index) => (
                      <tr
                        key={`${item.record_id}-${item.reason}-${index}`}
                      >
                        <td>{item.reason}</td>
                        <td>{item.record_id}</td>
                        <td>{item.location || "—"}</td>
                        <td>{item.a_value ?? "—"}</td>
                        <td>
                          {item.b_value?.length
                            ? item.b_value
                                .map((value) => value ?? "—")
                                .join(", ")
                            : "—"}
                        </td>
                        <td>{item.difference ?? "—"}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6">
                        No disagreements found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="pagination">
                <button
                  onClick={() =>
                    setCurrentPage((prev) =>
                      Math.max(1, prev - 1)
                    )
                  }
                  disabled={currentPage === 1}
                >
                  Previous
                </button>

                <span>
                  Page {currentPage} of {totalPages}
                </span>

                <button
                  onClick={() =>
                    setCurrentPage((prev) =>
                      Math.min(totalPages, prev + 1)
                    )
                  }
                  disabled={currentPage === totalPages}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
