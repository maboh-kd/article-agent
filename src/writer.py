from openai import OpenAI
from .config import OPENAI_API_KEY

SYSTEM = "あなたは育児ジャンルの凄腕ライターです。要点を整理して論理的に書きます。"

def generate_article(topic: str) -> str:
    if not OPENAI_API_KEY:
        # 鍵未設定でもパイプラインが落ちないためのダミー本文
        return f"【ダミー記事】\nテーマ: {topic}\n\n本文生成の本番化前テスト中。後でOpenAI生成に切り替わります。"

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""# テーマ
{topic}

# 要求
- 導入→課題→解決策→まとめ（1200字前後）
- 根拠や数値を可能な範囲で明示
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":SYSTEM},
                  {"role":"user","content":prompt}],
        temperature=0.7,
        max_tokens=1200,
    )
    return resp.choices[0].message.content.strip()
