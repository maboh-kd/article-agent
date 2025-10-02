import json, urllib.request
from .config import SLACK_WEBHOOK_URL

def send_to_slack(text: str) -> None:
    if not SLACK_WEBHOOK_URL:
        print("[Slack dummy] " + text[:1200])
        return
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        assert r.status == 200
