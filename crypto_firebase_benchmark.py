from Crypto.Cipher import AES, DES
from Crypto.Random import get_random_bytes
import base64
import requests
import time

# -------------------
# CONFIG
# -------------------
FIREBASE_URL = "https://pocs-project-68633-default-rtdb.asia-southeast1.firebasedatabase.app"
USER_ID = "UID12345"  # you can change this to another test user
PORTFOLIO = "BTC=0.25, ETH=1.5" * 5000  # large string for benchmark


# -------------------
# Helpers
# -------------------
def pad(data, block_size):
    padding_len = block_size - len(data) % block_size
    return data + chr(padding_len) * padding_len


def unpad(data):
    padding_len = ord(data[-1])
    return data[:-padding_len]


def aes_encrypt_decrypt(plaintext, key=None):
    if key is None:
        key = get_random_bytes(16)  # 128-bit AES key
    cipher = AES.new(key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(plaintext, 16).encode())
    b64 = base64.b64encode(ciphertext).decode()

    decipher = AES.new(key, AES.MODE_ECB)
    decrypted = unpad(decipher.decrypt(ciphertext).decode())
    return b64, decrypted


def des_encrypt_decrypt(plaintext, key=None):
    if key is None:
        key = get_random_bytes(8)  # 64-bit DES key
    cipher = DES.new(key, DES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(plaintext, 8).encode())
    b64 = base64.b64encode(ciphertext).decode()

    decipher = DES.new(key, DES.MODE_ECB)
    decrypted = unpad(decipher.decrypt(ciphertext).decode())
    return b64, decrypted


# -------------------
# MAIN
# -------------------
if __name__ == "__main__":
    print("Plaintext portfolio:", PORTFOLIO[:50] + "...")  # preview only

    # Fixed keys for consistent comparison
    aes_key = b"1234567890abcdef"  # 16 bytes = 128-bit AES key
    des_key = b"8bytekey"          # 8 bytes = 64-bit DES key

    # AES benchmark
    start = time.time()
    for _ in range(1000):
        aes_ct, aes_pt = aes_encrypt_decrypt(PORTFOLIO, key=aes_key)
    end = time.time()
    aes_time = (end - start) * 1000  # ms
    print(f"\nAES (1000 runs): {aes_time:.2f} ms")
    print("AES sample ciphertext:", aes_ct[:100] + "...")
    print("AES final decrypted:", aes_pt[:50] + "...")

    # DES benchmark
    start = time.time()
    for _ in range(1000):
        des_ct, des_pt = des_encrypt_decrypt(PORTFOLIO, key=des_key)
    end = time.time()
    des_time = (end - start) * 1000  # ms
    print(f"\nDES (1000 runs): {des_time:.2f} ms")
    print("DES sample ciphertext:", des_ct[:100] + "...")
    print("DES final decrypted:", des_pt[:50] + "...")

    # Push only truncated ciphertext to Firebase
    data = {
        "portfolio_AES": aes_ct[:100] + "...",  # 👈 safely truncated
        "portfolio_DES": des_ct[:100] + "...",  # 👈 safely truncated
        "benchmark": {
            "AES_ms": round(aes_time, 2),
            "DES_ms": round(des_time, 2)
        }
    }

    r = requests.put(f"{FIREBASE_URL}/users/{USER_ID}.json", json=data)
    print("\nWrite status:", r.status_code)

    # Read back from Firebase
    r = requests.get(f"{FIREBASE_URL}/users/{USER_ID}.json")
    print("Data read from Firebase:", r.json())
