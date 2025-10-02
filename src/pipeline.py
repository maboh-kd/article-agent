from datetime import datetime
from .google_trends import fetch_trending_queries
from .writer import generate_article
from .slack_notify import send_to_slack

def main() -> int:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    trends = fetch_trending_queries()
    head = f"📰 記事生成エージェント {ts}\n候補: " + ", ".join([q for q,_ in trends])

    topic = trends[0][0] if trends else "育児 トレンド"
    article = generate_article(topic)

    send_to_slack(head + f"\n\n# {topic}\n\n" + article[:1500] + ("…" if len(article)>1500 else ""))
    return 0
