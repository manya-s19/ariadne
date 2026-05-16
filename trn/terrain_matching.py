import numpy as np
from terrain_lookup import get_elevation

def get_checkPoints(start_lat, start_lon, end_lat, end_lon, num_samples):
    """
    Generate checkpoints along a path for terrain sampling.
    """

    latitudes = np.linspace(start_lat, end_lat, num_samples)
    longitudes = np.linspace(start_lon, end_lon, num_samples)

    return list(zip(latitudes, longitudes))

def sample_terrain_path(start_lat, start_lon,
                        end_lat, end_lon,
                        num_samples):
    """
    Sample terrain elevations along a path.
    """

    elevations = []
    checkpoints = get_checkPoints(start_lat, start_lon, end_lat, end_lon, num_samples)

    for lat, lon in zip(latitudes, longitudes):

        try:
            elevation = get_elevation(lat, lon)

        except FileNotFoundError:
            elevation = None

        elevations.append(elevation)

    return elevations


def simulate_sensor_profile(expected_profile, noise_std=5):
    """
    Simulate radar/LiDAR terrain measurements.
    """

    measured_profile = []

    for elevation in expected_profile:

        if elevation is None:
            measured_profile.append(None)

        else:
            noisy_value = elevation + np.random.normal(0, noise_std)

            measured_profile.append(noisy_value)

    return measured_profile

def compare_profiles(expected_profile, measured_profile):
    """
    Compare terrain profiles using mean absolute error.

    Returns:
        float error if comparison possible
        None if insufficient terrain data
    """

    if len(expected_profile) != len(measured_profile):
        raise ValueError("Profiles must have same length")

    differences = []

    for expected, measured in zip(expected_profile,
                                  measured_profile):

        if expected is None or measured is None:
            continue

        differences.append(abs(expected - measured))

    # No valid terrain comparisons possible
    if len(differences) == 0:
        return None

    return np.mean(differences)

def detect_terrain_anomaly(error, threshold=50):
    """
    Determine TRN status based on terrain comparison.
    """

    if error is None:
        return "Terrain data unavailable for this route."

    if error > threshold:
        return "WARNING: Terrain profile does not match expected route."

    return "Terrain profile matches expected route."
