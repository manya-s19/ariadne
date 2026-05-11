import numpy as np
import os
import math

DATA_DIR = "trn/EarthData"
tiles = {}

# SRTMGL1 resolution: 3601 x 3601 points per tile
SIZE = 3601

# Load .hgt file and return a 2D numpy array of elevations
def load_hgt(filename):
    data = np.fromfile(filename, dtype='>i2')
    return data.reshape((SIZE, SIZE))

# Converts latitude and longitude into the corresponding SRTM tile filename
def get_tile_filename(lat, lon):
    lat_base = math.floor(lat)
    lon_base = math.floor(lon)

    lat_dir = 'N' if lat_base >= 0 else 'S'
    lon_dir = 'E' if lon_base >= 0 else 'W'

    return (
        f"{lat_dir}{abs(lat_base):02d}"
        f"{lon_dir}{abs(lon_base):03d}.hgt"
    )

# Convert lat and lon to correspondingrow and column indices within the tile
def latlon_to_index(lat, lon):
    lat_base = math.floor(lat)
    lon_base = math.floor(lon)

    lat_frac = lat - lat_base
    lon_frac = lon - lon_base

    row = int((1 - lat_frac) * (SIZE - 1))
    col = int(lon_frac * (SIZE - 1))

    return row, col

# Returns terrain elevation in meters for the given latitude and longitude
# Note - Uses cached SRTM tiles for efficient lookup
def get_elevation(lat, lon):

    # Coordinate validation
    if not (-90 <= lat <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    if not (-180 <= lon <= 180):
        raise ValueError("Longitude must be between -180 and 180")
    
    tile_name = get_tile_filename(lat, lon)

    filename = os.path.join(DATA_DIR, tile_name)

    if not os.path.exists(filename):
        raise FileNotFoundError(f"Tile file {filename} not found in {DATA_DIR}.")

    if filename not in tiles:
        tiles[filename] = load_hgt(filename)

    data = tiles[filename]

    row, col = latlon_to_index(lat, lon)
    elevation = data[row, col]

    if elevation == -32768:  # Missing SRTM data
        return None
    
    return elevation

print(get_elevation(24.4667, 54.3667))  # Abu Dhabi coordinates
print(get_elevation(25.2769, 55.2962))  # Dubai coordinates
print(get_elevation(25.3374, 55.4121))  # Sharjah coordinates