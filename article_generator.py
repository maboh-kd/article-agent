from typing import Dict
from .prompt_templates import ARTICLE_PROMPT
from ..types import TrendItem, ArticleDoc

def _dummy_generate(trend: TrendItem) -> ArticleDoc:
    title = f"トレンド速記：{trend.get('topic')}"
    greeting = f"この記事はAIに丸投げで生成しています。テーマは『{trend.get('topic')}』。最新トレンドを参考に、専門家目線でまとめました。"
    body = (
        "■ テーマの背景\n"
        f"『{trend.get('topic')}』は今週の育児トレンドで注目上昇。家庭で実践しやすい要点に絞ります。\n\n"
        "■ 適正量・安全ラインの目安\n"
        "手のひら1枚など視覚基準で安定化。専門用語は初出で一言解説。\n\n"
        "■ よくある悩みと処方箋\n"
        "偏食/食べない/むらの3類型に観察→対策で対応。\n\n"
        "■ ミニFAQ\n"
        "年齢別の可否や例外を簡潔に整理。迷ったら専門家へ。\n"
    )
    review = "仕上がり総評：見出しで短尺化し、スマホでも読みやすい。根拠はURLで裏取り可の軽量設計。"
    return {
        "title": title,
        "sections": {"greeting": greeting, "body": body, "review": review},
        "meta": {"keywords": trend.get("keywords", []), "length": len(greeting)+len(body)+len(review)}
    }

def generate_article_with_model(trend: TrendItem, *, use_dummy: bool = True) -> ArticleDoc:
    """本番ではOpenAI等のモデル呼び出しに差し替え。
    use_dummy=True の間はダミー本文を返す（動作確認用）。
    """
    if use_dummy:
        return _dummy_generate(trend)

    # --- 参考：OpenAI SDKの雛形（コメントアウト） ---
    # from openai import OpenAI
    # import os
    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # prompt = ARTICLE_PROMPT(trend)
    # resp = client.chat.completions.create(
    #     model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    #     messages=[{"role":"system","content":"あなたは小児栄養と育児支援の専門家です。"},
    #               {"role":"user","content": prompt}]
    # )
    # text = resp.choices[0].message.content
    # # textから greeting/body/review を簡易パース（目印や区切りをプロンプトで明示しておくと楽）
    # # ここでは単純に丸ごとbodyに入れる例：
    # return {
    #     "title": f"トレンド速記：{trend.get('topic')}",
    #     "sections": {"greeting": "（自動生成）", "body": text, "review": "（自動生成）"},
    #     "meta": {"keywords": trend.get("keywords", [])}
    # }

    raise RuntimeError("use_dummy=False ですが実装がコメントアウトのままです")
