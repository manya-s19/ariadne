# keygen.py
# Run this ONCE to generate the ATC signing keys.
# atc_private.pem stays with the ATC sender (never share this).
# atc_public.pem goes on the aircraft receiver side.

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

with open("atc_private.pem", "wb") as f:
    f.write(private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    ))

with open("atc_public.pem", "wb") as f:
    f.write(private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    ))

print("Keys generated: atc_private.pem and atc_public.pem")
