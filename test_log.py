# test_log.py
# Tests the tamper-proof event log.
# Logs a series of simulated events, verifies chain integrity,
# then demonstrates that tampering is detected.

import sys
import os
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "logs"))
from event_log import init_db, log_event, verify_integrity, export_csv, DB_PATH

print("--- Ariadne Event Log Tests ---\n")

# Fresh database for testing
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

init_db()

# Log a series of realistic Ariadne events
log_event(
    event_type="SYSTEM_START",
    source="ariadne_core",
    detail="Ariadne navigation integrity system initialised",
    outcome="monitoring active"
)

log_event(
    event_type="GPS_ANOMALY",
    source="kalman_filter",
    detail="GPS residual exceeded threshold: 47.3km deviation from predicted position",
    outcome="GPS flagged as suspicious"
)

log_event(
    event_type="SENSOR_VOTE",
    source="voting_system",
    detail="IRS, TRN, and air data consensus disagrees with GPS by 51.2km",
    outcome="GPS excluded from navigation"
)

log_event(
    event_type="NAVIGATION_SWITCH",
    source="ariadne_core",
    detail="Switched primary navigation to TRN-corrected IRS",
    outcome="crew alerted, ATC notified"
)

log_event(
    event_type="ATC_REROUTE",
    source="atc_receiver",
    detail="Reroute message received: waypoint 51.5N 0.1W",
    outcome="signature valid, plausibility check passed, reroute applied"
)

print("\n--- Integrity Check (unmodified log) ---")
verify_integrity()

# Tamper with an entry directly in the database
print("\n--- Simulating tampering with event id=2 ---")
conn = sqlite3.connect(DB_PATH)
conn.execute("UPDATE events SET outcome='GPS accepted' WHERE id=2")
conn.commit()
conn.close()

print("\n--- Integrity Check (tampered log) ---")
verify_integrity()

# Export to CSV
print("\n--- CSV Export ---")
export_csv("ariadne_export.csv")