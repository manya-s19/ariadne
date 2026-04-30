# test_atc.py
# Run this to verify the full ATC authentication pipeline.
# Should print three outcomes: accepted, rejected (tampered), rejected (implausible).
#
# Before running, make sure you have generated keys first:
#   python atc/keygen.py

import sys
import os

# Allow imports from the atc/ folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "atc"))

from atc_sender import sign_reroute
from aircraft_receiver import process_reroute

# Simulate aircraft currently over southern England
current_position = {"lat": 51.0, "lon": -1.0}

print("--- ATC Reroute Authentication Tests ---\n")

# Test 1: valid reroute to nearby waypoint
msg = sign_reroute(
    waypoints=[{"lat": 51.5, "lon": -0.1}],
    timestamp="2024-03-01T12:00:00Z"
)
print(f"Test 1 (valid reroute):       {process_reroute(msg, current_position)}")

# Test 2: tampered message — change waypoints after signing
tampered_msg = sign_reroute(
    waypoints=[{"lat": 51.5, "lon": -0.1}],
    timestamp="2024-03-01T12:00:00Z"
)
tampered_msg["waypoints"] = [{"lat": 35.0, "lon": 139.0}]  # swapped to Tokyo after signing
print(f"Test 2 (tampered message):    {process_reroute(tampered_msg, current_position)}")

# Test 3: valid signature but implausible route (Tokyo from southern England)
far_msg = sign_reroute(
    waypoints=[{"lat": 35.0, "lon": 139.0}],
    timestamp="2024-03-01T12:00:00Z"
)
print(f"Test 3 (implausible route):   {process_reroute(far_msg, current_position)}")
