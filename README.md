# Ariadne

Ariadne protects aircraft from GPS spoofing by validating navigation data against independent sources before flight paths are affected. Throughout the flight, the software creates validation checkpoints ("breadcrumbs") along the planned route. At each checkpoint, terrain signatures and position estimates are compared against expected values to identify spoofing attempts and validate navigation integrity.

If GPS begins to diverge from the consensus of other sources, Ariadne gradually reduces trust in GPS. Persistent anomalies cause GPS to be removed entirely from the navigation solution, allowing the aircraft to continue using terrain-corrected inertial navigation.
Ariadne also protects against malicious reroute commands by cryptographically authenticating ATC messages before they are accepted.

## Key Features
- GPS Spoofing Detection using Kalman filtering and Mahalanobis distance anomaly detection
- Terrain Referenced Navigation (TRN) for independent position validation
- Adaptive Sensor Trust with dynamic sensor classification and weighting
- Breadcrumb Checkpoints for route-wide navigation validation
- Dead Reckoning Fallback when external navigation sources are unavailable
- Authenticated ATC Reroutes using digital signatures and plausibility checks
- Event Logging for anomaly tracking and post-flight analysis

## Folder structure
```
ariadne/
  dashboard/
    app.py
    kalman_filter.py  # kalman filter logic (sensor state cross-checking and voting)
    real_data.py
  logs/
    events.log.py
  trn/
    EarthData/          # hgt tiles of sample locations across Middle East
    terrain_lookup.py   # takes latitude, longitude and returns terrain elevation
    terrain_matching.py  # match terrain elevation to specific coordinates
  atc/
    keygen.py             # run once to generate keys
    atc_sender.py         # ATC side: signs reroute messages
    aircraft_receiver.py  # Aircraft side: verifies and validates
  requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
cd dashboard
python app.py

```
## ATC Reroute Authentication
Simulates authenticated ATC reroute messages. Every reroute is:
1. **Signed** by ATC using a private key before sending
2. **Verified** by the aircraft using the corresponding public key
3. **Plausibility checked** — first waypoint must be within 500km of current position

## Expected output
```
Test 1 (valid reroute):       ACCEPTED: reroute applied
Test 2 (tampered message):    REJECTED: invalid signature — message may have been tampered with
Test 3 (implausible route):   REJECTED: implausible route — first waypoint too far from current position
```

## Notes
- `atc_private.pem` should never be committed to GitHub — add it to `.gitignore`
- `atc_public.pem` is safe to share and commit
- The `max_jump_km` threshold in `plausibility_check()` can be tuned based on aircraft speed and reroute window

## Ariadne impact
Ariadne was designed around a simple idea: **Aircraft should not have to trust GPS blindly.**
By validating navigation information across multiple independent sources, Ariadne enables aircraft to continue operating safely even when GPS integrity is compromised.

Because the framework operates primarily at the navigation-logic level, it has the potential to be deployed as a software update rather than requiring widespread avionics hardware replacement.

Potential applications include:
- Commercial aviation
- Military and government aircraft
- Unmanned aerial vehicles (UAVs)
- Space launch and recovery systems

