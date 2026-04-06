"""
Firebase Realtime Database utility functions.
Handles all read/write operations to Firebase REST API.
"""

import requests
from config import FIREBASE_URL


def write_user_data(user_id: str, data: dict) -> int:
    """
    Write data to Firebase under /users/{user_id}.
    Uses PUT (overwrites entire user node).
    Returns HTTP status code.
    """
    url = f"{FIREBASE_URL}/users/{user_id}.json"
    r = requests.put(url, json=data, timeout=10)
    return r.status_code


def patch_user_data(user_id: str, data: dict) -> int:
    """
    Patch (merge) data into Firebase under /users/{user_id}.
    Uses PATCH (preserves existing fields).
    Returns HTTP status code.
    """
    url = f"{FIREBASE_URL}/users/{user_id}.json"
    r = requests.patch(url, json=data, timeout=10)
    return r.status_code


def read_user_data(user_id: str) -> dict | None:
    """
    Read user data from Firebase under /users/{user_id}.
    Returns parsed JSON dict, or None on error.
    """
    try:
        url = f"{FIREBASE_URL}/users/{user_id}.json"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def write_public_data(key: str, data: dict) -> int:
    """
    Write data to Firebase under /public/{key}.
    Returns HTTP status code.
    """
    url = f"{FIREBASE_URL}/public/{key}.json"
    r = requests.put(url, json=data, timeout=10)
    return r.status_code


def read_public_data(key: str) -> dict | None:
    """
    Read public data from Firebase under /public/{key}.
    Returns parsed JSON dict, or None on error.
    """
    try:
        url = f"{FIREBASE_URL}/public/{key}.json"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None
