"""
Manually encrypting and decrypting with X25519 and XSalsa20.
I know I can just the python package PyNaCl and bundle most of this into like 2 calls but this project is for learning not
for efficiency (also this works just as well).
"""

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
import os


def main():
    private_key = X25519PrivateKey.generate()
    public_key = private_key.publickey()
    public_key_bytes = public_key.private_bytes_raw()


def createSharedKey(private_key_A, public_key_B):
    raw_shared = private_key_A.exchange(public_key_B)
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"pspeak-chat-key",
    ).derive(raw_shared)

def encrypt():
    
    return

def decrypt():

    return


if __name__ =="__main__":
    main()