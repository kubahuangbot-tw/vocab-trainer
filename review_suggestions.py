#!/usr/bin/env python3
"""
單字建議定義審核工具（API 版）
1. 登入後端取得 JWT token
2. 找出有 suggested_meaning 的單字 → LLM 審核 → 接受/拒絕
3. 審核例句品質（是否真正示範單字用法，非 meta 句型）
4. DB 由後端管理，不再需要 scp

執行：python3 review_suggestions.py [--dry-run] [--skip-suggestions] [--skip-sentences]
      [--host http://localhost:8000] [--batch-size 30] [--offset 0]

環境變數：
  VOCAB_API_BASE   後端網址，預設 http://192.168.1.109:8501
  VOCAB_ADMIN_USER 管理員帳號，預設 admin
  VOCAB_ADMIN_PASS 管理員密碼（必填）
  GEMINI_API_KEY   Google Gemini API key（必填）
"""
import sys, json, time, re, os
import requests

DRY_RUN        = "--dry-run"         in sys.argv
SKIP_SUGGEST   = "--skip-suggestions" in sys.argv
SKIP_SENTENCES = "--skip-sentences"  in sys.argv

# --host 參數
_host_idx = next((i for i, a in enumerate(sys.argv) if a == "--host"), None)
API_BASE = sys.argv[_host_idx + 1] if _host_idx else os.environ.get("VOCAB_API_BASE", "http://192.168.1.109:8501")

# --batch-size 參數
_bs_idx = next((i for i, a in enumerate(sys.argv) if a == "--batch-size"), None)
BATCH_SIZE = int(sys.argv[_bs_idx + 1]) if _bs_idx else 30

# --offset 參數
_off_idx = next((i for i, a in enumerate(sys.argv) if a == "--offset"), None)
OFFSET = int(sys.argv[_off_idx + 1]) if _off_idx else 0

ADMIN_USER    = os.environ.get("VOCAB_ADMIN_USER", "admin")
ADMIN_PASS    = os.environ.get("VOCAB_ADMIN_PASS", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCRKOilVyIx7f_Ef94Xfh5_B5Vjl45gLxQ")
GEMINI_MODEL  = "gemini-2.5-flash"


# ── 1. 登入取得 token ─────────────────────────────────
def login() -> str:
    if not ADMIN_PASS:
        print("❌ 請設定 VOCAB_ADMIN_PASS 環境變數")
        sys.exit(1)
    resp = requests.post(
        f"{API_BASE}/api/auth/login",
        data={"username": ADMIN_USER, "password": ADMIN_PASS},
        timeout=10
    )
    if resp.status_code != 200:
        print(f"❌ 登入失敗：{resp.status_code} {resp.text}")
        sys.exit(1)
    token = resp.json().get("access_token")
    print(f"✅ 登入成功（{API_BASE}）")
    return token


def api_get(path: str, token: str, **params):
    resp = requests.get(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=15
    )
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, token: str, body: dict):
    resp = requests.post(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
        timeout=15
    )
    resp.raise_for_status()
    return resp.json()


# ── meta 例句快速初篩 ─────────────────────────────────
_META_PATTERNS = [
    r"the\s+(idea|concept|notion|term|word|use|usage)\s+of\s+\w+",
    r"\w+\s+is\s+(a|an)\s+(common|important|key|useful|basic)\s+(word|term|concept)",
    r"the\s+word\s+['\"]?\w+['\"]?\s+is\s+used",
    r"example:\s+the\s+word",
    r"\w+\s+is\s+often\s+misunderstood",
    r"beginners\s+(often|sometimes|frequently)",
    r"is\s+used\s+in\s+many\s+contexts",
]
_META_RE = re.compile("|".join(_META_PATTERNS), re.IGNORECASE)

def _is_meta_sentence(sentence: str) -> bool:
    return bool(_META_RE.search(sentence))


def _llm_chat(prompt: str, max_tokens: int = 300) -> str:
    """呼叫 Gemini API（gemini-2.5-flash，低成本審核用）"""
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens}
        },
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


# ── LLM 審核定義 ──────────────────────────────────────
def review_suggestion_with_llm(word: str, current_meaning: str, suggestion: str) -> dict:
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
        text = _llm_chat(prompt, max_tokens=200)
        if text.startswith("```"):
            text = re.sub(r"```\w*\n?", "", text).strip()
        return json.loads(text)
    except Exception as e:
        print(f"  ⚠️  LLM 錯誤：{e}")
        return {"accept": False, "reason": "審核失敗"}


