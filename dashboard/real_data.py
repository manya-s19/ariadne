# real_data.py
#
# PURPOSE: Bridges Kalman filter + TRN to the dashboard frame format.
#          Also provides per-scenario narrative text explaining what Ariadne is doing.

from dashboard.kalman_filter import run_full_simulation

# ---------------------------------------------------------------------------
# FLIGHT PATH DEFINITIONS
# ---------------------------------------------------------------------------
# Three real UAE routes, each paired with a different GPS attack type.
# The terrain type influences TRN confidence and justifies the attack choice.

FLIGHT_PATHS = {
    "abu_dhabi_fujairah": {
        "label":      "Abu Dhabi → Fujairah",
        "terrain":    "Mountain",
        "start_lat":  24.4667, "start_lon": 54.3667,
        "end_lat":    25.1221, "end_lon":   56.3345,
        "spoof_type": "gradual",
        # Hajar Mountains give TRN a strong elevation signature.
        # Gradual drift is the hardest attack to notice without cross-checking —
        # it mimics the 2023 Eastern Mediterranean incidents exactly.
        "narrative": {
            "route":   "Mountain crossing via the Hajar range — rich terrain for TRN.",
            "attack":  "GRADUAL DRIFT: GPS offset grows slowly. Hard to detect without sensor fusion.",
            "defense": "Kalman filter catches the growing gap between GPS and IRS prediction. "
                       "TRN confirms true position using mountain elevation profile.",
        },
    },
    "dubai_ras_al_khaimah": {
        "label":      "Dubai → Ras Al Khaimah",
        "terrain":    "Coastal",
        "start_lat":  25.2532, "start_lon": 55.3657,
        "end_lat":    25.7953, "end_lon":   55.9432,
        "spoof_type": "sudden",
        # Coastal / flat terrain → TRN less reliable.
        # Sudden jump is immediately visible in the Mahalanobis spike.
        "narrative": {
            "route":   "Short coastal hop — flat terrain limits TRN confidence.",
            "attack":  "SUDDEN JUMP: GPS snaps to a false position in one timestep.",
            "defense": "Mahalanobis distance spikes instantly above 5σ. "
                       "GPS is ELIMINATED in one step. IRS holds position until TRN confirms.",
        },
    },
    "abu_dhabi_al_ain": {
        "label":      "Abu Dhabi → Al Ain",
        "terrain":    "Desert",
        "start_lat":  24.4667, "start_lon": 54.3667,
        "end_lat":    24.2075, "end_lon":   55.7447,
        "spoof_type": "combined",
        # Desert = featureless terrain, low TRN confidence.
        # Combined attack tests the worst-case: GPS spoofed + IRS degraded simultaneously.
        "narrative": {
            "route":   "Desert crossing — featureless terrain, lowest TRN confidence.",
            "attack":  "COMBINED: GPS spoofed AND IRS sensor degraded simultaneously.",
            "defense": "Both primary sensors compromised. Dead reckoning activates — "
                       "aircraft navigates on last known good state until a fix is possible.",
        },
    },
}


# ---------------------------------------------------------------------------
# THREAT LEVEL HELPER
# ---------------------------------------------------------------------------
def _threat(gps_state: str, trn_state: str, mahal: float) -> str:
    if gps_state == "ELIMINATED" and trn_state == "ELIMINATED":
        return "CRITICAL"
    elif gps_state == "ELIMINATED":
        return "HIGH"
    elif gps_state == "FLAGGED":
        return "MEDIUM"
    else:
        return "LOW"


# ---------------------------------------------------------------------------
# MAIN: RUN A FLIGHT PATH SIMULATION
# ---------------------------------------------------------------------------
def run_flight_path(path_key: str, seconds: int = 60) -> list[dict]:
    """
    Runs the full Kalman + TRN simulation for the given flight path.
    Returns a list of frame dicts, one per timestep.

    Data key            Dashboard key       Notes
    ─────────────────── ─────────────────── ──────────────────────────────────
    Real Position         true_position       ground truth (kinematics)
    GPS Position          gps_position        raw spoofed GPS reading
    IRS Position          irs_position        physics-only dead reckoning
    TRN Position          trn_position        terrain-matched fix (normalised)
    Updated Position      kalman_estimate     fused best estimate
    Mahanalobis           residual            normalised anomaly score (σ)
    GPS State             gps_state           IN_KF / FLAGGED / ELIMINATED
    TRN State             trn_state           STANDBY / IN_KF / ELIMINATED
    """
    if path_key not in FLIGHT_PATHS:
        raise ValueError(f"Unknown path '{path_key}'. Choose from: {list(FLIGHT_PATHS)}")

    cfg = FLIGHT_PATHS[path_key]

    raw = run_full_simulation(
        start_lat=cfg["start_lat"],
        start_lon=cfg["start_lon"],
        end_lat=cfg["end_lat"],
        end_lon=cfg["end_lon"],
        spoof_type=cfg["spoof_type"],
        seconds=seconds,
    )

    # ------------------------------------------------------------------
    # NORMALISE TRN TO THE SAME SCALE AS GPS / IRS
    # ------------------------------------------------------------------
    # TRN returns position in "terrain_index × distance_per_step"
    # units, which can be very different from the metre-scale GPS/IRS values.
    # We rescale TRN to match the true_position range so all sensors plot
    # on the same axis.
    true_max = max(d["Real Position"] for d in raw) or 1.0
    trn_raw_max = max(abs(d["TRN Position"]) for d in raw) or 1.0
    trn_scale = true_max / trn_raw_max

    frames = []
    for i, d in enumerate(raw):
        gps_trusted = d["GPS State"] == "IN_KF"
        mahal       = d["Mahalanobis"]

        frames.append({
            "t":                     i,
            "true_position":         d["Real Position"],
            "naive_position":        d["GPS Position"],
            "gps_position":          d["GPS Position"],
            "irs_position":          d["IRS Position"],
            "trn_position":          d["TRN Position"] * trn_scale,  # normalised
            "kalman_estimate":       d["Updated Position"],
            "residual":              mahal,
            "gps_trusted":           gps_trusted,
            "gps_state":             d["GPS State"],
            "trn_state":             d["TRN State"],
            "threat_level":          _threat(d["GPS State"], d["TRN State"], mahal),
            "dead_reckoning_active": (
                d["GPS State"] == "ELIMINATED" and d["TRN State"] == "ELIMINATED"
            ),
            "flight_path":           path_key,
            "terrain":               cfg["terrain"],
            "spoof_type":            cfg["spoof_type"],
            "narrative":             cfg["narrative"],
        })

    return frames
