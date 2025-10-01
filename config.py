import os
from dotenv import load_dotenv

load_dotenv()

# ディレクトリ
ARTICLE_DIR = os.getenv("AGENT_ARTICLE_DIR", "outputs")
LOG_DIR = os.getenv("AGENT_LOG_DIR", "logs")

# Slack
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "").strip()
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "").strip()

# Trends
TREND_LIMIT = int(os.getenv("AGENT_TREND_LIMIT", "5"))
TOPIC_MIN_LEN = int(os.getenv("AGENT_TOPIC_MIN_LEN", "4"))

# Model
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
