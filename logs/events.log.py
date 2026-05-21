# event_log.py
# Tamper-proof event log for Ariadne.
# Records every sensor classification and system response with a timestamp
# and a hash chain — each entry includes a hash of the previous entry,
# so any modification to the log is detectable.

import sqlite3
import hashlib
import json
import csv
import os
from datetime import datetime, timezone


DB_PATH = os.path.join(os.path.dirname(__file__), "ariadne_events.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates the events table if it doesn't exist.
    Call once at system startup.
    """
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                event_type  TEXT NOT NULL,
                source      TEXT NOT NULL,
                detail      TEXT NOT NULL,
                outcome     TEXT NOT NULL,
                prev_hash   TEXT NOT NULL,
                entry_hash  TEXT NOT NULL
            )
        """)
        conn.commit()


def _hash_entry(timestamp: str, event_type: str, source: str,
                detail: str, outcome: str, prev_hash: str) -> str:
    """
    SHA-256 hash of all fields in this entry plus the previous entry's hash.
    This creates a chain — modifying any entry breaks all subsequent hashes.
    """
    content = f"{timestamp}|{event_type}|{source}|{detail}|{outcome}|{prev_hash}"
    return hashlib.sha256(content.encode()).hexdigest()


def _get_last_hash() -> str:
    """
    Returns the hash of the most recent entry, or a fixed genesis string
    if the log is empty.
    """
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT entry_hash FROM events ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return row["entry_hash"] if row else "GENESIS"


def log_event(event_type: str, source: str, detail: str, outcome: str):
    """
    Appends a new event to the log.

    Args:
        event_type: category of event e.g. "GPS_SPOOFING", "ATC_REROUTE", "SENSOR_FAULT"
        source:     which system generated the event e.g. "kalman_filter", "voting_system"
        detail:     human-readable description of what was detected
        outcome:    what the system did e.g. "GPS excluded", "reroute accepted"
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    prev_hash = _get_last_hash()
    entry_hash = _hash_entry(timestamp, event_type, source, detail, outcome, prev_hash)

    with _get_connection() as conn:
        conn.execute("""
            INSERT INTO events (timestamp, event_type, source, detail, outcome, prev_hash, entry_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, event_type, source, detail, outcome, prev_hash, entry_hash))
        conn.commit()

    print(f"[LOG] {timestamp} | {event_type} | {source} | {outcome}")


def verify_integrity() -> bool:
    """
    Walks the entire log and recomputes each entry's hash.
    Returns True if the chain is intact, False if any entry has been modified.
    """
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY id ASC"
        ).fetchall()

    if not rows:
        print("Log is empty.")
        return True

    expected_prev = "GENESIS"
    for row in rows:
        expected_hash = _hash_entry(
            row["timestamp"], row["event_type"], row["source"],
            row["detail"], row["outcome"], expected_prev
        )
        if expected_hash != row["entry_hash"]:
            print(f"INTEGRITY FAILURE at event id={row['id']} — log has been tampered with.")
            return False
        expected_prev = row["entry_hash"]

    print(f"Integrity check passed — {len(rows)} events verified.")
    return True


def export_csv(output_path: str = "ariadne_export.csv"):
    """
    Exports the full event log to a CSV file for regulatory reporting.
    Does not include hash fields — those are for internal integrity only.
    """
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, event_type, source, detail, outcome FROM events ORDER BY id ASC"
        ).fetchall()

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "timestamp", "event_type", "source", "detail", "outcome"])
        for row in rows:
            writer.writerow([row["id"], row["timestamp"], row["event_type"],
                             row["source"], row["detail"], row["outcome"]])

    print(f"Exported {len(rows)} events to {output_path}")