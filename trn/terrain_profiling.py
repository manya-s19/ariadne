import numpy as np
from terrain_lookup import get_elevation


def sample_terrain_path(start_lat, start_lon,
                        end_lat, end_lon,
                        num_samples):
    """
    Generate terrain checkpoints along a path.
    """

    checkpoints = []

    latitudes = np.linspace(start_lat, end_lat, num_samples)
    longitudes = np.linspace(start_lon, end_lon, num_samples)

    for lat, lon in zip(latitudes, longitudes):

        try:
            elevation = get_elevation(lat, lon)

        except FileNotFoundError:
            elevation = None

        checkpoints.append({
            "latitude": lat,
            "longitude": lon,
            "elevation": elevation
        })

    return checkpoints