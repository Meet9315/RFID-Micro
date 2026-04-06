"""
Shared cryptographic utility functions for AES and DES encryption/decryption.
Used by both Streamlit dashboards and CLI scripts.

Encryption: AES-128-ECB and DES-ECB (with optional CBC mode support)
Encoding: Base64 for Firebase-safe storage
"""

import base64
import time
from Crypto.Cipher import AES, DES
from Crypto.Random import get_random_bytes

from config import AES_KEY_SIZE, DES_KEY_SIZE, AES_BLOCK_SIZE, DES_BLOCK_SIZE


# -------------------
# Padding (PKCS#7)
# -------------------
def pad(data: str, block_size: int) -> str:
    """PKCS#7 padding to make data a multiple of block_size."""
    padding_len = block_size - len(data) % block_size
    return data + chr(padding_len) * padding_len


def unpad(data: str) -> str:
    """Remove PKCS#7 padding."""
    padding_len = ord(data[-1])
    return data[:-padding_len]


# -------------------
# AES Encryption / Decryption
# -------------------
def aes_encrypt(plaintext: str, key: bytes = None) -> tuple:
    """
    Encrypt plaintext using AES-128-ECB.
    Returns (base64_ciphertext, key, encryption_time_ms).
    """
    if key is None:
        key = get_random_bytes(AES_KEY_SIZE)

    cipher = AES.new(key, AES.MODE_ECB)
    start = time.perf_counter()
    ciphertext = cipher.encrypt(pad(plaintext, AES_BLOCK_SIZE).encode())
    enc_time = (time.perf_counter() - start) * 1000

    b64 = base64.b64encode(ciphertext).decode()
    return b64, key, enc_time


def aes_decrypt(b64_ciphertext: str, key: bytes) -> tuple:
    """
    Decrypt base64-encoded AES-128-ECB ciphertext.
    Returns (plaintext, decryption_time_ms).
    """
    ciphertext = base64.b64decode(b64_ciphertext)
    decipher = AES.new(key, AES.MODE_ECB)
    start = time.perf_counter()
    decrypted = unpad(decipher.decrypt(ciphertext).decode())
    dec_time = (time.perf_counter() - start) * 1000
    return decrypted, dec_time


def aes_encrypt_decrypt(plaintext: str, key: bytes = None) -> tuple:
    """
    Full AES encrypt + decrypt cycle.
    Returns (base64_ciphertext, decrypted_text, enc_time_ms, dec_time_ms).
    """
    b64, key, enc_time = aes_encrypt(plaintext, key)
    decrypted, dec_time = aes_decrypt(b64, key)
    return b64, decrypted, enc_time, dec_time


# -------------------
# DES Encryption / Decryption
# -------------------
def des_encrypt(plaintext: str, key: bytes = None) -> tuple:
    """
    Encrypt plaintext using DES-ECB.
    Returns (base64_ciphertext, key, encryption_time_ms).
    """
    if key is None:
        key = get_random_bytes(DES_KEY_SIZE)

    cipher = DES.new(key, DES.MODE_ECB)
    start = time.perf_counter()
    ciphertext = cipher.encrypt(pad(plaintext, DES_BLOCK_SIZE).encode())
    enc_time = (time.perf_counter() - start) * 1000

    b64 = base64.b64encode(ciphertext).decode()
    return b64, key, enc_time


def des_decrypt(b64_ciphertext: str, key: bytes) -> tuple:
    """
    Decrypt base64-encoded DES-ECB ciphertext.
    Returns (plaintext, decryption_time_ms).
    """
    ciphertext = base64.b64decode(b64_ciphertext)
    decipher = DES.new(key, DES.MODE_ECB)
    start = time.perf_counter()
    decrypted = unpad(decipher.decrypt(ciphertext).decode())
    dec_time = (time.perf_counter() - start) * 1000
    return decrypted, dec_time


def des_encrypt_decrypt(plaintext: str, key: bytes = None) -> tuple:
    """
    Full DES encrypt + decrypt cycle.
    Returns (base64_ciphertext, decrypted_text, enc_time_ms, dec_time_ms).
    """
    b64, key, enc_time = des_encrypt(plaintext, key)
    decrypted, dec_time = des_decrypt(b64, key)
    return b64, decrypted, enc_time, dec_time


