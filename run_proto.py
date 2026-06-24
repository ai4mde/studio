import json, urllib.error, urllib.request, time

# First stop any running prototype
try:
    req = urllib.request.Request('http://localhost:8010/stop_prototypes', data=b'', method='POST')
    urllib.request.urlopen(req)
    time.sleep(1)
except urllib.error.URLError:
    pass

# Start the prototype
data = json.dumps({
    'id': 'e2d70c9b-aa29-40f8-9612-680603763443',
    'name': 'sync1781202455394',
    'system': 'a0000002-0000-5000-8000-000000000000'
}).encode()

req = urllib.request.Request(
    'http://localhost:8010/run',
    data=data,
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    resp = urllib.request.urlopen(req)
    print("Started:", resp.status)
except urllib.error.HTTPError as e:
    if e.code == 307:
        print("Started (307 redirect = success)")
    else:
        print("Error:", e.code, e.read()[:200])
except Exception as e:
    print("Error:", e)

# Wait and check status
time.sleep(5)
status_req = urllib.request.Request('http://localhost:8010/active_prototype')
status = json.loads(urllib.request.urlopen(status_req).read())
print("Status:", json.dumps(status, indent=2))