# ── LLM 審核例句 ──────────────────────────────────────
def review_sentence_with_llm(word: str, meaning: str, sentence: str) -> dict:
    prompt = f"""你是英文單字教材審核員。請判斷以下例句是否能有效幫助學習者理解單字的意思。

單字：{word}
中文意思：{meaning}
例句：{sentence}

判斷重點：
1. 例句是否「展示」單字的實際用法（讓讀者自然理解其意思）？
2. 還是只是「談論」這個單字的概念，沒有真正示範用法？

❌ 不好的例句類型：
- "The idea of {word} is often misunderstood by beginners."（談論概念，不示範用法）
- "{word} is a common term used in many contexts."（定義式描述）
- "Example: The word '{word}' appears in many sentences."（元描述）
- 任何以「{word} is a/an...」開頭且是在下定義的句子

✅ 好的例句：句子本身自然地使用這個單字，讓讀者能從語境推測其意思。

如果例句不好，請提供一個更好的替代例句。

請回覆 JSON（只回 JSON）：
{{
  "good": true 或 false,
  "reason": "簡短說明（30字內）",
  "new_sentence": "替代例句（如果 good=false 才需要，否則留空字串）"
}}
"""
    try:
        text = _llm_chat(prompt, max_tokens=300).strip()
        if text.startswith("```"):
            text = re.sub(r"```\w*\n?", "", text).strip()
        return json.loads(text)
    except Exception as e:
        print(f"  ⚠️  LLM 錯誤：{e}")
        return {"good": True, "reason": "審核失敗，跳過", "new_sentence": ""}


# ── 主流程 ────────────────────────────────────────────
def main():
    token = login()

    # ── Part A：審核建議定義 ──────────────────────────
    if not SKIP_SUGGEST:
        pending = api_get("/api/words/pending-suggestions", token)
        if not pending:
            print("✅ 沒有待審核的定義建議")
        else:
            print(f"\n📋 找到 {len(pending)} 個定義建議\n")
            accepted = rejected = 0

            for row in pending:
                word       = row["word"]
                current    = row["meaning"]
                suggestion = row["suggested_meaning"]
                print(f"🔍 {word}")
                print(f"   現有：{current}")
                print(f"   建議：{suggestion}")

                result = review_suggestion_with_llm(word, current, suggestion)
                accept = result.get("accept", False)
                reason = result.get("reason", "")

                if accept:
                    print(f"   ✅ 接受 — {reason}")
                    accepted += 1
                else:
                    print(f"   ❌ 拒絕 — {reason}")
                    rejected += 1

                if not DRY_RUN:
                    api_post(f"/api/words/{row['id']}/review-suggestion", token, {
                        "accept": accept,
                        "new_meaning": suggestion if accept else None
                    })

                time.sleep(0.3)

            print(f"\n定義審核：✅ 接受 {accepted}  ❌ 拒絕 {rejected}")

    # ── Part B：審核例句品質 ──────────────────────────
    if not SKIP_SENTENCES:
        sentences = api_get("/api/words/pending-sentences", token,
                            batch_size=BATCH_SIZE, offset=OFFSET)
        if not sentences:
            print("\n✅ 沒有待審核的例句")
        else:
            # 優先審核 regex 初判為 meta 的句子
            flagged = [r for r in sentences if _is_meta_sentence(r["example_sentence"])]
            rest    = [r for r in sentences if not _is_meta_sentence(r["example_sentence"])]
            to_review = (flagged + rest)[:BATCH_SIZE]

            print(f"\n📝 審核例句品質（{len(to_review)} 筆，offset={OFFSET}）\n")
            good_count = replaced = 0

            for row in to_review:
                word     = row["word"]
                meaning  = row["meaning"]
                sentence = row["example_sentence"]

                flagged_mark = "⚠️ " if _is_meta_sentence(sentence) else ""
                print(f"📖 {flagged_mark}{word}")
                print(f"   例句：{sentence}")

                result       = review_sentence_with_llm(word, meaning, sentence)
                is_good      = result.get("good", True)
                reason       = result.get("reason", "")
                new_sentence = result.get("new_sentence", "").strip()

                if is_good:
                    print(f"   ✅ 好 — {reason}")
                    good_count += 1
                else:
                    if new_sentence:
                        print(f"   🔄 替換 — {reason}")
                        print(f"   新例句：{new_sentence}")
                        replaced += 1
                        if not DRY_RUN:
                            api_post(f"/api/words/{row['id']}/review-sentence", token, {
                                "new_sentence": new_sentence
                            })
                    else:
                        print(f"   ⚠️  不佳但無替代句 — {reason}")

                time.sleep(0.3)

            print(f"\n例句審核：✅ 良好 {good_count}  🔄 已替換 {replaced}")
            next_offset = OFFSET + BATCH_SIZE
            print(f"\n下一批：python3 review_suggestions.py --skip-suggestions --offset {next_offset}")

    if DRY_RUN:
        print("\n[DRY RUN] 未寫入任何變更")


if __name__ == "__main__":
    main()
