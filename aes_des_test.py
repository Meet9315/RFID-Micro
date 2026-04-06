from Crypto.Cipher import AES, DES
from Crypto.Random import get_random_bytes
import base64, time

# Padding function (DES needs 8-byte multiples, AES needs 16-byte multiples)
def pad(data, block_size):
    padding_len = block_size - len(data) % block_size
    return data + chr(padding_len) * padding_len

def unpad(data):
    padding_len = ord(data[-1])
    return data[:-padding_len]

# Test string
plaintext = "BTC=0.25, ETH=1.5"

# --- AES Test ---
key_aes = get_random_bytes(16)   # AES requires 16 bytes = 128-bit key
cipher_aes = AES.new(key_aes, AES.MODE_ECB) # create AES cipher in ECB mode

start = time.time() # start timer
ciphertext_aes = cipher_aes.encrypt(pad(plaintext, 16).encode()) # encrypt padded text
end = time.time() # stop timer

print("AES Encrypted:", base64.b64encode(ciphertext_aes).decode()) # print cipher text (base64)
print("AES Time:", (end - start) * 1000, "ms") # print time taken

decipher_aes = AES.new(key_aes, AES.MODE_ECB)
decrypted_aes = unpad(decipher_aes.decrypt(ciphertext_aes).decode())
print("AES Decrypted:", decrypted_aes)

# --- DES Test ---
key_des = get_random_bytes(8)   # DES is 8 bytes = 64-bit key
cipher_des = DES.new(key_des, DES.MODE_ECB)

start = time.time()
ciphertext_des = cipher_des.encrypt(pad(plaintext, 8).encode())
end = time.time()

print("\nDES Encrypted:", base64.b64encode(ciphertext_des).decode())
print("DES Time:", (end - start) * 1000, "ms")

decipher_des = DES.new(key_des, DES.MODE_ECB)
decrypted_des = unpad(decipher_des.decrypt(ciphertext_des).decode())
print("DES Decrypted:", decrypted_des)
