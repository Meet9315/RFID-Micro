from Crypto.Cipher import AES, DES
from Crypto.Random import get_random_bytes
import base64
import requests

# -------------------
# CONFIG
# -------------------
FIREBASE_URL = "https://pocs-project-68633-default-rtdb.asia-southeast1.firebasedatabase.app"
USER_ID = "UID12345"   # you can change this to another test user
PORTFOLIO = "BTC=0.25, ETH=1.5"   # sample plaintext portfolio

# -------------------
# Helpers
# -------------------
def pad(data, block_size):
    padding_len = block_size - len(data) % block_size
    return data + chr(padding_len) * padding_len

def unpad(data):
    padding_len = ord(data[-1])
    return data[:-padding_len]

def aes_encrypt_decrypt(plaintext):
    key = get_random_bytes(16)  # 128-bit AES key
    cipher = AES.new(key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(plaintext, 16).encode())
    b64 = base64.b64encode(ciphertext).decode()

    decipher = AES.new(key, AES.MODE_ECB)
    decrypted = unpad(decipher.decrypt(ciphertext).decode())
    return b64, decrypted

def des_encrypt_decrypt(plaintext):
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
    print("Plaintext portfolio:", PORTFOLIO)

    # AES
    aes_ct, aes_pt = aes_encrypt_decrypt(PORTFOLIO)
    print("\nAES Encrypted:", aes_ct)
    print("AES Decrypted:", aes_pt)

    # DES
    des_ct, des_pt = des_encrypt_decrypt(PORTFOLIO)
    print("\nDES Encrypted:", des_ct)
    print("DES Decrypted:", des_pt)

    # Push to Firebase
    data = {
        "portfolio_AES": aes_ct,
        "portfolio_DES": des_ct
    }
    r = requests.put(f"{FIREBASE_URL}/users/{USER_ID}.json", json=data)
    print("\nWrite status:", r.status_code)

    # Read back from Firebase
    r = requests.get(f"{FIREBASE_URL}/users/{USER_ID}.json")
    print("Data read from Firebase:", r.json())
