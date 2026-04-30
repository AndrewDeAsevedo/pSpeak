"""
Manually encrypting and decrypting with X25519 and XSalsa20.
I know I can just the python package PyNaCl and bundle most of this into like 2 calls but this project is for learning not
for efficiency (also this works just as well).
"""

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes


class Encryptor:
    def __init__(self, raw_shared_key, start_nonce):
        self.cipher = AESGCM(raw_shared_key)
        self.nonce = start_nonce

    def encrypt(self, data):
        nonce_bytes = self.nonce.to_bytes(12, "big")
        ciphertext = self.cipher.encrypt(nonce_bytes, data, None)
        self.nonce += 2

        return nonce_bytes + ciphertext

    def decrypt(self, data):
        nonce_bytes = data[:12]
        ciphertext = data[12:]
        return self.cipher.decrypt(nonce_bytes, ciphertext, None)


def createSharedKey(private_key_a, public_key_b):
    raw_shared_key = private_key_a.exchange(public_key_b)
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"pspeak-chat-key",
    ).derive(raw_shared_key)


class KeyGenerator:
    def __init__(self):
        self.private_key = X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()


# Dont forget to take out this main when you make the proper file
def main():
    gen = KeyGenerator()
    nonce1 = 1
    gen2 = KeyGenerator()
    nonce2 = 0

    sharedKey = createSharedKey(gen.private_key, gen2.public_key)

    enc1 = Encryptor(sharedKey, nonce1)
    enc2 = Encryptor(sharedKey, nonce2)

    encrypted_mssg = enc1.encrypt("Hi bro".encode())
    decrypted_mssg = enc2.decrypt(encrypted_mssg)
    print("Encrypted:", encrypted_mssg)
    print("Decrypted:", decrypted_mssg.decode())

    return


if __name__ == "__main__":
    main()
