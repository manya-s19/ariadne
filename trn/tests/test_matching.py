from terrain_matching import (
    sample_terrain_path,
    simulate_sensor_profile,
    compare_profiles,
    detect_terrain_anomaly
)

print("=== Terrain Matching Tests ===")

expected = sample_terrain_path(
    24.4667, 54.3667,
    25.1288, 56.3265,
    20
)

measured = simulate_sensor_profile(expected)

error = compare_profiles(expected, measured)

print("Matching Route Error:", error)
print(detect_terrain_anomaly(error))


# Simulated spoofing scenario
spoofed = sample_terrain_path(
    24.4667, 54.3667,
    24.6000, 54.5000,
    20
)

spoof_error = compare_profiles(expected, spoofed)

print("\nSpoofed Route Error:", spoof_error)
print(detect_terrain_anomaly(spoof_error))
