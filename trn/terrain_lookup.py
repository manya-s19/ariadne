import numpy as np
import os
import math

# Absolute path to EarthData folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "EarthData")

tiles = {}

# SRTMGL1 resolution: 3601 x 3601 elevation points per tile
SIZE = 3601


def load_hgt(filename):
    """
    Load .hgt terrain file into NumPy array.
    """

    data = np.fromfile(filename, dtype='>i2')

    return data.reshape((SIZE, SIZE))


def get_tile_filename(lat, lon):
    """
    Convert coordinates into SRTM tile filename.
    """

    lat_base = math.floor(lat)
    lon_base = math.floor(lon)

    lat_dir = 'N' if lat_base >= 0 else 'S'
    lon_dir = 'E' if lon_base >= 0 else 'W'

    return (
        f"{lat_dir}{abs(lat_base):02d}"
        f"{lon_dir}{abs(lon_base):03d}.hgt"
    )


def latlon_to_index(lat, lon):
    """
    Convert latitude/longitude into row/column indices.
    """

    lat_base = math.floor(lat)
    lon_base = math.floor(lon)

    lat_frac = lat - lat_base
    lon_frac = lon - lon_base

    row = int((1 - lat_frac) * (SIZE - 1))
    col = int(lon_frac * (SIZE - 1))

    return row, col


def get_elevation(lat, lon):
    """
    Return terrain elevation in meters.
    """

    # Coordinate validation
    if not (-90 <= lat <= 90):
        raise ValueError("Latitude must be between -90 and 90")

    if not (-180 <= lon <= 180):
        raise ValueError("Longitude must be between -180 and 180")

    tile_name = get_tile_filename(lat, lon)

    filename = os.path.join(DATA_DIR, tile_name)

    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"Tile file '{tile_name}' not found in EarthData."
        )

    # Load tile into cache if not already loaded
    if filename not in tiles:
        tiles[filename] = load_hgt(filename)

    data = tiles[filename]

    row, col = latlon_to_index(lat, lon)

    elevation = data[row, col]

    # Missing SRTM data value
    if elevation == -32768:
        return None

    return elevation
