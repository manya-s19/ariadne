# atc_sender.py
# Simulates the ATC ground side.
# Signs reroute messages with the private key before sending.

import json
import base64
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def sign_reroute(waypoints: list, timestamp: str) -> dict:
    """
    Signs a reroute message with the ATC private key.

    Args:
        waypoints: list of dicts with 'lat' and 'lon' keys
        timestamp: ISO 8601 timestamp string

    Returns:
        dict with waypoints, timestamp, and base64-encoded signature
    """
    key_path = os.path.join(os.path.dirname(__file__), "atc_private.pem")
    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    message = json.dumps({"waypoints": waypoints, "timestamp": timestamp}).encode()
    signature = private_key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )

    return {
        "waypoints": waypoints,
        "timestamp": timestamp,
        "signature": base64.b64encode(signature).decode()
    }
