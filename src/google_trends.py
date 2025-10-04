# -*- coding: utf-8 -*-
from __future__ import annotations
import json, random, time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd
from pytrends.request import TrendReq

# ===== 運用パラメタ =====
GEO = "JP"                    # 日本
HL = "ja-JP"
TZOFFSET = 540                # JST=+9h
HISTORY_PATH = Path("data/trend_history.json")
HISTORY_DAYS_AVOID = 10       # 直近N日は同一テーマを避ける
MAX_RESULTS = 12              # 候補最大件数

# バックアップ語彙（トレンド取得失敗時の非常口）
BACKUP_QUERIES = [
    "離乳食 鉄分", "寝かしつけ 方法", "偏食 対処", "一歳 生活リズム", "保育園 入園準備",
    "イヤイヤ期 対処", "断乳 進め方", "仕上げ磨き コツ", "夜泣き 対策", "虫歯 予防",
]

# ====== ここから本体 ======

def _load_history() -> List[dict]:
    try:
        if HISTORY_PATH.exists():
            return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []

def _save_history(rows: List[dict]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

def _recently_used_set(days: int) -> set[str]:
    hist = _load_history()
    cutoff = (datetime.now() - timedelta(days=days)).date().isoformat()
    used = {r["query"] for r in hist if r.get("date", "") >= cutoff}
    return used

def _append_history(query: str, score: float) -> None:
    hist = _load_history()
    hist.append({
        "date": datetime.now().date().isoformat(),
        "query": query,
        "score": float(score),
    })
    # サイズが膨らみすぎないよう軽く上限
    if len(hist) > 1000:
        hist = hist[-1000:]
    _save_history(hist)

def _make_client() -> TrendReq:
    # pytrends は内部で UA をよしなにしてくれるが、接続不調は起きる
    return TrendReq(hl=HL, tz=TZOFFSET, retries=3, backoff_factor=0.3, timeout=(3.0, 10.0))

def _normalize_scores(series: pd.Series) -> pd.Series:
    # 0-100 の相対値で入っていることが多いが、念のため線形正規化
    s = series.fillna(0).astype(float)
    if s.max() <= 0:
        return s
    return (s / s.max() * 100.0).round(2)

def _unique_keep_order(items: List[str]) -> List[str]:
    seen = set(); out = []
    for x in items:
        if x not in seen and x.strip():
            out.append(x); seen.add(x)
    return out

def _candidate_from_related(pytrends: TrendReq, seeds: List[str]) -> List[Tuple[str, float]]:
    """
    種語（seeds）について「関連クエリ」から候補を作る。
    """
    all_rows: list[tuple[str, float]] = []
    for kw in seeds:
        try:
            pytrends.build_payload([kw], cat=0, timeframe="today 3-m", geo=GEO, gprop="")
            related = pytrends.related_queries()
            if not related or kw not in related:
                continue
            rq = related[kw]
            # rising があればまず rising（直近動意）→ 無ければ top
            for key in ("rising", "top"):
                df = rq.get(key)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    df = df.dropna().copy()
                    # 'value' を強度として採用
                    df["value"] = _normalize_scores(df["value"])
                    for q, v in zip(df["query"].astype(str).tolist(), df["value"].tolist()):
                        all_rows.append((q, float(v)))
        except Exception:
            # 1 seed 失敗はスルー、次へ
            continue
        # 相手を怒らせない＆429回避の間合い
        time.sleep(0.8 + random.random() * 0.6)
    # 重複除去（スコアは最大値を採用）
    tmp = {}
    for q, v in all_rows:
        tmp[q] = max(v, tmp.get(q, 0.0))
    rows = [(q, tmp[q]) for q in _unique_keep_order(list(tmp.keys()))]
    # スコア降順で並べて上位だけ返す
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows[:MAX_RESULTS]

def _candidate_from_daily(pytrends: TrendReq) -> List[Tuple[str, float]]:
    """
    デイリートレンド（日本）から候補作成。score は出荷しづらいので 60 固定評価。
    """
    try:
        df = pytrends.trending_searches(pn="japan")
        if isinstance(df, pd.DataFrame) and not df.empty:
            qs = [str(x) for x in df[0].tolist()]
            return [(q, 60.0) for q in qs]
    except Exception:
        pass
    return []

def fetch_trending_queries() -> List[Tuple[str, float]]:
    """
    返り値: [(クエリ, スコア0-100)]
    - pytrends の related_queries & trending_searches を組み合わせ
    - 最近N日で未使用のものを優先フィルタ
    - 失敗時は BACKUP_QUERIES でフォールバック
    """
    used_recent = _recently_used_set(HISTORY_DAYS_AVOID)
    try:
        pytrends = _make_client()

        # 1) コア種語（育児ドメイン）から関連キーワードを掘る
        seed_core = [
            "離乳食", "寝かしつけ", "保育園", "時短 家事", "一歳児", "イヤイヤ期",
            "むし歯 予防", "断乳", "偏食", "保活", "発達 目安", "ベビーカー 選び方"
        ]
        rel = _candidate_from_related(pytrends, seed_core)

        # 2) デイリートレンドも混ぜる（話題の注入）
        daily = _candidate_from_daily(pytrends)

        rows = rel + daily
        if not rows:
            raise RuntimeError("pytrends empty")

        # 3) 最近使ってないものを優先
        fresh = [(q, s) for (q, s) in rows if q not in used_recent]
        if not fresh:
            fresh = rows  # それでも無ければ全体から

        # 4) 上位を少しランダムにサンプリング（単調回避）
        fresh.sort(key=lambda x: x[1], reverse=True)
        topk = fresh[:10]
        # スコアに 1〜5% のノイズを足して重み抽選
        def weight(v: float) -> float:
            return max(0.1, v * (1.0 + random.uniform(-0.05, 0.05)))
        picks = []
        pool = topk.copy()
        while pool and len(picks) < min(5, len(topk)):
            total = sum(weight(v) for _, v in pool)
            r = random.uniform(0, total)
            acc = 0.0
            for i, (q, v) in enumerate(pool):
                acc += weight(v)
                if acc >= r:
                    picks.append((q, v))
                    pool.pop(i)
                    break

        # 5) 最終候補が空ならトップから落とす
        if not picks:
            picks = topk[:5]

        return picks

    except Exception:
        # フォールバック：バックアップ語彙から最近未使用を優先
        pool = [q for q in BACKUP_QUERIES if q not in used_recent] or BACKUP_QUERIES
        random.shuffle(pool)
        return [(q, 50.0) for q in pool[:5]]

def pick_topic_and_record(candidates: Optional[List[Tuple[str, float]]] = None) -> Tuple[str, float]:
    """
    候補から本日の1本を選んで履歴に記録。
    pipeline側で使うユーティリティ。
    """
    if candidates is None:
        candidates = fetch_trending_queries()
    if not candidates:
        topic, score = "育児 トレンド", 40.0
    else:
        # 一番スコア高いものを基本に、わずかに遊びを入れる
        candidates.sort(key=lambda x: x[1], reverse=True)
        topic, score = candidates[0]
        if len(candidates) >= 3 and random.random() < 0.25:
            topic, score = random.choice(candidates[:3])
    _append_history(topic, score)
    return topic, score
