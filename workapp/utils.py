from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

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