# Ariadne — ATC Reroute Authentication

## What this does
Simulates authenticated ATC reroute messages. Every reroute is:
1. **Signed** by ATC using a private key before sending
2. **Verified** by the aircraft using the corresponding public key
3. **Plausibility checked** — first waypoint must be within 500km of current position

## Folder structure
```
ariadne/
  atc/
    keygen.py           # run once to generate keys
    atc_sender.py       # ATC side: signs reroute messages
    aircraft_receiver.py # Aircraft side: verifies and validates
  test_atc.py           # runs all three test cases
  requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
cd atc
python keygen.py        # generates atc_private.pem and atc_public.pem
cd ..
python test_atc.py      # should print 3 outcomes
```

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
