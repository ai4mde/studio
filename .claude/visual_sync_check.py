"""
Stop hook: compare preview vs. running prototype via the visual_check API.
Outputs JSON with additionalContext summarizing any mismatches for Claude.
Requires only `requests` (no psycopg2 needed — uses REST API for data).
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
API_BASE = "http://localhost:8000/api/v1"


def dotenv_values(path: str) -> dict:
    result = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return result


def load_config() -> dict:
    cfg = {}
    for env_file in ["config/api.env", "config/secrets.env", "config/prototypes.env"]:
        cfg.update(dotenv_values(str(ROOT / env_file)))
    return cfg


def get_token(cfg: dict) -> str | None:
    import requests
    try:
        resp = requests.post(
            f"{API_BASE}/auth/token",
            json={
                "username": cfg.get("DJANGO_SUPERUSER_USERNAME", "admin"),
                "password": cfg.get("DJANGO_SUPERUSER_PASSWORD", ""),
            },
            timeout=10,
        )
        if resp.ok:
            return resp.json().get("token")
    except Exception:
        pass
    return None


def get_interfaces(token: str) -> list[dict]:
    import requests
    try:
        resp = requests.get(
            f"{API_BASE}/metadata/interfaces/",
            params={"limit": 50},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if not resp.ok:
            return []
        return [
            iface for iface in resp.json()
            if iface.get("data", {}).get("pages")
        ]
    except Exception:
        return []


def visual_check(interface_id: str, token: str) -> dict:
    import requests
    try:
        resp = requests.post(
            f"{API_BASE}/generator/prototypes/visual_check/",
            json={"interface_id": str(interface_id)},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        if resp.status_code in (404, 502):
            return {"skipped": True, "reason": resp.json().get("detail", "unavailable")}
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"skipped": True, "reason": str(e)}


def main():
    cfg = load_config()
    token = get_token(cfg)
    if not token:
        sys.exit(0)

    interfaces = get_interfaces(token)
    if not interfaces:
        sys.exit(0)

    summary_lines = []
    any_fail = False

    for iface in interfaces:
        name = iface.get("name", iface["id"])
        result = visual_check(str(iface["id"]), token)

        if result.get("skipped"):
            reason = result.get("reason", "")
            if any(kw in reason for kw in ("No prototype", "prototype API", "unavailable", "Connection aborted", "ConnectionAbortedError", "RemoteDisconnected", "ConnectionRefused", "ConnectionError")):
                sys.exit(0)
            summary_lines.append(f"[{name}] skipped: {reason}")
            continue

        checks = result.get("checks", [])
        if not checks:
            continue

        fails = [c for c in checks if not c.get("ok")]
        ok_count = len(checks) - len(fails)

        if fails:
            any_fail = True
            for f in fails:
                mismatches = "; ".join(f.get("mismatches", [])[:3])
                summary_lines.append(f"[{name}] page '{f['page']}' MISMATCH: {mismatches}")
        else:
            summary_lines.append(f"[{name}] OK {ok_count}/{len(checks)} pages consistent")

    if not summary_lines:
        sys.exit(0)

    status = "MISMATCHES DETECTED — prototype/preview out of sync" if any_fail else "all pages consistent"
    context = f"Visual sync check ({status}):\n" + "\n".join(summary_lines)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
