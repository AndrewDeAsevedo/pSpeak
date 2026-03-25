"""
EXAMPLE: Demonstrates the full encryption flow for a P2P chat.

This shows how two peers (Alice and Bob) can:
  1. Generate their own keypairs
  2. Exchange public keys
  3. Derive the SAME shared secret independently
  4. Encrypt/decrypt messages with that shared secret

This is NOT the pSpeak crypto module. It's a learning reference.

What YOUR crypto.py needs to do differently:
  - Wrap these into clean functions: generate_keypair(), derive_shared_secret(),
    encrypt(), decrypt()
  - Handle nonce counting (this example uses random nonces for simplicity;
    yours should use incrementing counters)
  - Return the public key as bytes so it can be sent over the signaling server
  - Raise clear errors when decryption fails (tampered message)

Run: pip install cryptography
Then: python example_crypto.py
"""

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
import os


# ============================================================
# STEP 1: Key Generation
# Each side generates a keypair. The private key stays secret.
# The public key gets sent to the other person.
# ============================================================

# Alice generates her keypair
alice_private = X25519PrivateKey.generate()
alice_public = alice_private.public_key()

# Bob generates his keypair
bob_private = X25519PrivateKey.generate()
bob_public = bob_private.public_key()

# To send a public key over the network, you need it as raw bytes.
# This is what you'd include in the signaling server payload.
alice_public_bytes = alice_public.public_bytes_raw()
bob_public_bytes = bob_public.public_bytes_raw()

print(f"Alice's public key (32 bytes): {alice_public_bytes.hex()}")
print(f"Bob's public key   (32 bytes): {bob_public_bytes.hex()}")
print()


# ============================================================
# STEP 2: Key Exchange (Diffie-Hellman)
# Each side combines their private key with the other's public key.
# The math guarantees both get the same result.
# ============================================================

# Alice computes: her private key + Bob's public key
alice_raw_shared = alice_private.exchange(bob_public)

# Bob computes: his private key + Alice's public key
bob_raw_shared = bob_private.exchange(alice_public)

# These are identical! That's the magic of Diffie-Hellman.
print(f"Alice's raw shared secret: {alice_raw_shared.hex()}")
print(f"Bob's raw shared secret:   {bob_raw_shared.hex()}")
print(f"Shared secrets match: {alice_raw_shared == bob_raw_shared}")
print()


# ============================================================
# STEP 3: Key Derivation (HKDF)
# The raw shared secret works, but best practice is to run it
# through a key derivation function. This "stretches" and
# standardizes the key material.
#
# Think of it as refining raw metal into a precise tool.
# ============================================================

def derive_key(raw_shared_secret: bytes) -> bytes:
    """Derive a 32-byte AES key from the raw shared secret."""
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"pspeak-chat-key",  # A label unique to your app
    ).derive(raw_shared_secret)

alice_key = derive_key(alice_raw_shared)
bob_key = derive_key(bob_raw_shared)

print(f"Alice's AES key: {alice_key.hex()}")
print(f"Bob's AES key:   {bob_key.hex()}")
print(f"AES keys match:  {alice_key == bob_key}")
print()


# ============================================================
# STEP 4: Encrypt a message
# Now both sides have the same 32-byte key. They can use it
# with AES-256-GCM to encrypt and decrypt messages.
#
# Each message needs a UNIQUE nonce (12 bytes). In this example
# we use random nonces. YOUR version should use incrementing
# counters instead — simpler and guaranteed unique.
# ============================================================

# Alice wants to send "Hello Bob!" to Bob.
message = b"Hello Bob!"

# Create an AES-GCM cipher using the shared key
alice_cipher = AESGCM(alice_key)

# Generate a nonce. In YOUR code, this should be a counter (0, 1, 2, ...)
# converted to 12 bytes, not random.
nonce = os.urandom(12)

# Encrypt. The output contains the ciphertext + a 16-byte authentication tag.
ciphertext = alice_cipher.encrypt(nonce, message, None)

print(f"Original message:  {message}")
print(f"Nonce:             {nonce.hex()}")
print(f"Encrypted:         {ciphertext.hex()}")
print(f"Encrypted length:  {len(ciphertext)} bytes (message + 16-byte auth tag)")
print()


# ============================================================
# STEP 5: Decrypt the message
# Bob receives the ciphertext + nonce. He uses the same key
# (which he derived independently) to decrypt it.
# ============================================================

bob_cipher = AESGCM(bob_key)

# Bob decrypts using the same nonce that Alice used.
# In practice, Alice sends the nonce alongside the ciphertext.
decrypted = bob_cipher.decrypt(nonce, ciphertext, None)

print(f"Bob decrypted:     {decrypted}")
print(f"Matches original:  {decrypted == message}")
print()


# ============================================================
# STEP 6: Tamper detection
# What if someone modifies the ciphertext in transit?
# AES-GCM catches it and raises an exception.
# ============================================================

tampered = bytearray(ciphertext)
tampered[0] ^= 0xFF  # Flip some bits

try:
    bob_cipher.decrypt(nonce, bytes(tampered), None)
    print("ERROR: Tampered message was accepted (this should never happen)")
except Exception as e:
    print(f"Tampered message rejected: {e}")
    print("AES-GCM caught the modification — integrity protected.")
