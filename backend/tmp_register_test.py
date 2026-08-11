import json
from urllib import request, error
import time

url = 'http://127.0.0.1:8001/api/v1/auth/register'
payload = {
    'email': 'piyush+trace@example.com',
    'password': 'Secret123!',
    'full_name': 'Piyush Trace',
    'role': 'doctor',
}

body = json.dumps(payload).encode('utf-8')
req = request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
start = time.time()
try:
    with request.urlopen(req, timeout=20) as resp:
        print('status', resp.status)
        print(resp.read().decode())
except error.HTTPError as e:
    print('HTTP', e.code, e.read().decode())
except Exception as e:
    print('EXC', type(e).__name__, e)
print('elapsed', time.time()-start)
