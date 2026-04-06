import requests # library to send http requests to firebase

# Replace with your database URL
FIREBASE_URL = FIREBASE_URL = "https://pocs-project-68633-default-rtdb.asia-southeast1.firebasedatabase.app"

# Write some test data
data = {
    "message": "Hello from Python",
    "encryption": "AES",
    "value": "U2FsdGVkX19a3hJ4Nv9qkqvK2uF1zM3n"
}

# PUT request to write under /users/UID12345
r = requests.put(f"{FIREBASE_URL}/users/UID12345.json", json=data)
print("Write status:", r.status_code)

# GET request to read back
r = requests.get(f"{FIREBASE_URL}/users/UID12345.json")
print("Data read:", r.json())
