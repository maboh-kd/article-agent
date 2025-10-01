import json, os, requests
from typing import Optional

def post_via_webhook(webhook_url: str, text: str) -> None:
    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL が未設定です")
    resp = requests.post(webhook_url, json={"text": text}, timeout=15)
    resp.raise_for_status()

def post_via_bot(token: str, channel: str, text: str) -> None:
    if not token or not channel:
        raise ValueError("SLACK_BOT_TOKEN/SLACK_CHANNEL_ID が未設定です")
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"channel": channel, "text": text}
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error: {data}")

def build_summary_message(headline: str, summary: str, link_hint: Optional[str] = None) -> str:
    msg = f"{headline}\n{summary}"
    if link_hint:
        msg += f"\n全文: {link_hint}"
    return msg
