# aircraft_receiver.py
# Simulates the aircraft side.
# Verifies the ATC signature and checks the reroute is physically plausible.

import json
import base64
import math
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature


def verify_signature(message: dict) -> bool:
    """
    Verifies the digital signature on an incoming ATC reroute message.
    Returns True if the signature is valid, False if tampered or invalid.
    """
    key_path = os.path.join(os.path.dirname(__file__), "atc_public.pem")
    with open(key_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    payload = json.dumps({
        "waypoints": message["waypoints"],
        "timestamp": message["timestamp"]
    }).encode()
    signature = base64.b64decode(message["signature"])

    try:
        public_key.verify(
            signature,
            payload,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance in km between two lat/lon points.
    """
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def plausibility_check(current_pos: dict, waypoints: list, max_jump_km: float = 500) -> bool:
    """
    Checks that the first waypoint in the reroute is within a plausible
    distance of the aircraft's current position.

    Args:
        current_pos: dict with 'lat' and 'lon' keys
        waypoints: list of waypoint dicts from the reroute message
        max_jump_km: maximum allowed distance in km (default 500)

    Returns:
        True if plausible, False if the route is geometrically impossible
    """
    first_wp = waypoints[0]
    distance = haversine(
        current_pos["lat"], current_pos["lon"],
        first_wp["lat"], first_wp["lon"]
    )
    return distance <= max_jump_km


def process_reroute(message: dict, current_pos: dict) -> str:
    """
    Full reroute validation pipeline.
    Runs signature check first, then plausibility check.

    Returns a status string describing the outcome.
    """
    if not verify_signature(message):
        return "REJECTED: invalid signature — message may have been tampered with"

    if not plausibility_check(current_pos, message["waypoints"]):
        return "REJECTED: implausible route — first waypoint too far from current position"

    return "ACCEPTED: reroute applied"
