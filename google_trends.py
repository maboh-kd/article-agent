from typing import List
from ..types import TrendItem

class GoogleTrendsSource:
    name = "google_trends"

    def __init__(self, hl: str = "ja-JP", tz: int = 540):
        self.hl = hl
        self.tz = tz

    def fetch(self, limit: int = 5) -> List[TrendItem]:
        """pytrendsを使った実装に差し替え推奨。
        フォールバックとしてダミーを返す（最初の作動確認用）。
        """
        # --- 本実装の例（コメントアウト）： ---
        # from pytrends.request import TrendReq
        # pytrends = TrendReq(hl=self.hl, tz=self.tz)
        # df = pytrends.trending_searches(pn='japan')
        # topics = [x for x in df[0].tolist() if len(x) >= 2][:limit]
        # return [{
        #     "topic": t,
        #     "source": self.name,
        #     "evidence": [],
        #     "why_now": "Googleトレンド上昇ワード",
        #     "keywords": [t]
        # } for t in topics]

        # --- フォールバック（ダミー） ---
        dummies: List[TrendItem] = [
            {"topic": "一歳児 手づかみ食べ", "source": self.name, "evidence": [], "why_now": "ダミー", "keywords": ["一歳児","食","安全"]},
            {"topic": "赤ちゃん 便秘 対処", "source": self.name, "evidence": [], "why_now": "ダミー", "keywords": ["便秘","対処"]},
            {"topic": "保育園 慣らし保育 期間", "source": self.name, "evidence": [], "why_now": "ダミー", "keywords": ["保育園","慣らし"]}
        ]
        return dummies[:limit]
