"""Simple test for A8 endpoints using urllib (no external deps)."""
import json
from urllib import request, parse

BASE = "http://127.0.0.1:8000/api/v1"

def post_json(path, data):
    data_bytes = json.dumps(data).encode("utf-8")
    req = request.Request(BASE + path, data=data_bytes, headers={"Content-Type": "application/json"})
    with request.urlopen(req) as resp:
        return json.load(resp)

def post_form(path, form):
    data = parse.urlencode(form).encode()
    req = request.Request(BASE + path, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with request.urlopen(req) as resp:
        return json.load(resp)

def get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(BASE + path, headers=headers)
    with request.urlopen(req) as resp:
        return json.load(resp)

if __name__ == "__main__":
    try:
        print("Registering user...")
        r = post_json("/auth/register", {"email": "test@local", "password": "Pass1234", "full_name": "Test User"})
        print(r)
    except Exception as e:
        print("Register may have failed or user exists:", e)
    print("Logging in...")
    login = post_form("/auth/login", {"username": "test@local", "password": "Pass1234"})
    print(login)
    token = login.get("access_token")
    print("Got token:", bool(token))
    print("Profile:")
    print(get("/settings/profile", token=token))
    print("Devices:")
    print(get("/settings/devices", token=token))
    print("Sessions:")
    print(get("/settings/sessions", token=token))
    print("Login history:")
    print(get("/settings/login-history", token=token))
