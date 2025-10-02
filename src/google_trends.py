from typing import List, Tuple

def fetch_trending_queries() -> List[Tuple[str, float]]:
    # 後でpytrends実装に差し替え。今は通電優先で固定値。
    return [("離乳食 鉄分", 78.0), ("保育園 入園準備", 66.0), ("寝かしつけ 方法", 61.0)]
