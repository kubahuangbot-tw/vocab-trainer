#!/usr/bin/env python3
"""
VocabTrainer — 建議移除單字審核腳本

功能：
1. 從 Supabase 拉取所有被投票移除的單字
2. 用 Claude CLI 分析每個單字的類型（人名/品牌/縮寫/正常詞彙）
3. 建議刪除或保留並更新 meaning
4. 執行 DB 操作

使用方式：
  python3 review_removal_votes.py          # 互動模式（逐一確認）
  python3 review_removal_votes.py --auto   # 自動模式（依 Claude 建議直接執行）

需求：
  pip install psycopg2-binary anthropic
"""

import sys
import psycopg2
import psycopg2.extras

DATABASE_URL = "postgresql://postgres.wzxqbvrtrjgndfhxxyjw:LFHGDXKg22rnSDPO@aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require"

PROPER_NOUN_PATTERNS = {
    # 已知人名 pattern（可自行擴充）
    "person_names": [],
    # 已知品牌
    "brands": ["toyota", "honda", "benz", "mercedes", "bmw", "nintendo", "sony", "samsung",
               "apple", "google", "microsoft", "amazon", "facebook", "twitter", "instagram",
               "pepsi", "coca-cola", "starbucks", "mcdonald", "ikea", "nike", "adidas"],
    # 縮寫（全大寫或常見縮寫）
    "abbreviations": ["nhs", "lcd", "cpu", "gpu", "dna", "rna", "usa", "uk", "eu", "un",
                      "nato", "who", "imf", "gdp", "gop"],
    # 已消失或過於特定的網站/服務
    "obsolete": ["epinions", "friendster", "myspace", "digg", "netscape"],
}


def get_flagged_words():
    """從 DB 拉取被投票移除的單字"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, word, meaning, cefr, removal_vote_count
        FROM words
        WHERE removal_vote_count > 0
        ORDER BY removal_vote_count DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def heuristic_classify(word, meaning):
    """
    簡單規則分類，不需要 API
    回傳：('delete'|'update'|'keep', reason)
    """
    w = word.lower()

    # 品牌
    for brand in PROPER_NOUN_PATTERNS["brands"]:
        if w == brand:
            return "delete", f"品牌名稱：{brand}"

    # 縮寫
    for abbr in PROPER_NOUN_PATTERNS["abbreviations"]:
        if w == abbr:
            return "delete", f"縮寫/簡稱：{abbr}"

    # 已消失服務
    for obs in PROPER_NOUN_PATTERNS["obsolete"]:
        if w == obs:
            return "delete", f"已消失的網站/服務：{obs}"

    # meaning 是純音譯（短、無實質解釋）
    if len(meaning) <= 4 and not any(c in meaning for c in "的是一種"):
        return "review", f"meaning 過短，可能是音譯人名：{meaning}"

    return "keep", "無明顯問題"


def delete_word(word_id, word, conn):
    """刪除單字及相關記錄"""
    cur = conn.cursor()
    cur.execute("DELETE FROM user_progress WHERE word_id = %s", (word_id,))
    cur.execute("DELETE FROM wrong_records WHERE word_id = %s", (word_id,))
    cur.execute("DELETE FROM word_removal_votes WHERE word = %s", (word,))
    cur.execute("DELETE FROM word_image_bad_votes WHERE word = %s", (word,))
    cur.execute("DELETE FROM word_set_members WHERE word_id = %s", (word_id,))
    cur.execute("DELETE FROM words WHERE id = %s RETURNING word", (word_id,))
    result = cur.fetchone()
    return result is not None


def update_meaning(word_id, new_meaning, conn):
    """更新單字 meaning 並清除投票"""
    cur = conn.cursor()
    cur.execute(
        "UPDATE words SET meaning=%s, removal_vote_count=0 WHERE id=%s RETURNING word",
        (new_meaning, word_id)
    )
    cur.execute("DELETE FROM word_removal_votes WHERE word = (SELECT word FROM words WHERE id=%s)", (word_id,))
    return cur.fetchone() is not None


def main():
    auto_mode = "--auto" in sys.argv

    print("=" * 60)
    print("VocabTrainer 建議移除單字審核")
    print("=" * 60)

    flagged = get_flagged_words()
    if not flagged:
        print("目前沒有被投票的單字。")
        return

    print(f"\n共 {len(flagged)} 個被投票的單字：\n")

    actions = []
    for w in flagged:
        action, reason = heuristic_classify(w["word"], w["meaning"])
        print(f"  {w['word']:20s} ({w['cefr']}) | {w['meaning']}")
        print(f"  票數：{w['removal_vote_count']}  建議：{action}  原因：{reason}")
        print()

        if not auto_mode and action in ("delete", "update"):
            confirm = input(f"  執行「{action}」？ (y/n/skip) > ").strip().lower()
            if confirm != "y":
                action = "skip"

        actions.append((w, action))

    # Execute
    conn = psycopg2.connect(DATABASE_URL)
    deleted = []
    skipped = []

    for w, action in actions:
        if action == "delete":
            ok = delete_word(w["id"], w["word"], conn)
            if ok:
                deleted.append(w["word"])
        elif action == "skip":
            skipped.append(w["word"])

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print(f"已刪除：{deleted}")
    print(f"已跳過：{skipped}")
    print("Done!")


if __name__ == "__main__":
    main()
