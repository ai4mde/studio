import requests
import json
import sys

try:
    headers = {"Authorization": "Bearer studio-internal-service-key"}
    resp = requests.get('http://localhost:8000/api/v1/metadata/interfaces/', headers=headers)
    resp.raise_for_status()
    data = resp.json()
    print(json.dumps(data[:5], indent=2))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
