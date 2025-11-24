"""
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_OAEP, AES
from Cryptodome.Util.Padding import pad, unpad
from oqs import KEM

def generate_rsa_keys():
    key = RSA.generate(2048)
    private_key = key
    public_key = key.publickey()
    return public_key, private_key

public_key, private_key = generate_rsa_keys()

# RSA encryption for AES key
def rsa_encrypt(public_key, aes_key):
    cipher = PKCS1_OAEP.new(public_key)
    encrypted_aes_key = cipher.encrypt(aes_key)  # Encrypt the AES key with RSA
    return encrypted_aes_key

# ===== POSTKWANTOWA WARSTWA: Kyber768 =====

def pq_generate_keys():
    kem = oqs.KEM("Kyber768")
    public_key = kem.generate_keypair()
    private_key = kem.export_secret_key()
    return public_key, private_key

# W praktyce klucze PQC powinny być zapisane w bezpiecznym miejscu (np. w bazie lub w HSM)
PQ_PUBLIC_KEY, PQ_PRIVATE_KEY = pq_generate_keys()

def pq_encrypt(data: bytes) -> dict:
    Szyfruje dane:
    - generuje losowy klucz AES
    - szyfruje dane AES-em
    - klucz AES kapsułkuje postkwantowo (Kyber768)
    # Kapsułkowanie PQC
    kem = oqs.KEM("Kyber768")
    shared_secret = kem.encap_secret(PQ_PUBLIC_KEY)

    # AES szyfrowanie danych
    aes_cipher = AES.new(shared_secret[:32], AES.MODE_CBC)
    ct_bytes = aes_cipher.encrypt(pad(data, AES.block_size))

    return ct_bytes.hex()
"""