# -------------------
# AES-CBC Encryption / Decryption
# -------------------
def aes_cbc_encrypt_decrypt(plaintext: str, key: bytes = None) -> tuple:
    """
    Full AES-128-CBC encrypt + decrypt cycle with random IV.
    Returns (base64_ciphertext, decrypted_text, enc_time_ms, dec_time_ms, iv_hex).
    """
    if key is None:
        key = get_random_bytes(AES_KEY_SIZE)
    iv = get_random_bytes(AES_BLOCK_SIZE)

    # Encrypt
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    start = time.perf_counter()
    ciphertext = cipher.encrypt(pad(plaintext, AES_BLOCK_SIZE).encode())
    enc_time = (time.perf_counter() - start) * 1000

    b64 = base64.b64encode(ciphertext).decode()

    # Decrypt
    decipher = AES.new(key, AES.MODE_CBC, iv=iv)
    start = time.perf_counter()
    decrypted = unpad(decipher.decrypt(ciphertext).decode())
    dec_time = (time.perf_counter() - start) * 1000

    iv_hex = iv.hex()
    return b64, decrypted, enc_time, dec_time, iv_hex


def des_cbc_encrypt_decrypt(plaintext: str, key: bytes = None) -> tuple:
    """
    Full DES-CBC encrypt + decrypt cycle with random IV.
    Returns (base64_ciphertext, decrypted_text, enc_time_ms, dec_time_ms, iv_hex).
    """
    if key is None:
        key = get_random_bytes(DES_KEY_SIZE)
    iv = get_random_bytes(DES_BLOCK_SIZE)

    # Encrypt
    cipher = DES.new(key, DES.MODE_CBC, iv=iv)
    start = time.perf_counter()
    ciphertext = cipher.encrypt(pad(plaintext, DES_BLOCK_SIZE).encode())
    enc_time = (time.perf_counter() - start) * 1000

    b64 = base64.b64encode(ciphertext).decode()

    # Decrypt
    decipher = DES.new(key, DES.MODE_CBC, iv=iv)
    start = time.perf_counter()
    decrypted = unpad(decipher.decrypt(ciphertext).decode())
    dec_time = (time.perf_counter() - start) * 1000

    iv_hex = iv.hex()
    return b64, decrypted, enc_time, dec_time, iv_hex


# -------------------
# ECB vs CBC Demonstration (Penguin Problem)
# -------------------
def ecb_vs_cbc_demo(plaintext: str) -> dict:
    """
    Encrypt the SAME plaintext with ECB and CBC to show the difference.
    ECB produces identical ciphertext blocks for identical plaintext blocks.
    CBC produces different ciphertext each time due to IV randomization.
    Returns dict with results from multiple ECB and CBC runs.
    """
    key = get_random_bytes(AES_KEY_SIZE)

    # ECB: same key, same plaintext → SAME ciphertext every time
    ecb_results = []
    for _ in range(3):
        cipher = AES.new(key, AES.MODE_ECB)
        ct = cipher.encrypt(pad(plaintext, AES_BLOCK_SIZE).encode())
        ecb_results.append(base64.b64encode(ct).decode())

    # CBC: same key, same plaintext → DIFFERENT ciphertext each time (random IV)
    cbc_results = []
    for _ in range(3):
        iv = get_random_bytes(AES_BLOCK_SIZE)
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        ct = cipher.encrypt(pad(plaintext, AES_BLOCK_SIZE).encode())
        cbc_results.append(base64.b64encode(ct).decode())

    return {
        "ecb_results": ecb_results,
        "cbc_results": cbc_results,
        "ecb_all_same": len(set(ecb_results)) == 1,
        "cbc_all_different": len(set(cbc_results)) == len(cbc_results),
    }


# -------------------
# Hashing: SHA-256 vs MD5
# -------------------
import hashlib

def hash_sha256(data: str) -> tuple:
    """Hash using SHA-256. Returns (hex_digest, time_ms)."""
    start = time.perf_counter()
    digest = hashlib.sha256(data.encode()).hexdigest()
    hash_time = (time.perf_counter() - start) * 1000
    return digest, hash_time


def hash_md5(data: str) -> tuple:
    """Hash using MD5. Returns (hex_digest, time_ms)."""
    start = time.perf_counter()
    digest = hashlib.md5(data.encode()).hexdigest()
    hash_time = (time.perf_counter() - start) * 1000
    return digest, hash_time


# -------------------
# Firebase-Ready Encryption (for portfolio storage)
# -------------------
def encrypt_portfolio_for_firebase(plaintext: str, aes_key: bytes) -> str:
    """
    Encrypt portfolio text with a FIXED AES key (shared with ESP32).
    Returns base64-encoded ciphertext ready for Firebase storage.
    The SAME key must be used on the ESP32 side for decryption.
    """
    b64, _, _ = aes_encrypt(plaintext, key=aes_key)
    return b64


def decrypt_portfolio_from_firebase(b64_ciphertext: str, aes_key: bytes) -> str:
    """
    Decrypt portfolio text fetched from Firebase using the shared AES key.
    """
    plaintext, _ = aes_decrypt(b64_ciphertext, key=aes_key)
    return plaintext
