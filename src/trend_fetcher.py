# -*- coding: utf-8 -*-
"""
トレンド収集（日本×育児ドメイン寄せ）→TXT保存→Slack通知
- デフォルト: 日本(JP) / 育児系シード語 / 直近7日間 / 上位30件
- モード:
    HOT: Googleの「今日は急上昇」(国別)でシンプルに収集（カテゴリ指定は不可）
    SEEDED: 育児系シード語から関連クエリを収集（カテゴリ寄せに最適・推奨）
- 主要パラメータは環境変数で上書き可能（GitHub Actions からも設定可）
"""

import os
import re
import json
import datetime as dt
from pytrends.request import TrendReq
import requests
from pathlib import Path

# -------------------------
# 環境変数（簡単に変更できるように）
# -------------------------
MODE = os.getenv("GTR_MODE", "SEEDED").upper()     # "SEEDED" or "HOT"
GEO = os.getenv("GTR_GEO", "JP")                   # 国コード
TIMEFRAME = os.getenv("GTR_TIMEFRAME", "now 7-d")  # 期間
TOP_N = int(os.getenv("GTR_TOP_N", "30"))          # 出力件数
OUT_DIR = os.getenv("GTR_OUT_DIR", "assets")       # 保存フォルダ
OUT_PREFIX = os.getenv("GTR_OUT_PREFIX", "trends") # ファイル名接頭辞
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL") # Slack Incoming Webhook (Secretsで設定)
# 育児寄せのシード語（カンマ区切りで上書き可能）
SEEDS_ENV = os.getenv(
    "GTR_SEEDS",
    "育児, 子育て, 赤ちゃん, 1歳, 2歳, 保育園, 夜泣き, 離乳食, イヤイヤ期, トイレトレーニング, 予防接種, 断乳"
)
SEEDS = [s.strip() for s in SEEDS_ENV.split(",") if s.strip()]

# 軽い正規化用（ノイズ削ぎ落とし）
EMOJI_RE = re.compile(
    "["                     # 多くの絵文字領域をザックリ削除
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002700-\U000027BF"
    "]+",
    flags=re.UNICODE
)

STOPWORDS = set([
    # よくあるノイズ・曖昧語（最低限）
    "とは", "とは？", "いつ", "どこ", "なに", "何", "ニュース", "まとめ", "意味", "英語",
    "twitter", "x", "画像", "動画", "公式", "wiki", "価格", "値段",
])

MIN_LEN = int(os.getenv("GTR_MIN_LEN", "2"))  # 短すぎる語を除外

def normalize(q: str) -> str:
    q = q.strip()
    q = EMOJI_RE.sub("", q)
    q = re.sub(r"\s+", " ", q)
    return q

def is_valid(q: str) -> bool:
    if len(q) < MIN_LEN:
        return False
    if q.lower() in STOPWORDS:
        return False
    return True

def fetch_hot(pytrends: TrendReq, geo: str) -> list[str]:
    """国別急上昇をざっと取得（カテゴリ指定は不可）。"""
    try:
        df = pytrends.trending_searches(pn="japan" if geo.upper()=="JP" else "united_states")
        # jp以外は簡易対応：USにフォールバック。必要ならpnマップ拡張可。
        words = [normalize(str(x)) for x in df[0].tolist()]
        words = [w for w in words if is_valid(w)]
        return words
    except Exception as e:
        print(f"[WARN] HOT取得でエラー: {e}")
        return []

def fetch_seeded(pytrends: TrendReq, geo: str, timeframe: str, seeds: list[str]) -> list[str]:
    """シード語から関連クエリを集める（育児ドメイン寄せ）。"""
    bag = []
    for kw in seeds:
        try:
            pytrends.build_payload([kw], timeframe=timeframe, geo=geo, cat=0)  # catは0（全体）にしてドメインをシードで寄せる
            rq = pytrends.related_queries()
            if kw in rq and isinstance(rq[kw], dict):
                for k in ("rising", "top"):
                    df = rq[kw].get(k)
                    if df is None:
                        continue
                    for term in df["query"].tolist():
                        bag.append(term)
        except Exception as e:
            print(f"[WARN] SEEDED取得で {kw} 失敗: {e}")
    # 正規化とフィルタ
    bag = [normalize(x) for x in bag]
    bag = [x for x in bag if is_valid(x)]
    # 出現頻度でソート（多いほど先頭）
    from collections import Counter
    cnt = Counter(bag)
    ranked = [w for w, _ in cnt.most_common()]
    return ranked

def dedup_preserve_order(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def save_txt(words: list[str], out_dir: str, prefix: str) -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y%m%d_%H%M%S")  # JSTタイムスタンプ
    path = Path(out_dir) / f"{prefix}_{stamp}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write("# トレンド抽出結果（JST）\n")
        f.write(f"# mode={MODE}  geo={GEO}  timeframe='{TIMEFRAME}'  top={TOP_N}\n")
        f.write(f"# seeds={','.join(SEEDS)}\n\n")
        for i, w in enumerate(words, 1):
            f.write(f"{i:02d}. {w}\n")
    return path

def post_slack(words: list[str]):
    if not SLACK_WEBHOOK_URL:
        print("[INFO] SLACK_WEBHOOK_URL 未設定。Slack通知はスキップします。")
        return
    title = f":satellite: トレンド速報（{GEO} / {MODE} / {TIMEFRAME}）"
    lines = "\n".join([f"{i+1:02d}. {w}" for i, w in enumerate(words)])
    text = f"*{title}*\n```\n{lines}\n```"
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=15)
        if resp.status_code >= 300:
            print(f"[WARN] Slack通知に失敗: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[WARN] Slack通知エラー: {e}")

def main():
    print(f"[INFO] Start: mode={MODE} geo={GEO} timeframe={TIMEFRAME} top={TOP_N}")
    pytrends = TrendReq(hl="ja-JP", tz=540)  # JST(+9h)相当
    words: list[str] = []

    if MODE == "HOT":
        words = fetch_hot(pytrends, GEO)
    else:
        words = fetch_seeded(pytrends, GEO, TIMEFRAME, SEEDS)

    words = dedup_preserve_order(words)
    words = words[:TOP_N]

    out_path = save_txt(words, OUT_DIR, OUT_PREFIX)
    print(f"[INFO] Saved: {out_path}")

    post_slack(words)
    print("[INFO] Done.")

if __name__ == "__main__":
    main()
