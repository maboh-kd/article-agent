from datetime import datetime
from .google_trends import fetch_trending_queries, pick_topic_and_record
from .writer import generate_article
from .slack_notify import send_to_slack

def main() -> int:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    candidates = fetch_trending_queries()  # [(query, score)]
    head = "候補: " + ", ".join([f"{q}（{int(s)}）" for q, s in candidates]) if candidates else "候補: 取得失敗→フォールバック"

    topic, score = pick_topic_and_record(candidates)
    article = generate_article(topic)

    body = f"📰 記事生成エージェント {ts}\n{head}\n\n# {topic}（{int(score)}）\n\n{article}"
    # 長文のときは分割送信したいなら、ここで chunk してループ送信でもOK
    send_to_slack(body)
    return 0
