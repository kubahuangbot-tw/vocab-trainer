#!/usr/bin/env python3
"""
單字建議定義審核工具
1. 從 NAS 拉最新 vocab.db
2. 找出有 suggested_meaning 的單字
3. 用 Claude API 判斷建議是否合理
4. 合理則自動替換 meaning；不合理則清除 suggested_meaning
5. 同步更新後的 DB 回 NAS

執行：python3 review_suggestions.py [--dry-run]
"""
import sqlite3, subprocess, sys, json, time
from pathlib import Path
import anthropic

BASE_DIR  = Path(__file__).parent
LOCAL_DB  = BASE_DIR / "data" / "vocab.db"
NAS_HOST  = "kubabot@192.168.1.109"
NAS_KEY   = Path.home() / ".ssh" / "nas_key"
NAS_DB    = "/volume1/botfoler/vocabtrainer_v3/data/vocab.db"
DRY_RUN   = "--dry-run" in sys.argv

client = anthropic.Anthropic()

# ── 1. 拉最新 DB ─────────────────────────────────────
def pull_db():
    print("📥 從 NAS 拉取最新 vocab.db ...")
    result = subprocess.run(
        ["scp", "-i", str(NAS_KEY), "-o", "StrictHostKeyChecking=no",
         f"{NAS_HOST}:{NAS_DB}", str(LOCAL_DB)],
        capture_output=True
    )
    if result.returncode != 0:
        print("⚠️  SCP 失敗，使用本地 DB")
    else:
        print("✅ DB 已更新")

# ── 2. 讀取待審核單字 ────────────────────────────────
def get_pending():
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, word, meaning, suggested_meaning
        FROM words
        WHERE suggested_meaning IS NOT NULL AND suggested_meaning != ''
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ── 3. Claude 審核 ───────────────────────────────────
def review_with_llm(word: str, current_meaning: str, suggestion: str) -> dict:
    prompt = f"""你是英文單字審核員，請判斷用戶對英文單字的中文定義建議是否比現有定義更準確、更易懂。

單字：{word}
現有定義：{current_meaning}
用戶建議：{suggestion}

請回覆 JSON 格式（只回 JSON，不要加其他文字）：
{{
  "accept": true 或 false,
  "reason": "簡短說明（20字內）"
}}

判斷標準：
- 建議的翻譯是否正確？
- 是否比現有定義更簡潔易懂？
- 是否包含不雅或錯誤內容？
"""
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(msg.content[0].text)
    except Exception as e:
        print(f"  ⚠️  LLM 錯誤：{e}")
        return {"accept": False, "reason": "審核失敗"}

# ── 4. 更新 DB ───────────────────────────────────────
def apply_decision(word_id: int, accept: bool, suggestion: str):
    conn = sqlite3.connect(LOCAL_DB)
    cur = conn.cursor()
    if accept:
        cur.execute(
            "UPDATE words SET meaning=?, suggested_meaning=NULL, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (suggestion, word_id)
        )
    else:
        cur.execute("UPDATE words SET suggested_meaning=NULL WHERE id=?", (word_id,))
    conn.commit()
    conn.close()

# ── 5. 同步回 NAS ────────────────────────────────────
def push_db():
    print("\n📤 同步 DB 回 NAS ...")
    result = subprocess.run(
        ["scp", "-i", str(NAS_KEY), "-o", "StrictHostKeyChecking=no",
         str(LOCAL_DB), f"{NAS_HOST}:{NAS_DB}"],
        capture_output=True
    )
    if result.returncode == 0:
        print("✅ 同步完成")
    else:
        print(f"❌ 同步失敗：{result.stderr.decode()}")

# ── 主流程 ───────────────────────────────────────────
def main():
    if not DRY_RUN:
        pull_db()

    pending = get_pending()
    if not pending:
        print("✅ 沒有待審核的建議")
        return

    print(f"\n📋 找到 {len(pending)} 個待審核建議\n")
    accepted = rejected = 0

    for row in pending:
        word = row["word"]
        current = row["meaning"]
        suggestion = row["suggested_meaning"]
        print(f"🔍 {word}")
        print(f"   現有：{current}")
        print(f"   建議：{suggestion}")

        result = review_with_llm(word, current, suggestion)
        accept = result.get("accept", False)
        reason = result.get("reason", "")

        if accept:
            print(f"   ✅ 接受 — {reason}")
            accepted += 1
        else:
            print(f"   ❌ 拒絕 — {reason}")
            rejected += 1

        if not DRY_RUN:
            apply_decision(row["id"], accept, suggestion)

        time.sleep(0.3)

    print(f"\n{'='*40}")
    print(f"審核完成：✅ 接受 {accepted}  ❌ 拒絕 {rejected}")

    if not DRY_RUN and (accepted + rejected) > 0:
        push_db()

if __name__ == "__main__":
    main()
