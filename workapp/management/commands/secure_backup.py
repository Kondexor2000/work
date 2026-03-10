import os
import json
from django.core.management.base import BaseCommand
from django.core.management import call_command

from pqcrypto.kem.ml_kem_512 import generate_keypair, encrypt

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes, hmac
from cryptography.hazmat.backends import default_backend


class Command(BaseCommand):
    help = "Secure encrypted database backup using AES + ML-KEM"

    def handle(self, *args, **kwargs):

        # =========================================
        # 1️⃣ Tworzenie dumpa bazy
        # =========================================
        dump_file = "backup.json"

        with open(dump_file, "w") as f:
            call_command("dumpdata", stdout=f)

        with open(dump_file, "rb") as f:
            data = f.read()

        os.remove(dump_file)

        # =========================================
        # 2️⃣ ML-KEM (Post-Quantum Key Exchange)
        # =========================================
        public_key, secret_key = generate_keypair()
        kem_ciphertext, shared_secret = encrypt(public_key)

        # Klucz AES-256
        aes_key = shared_secret[:32]

        # =========================================
        # 3️⃣ AES-256-CBC szyfrowanie
        # =========================================
        iv = os.urandom(16)

        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()

        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # =========================================
        # 4️⃣ HMAC (integralność)
        # =========================================
        h = hmac.HMAC(aes_key, hashes.SHA256())
        h.update(ciphertext)
        mac = h.finalize()

        # =========================================
        # 5️⃣ Zapis backupu
        # =========================================
        with open("backup.enc", "wb") as f:
            f.write(iv + ciphertext)

        meta = {
            "kem_ciphertext": kem_ciphertext.hex(),
            "hmac": mac.hex()
        }

        with open("backup_meta.json", "w") as f:
            json.dump(meta, f)

        self.stdout.write(
            self.style.SUCCESS("Secure backup created successfully.")
        )