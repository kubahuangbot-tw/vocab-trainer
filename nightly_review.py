#!/usr/bin/env python3
"""
VocabTrainer — Nightly Review Job
每天 3am 執行，依序做以下任務：

  Step 1  移除投票審核   (純 heuristic，0 token)
  Step 2  Meta 例句偵測  (regex，0 token，自動替換模板)
  Step 3  建議定義審核   (Gemini，批次 10 個/call，有佇列才執行)
  Step 4  例句品質審核   (Gemini，批次 10 個/call，每週日才執行)

環境變數：
  VOCAB_API_BASE    後端網址，預設 http://192.168.1.106:8501
  VOCAB_ADMIN_PASS  管理員密碼（必填）
  GEMINI_API_KEY    Google Gemini API key（必填）

執行：
  python3 nightly_review.py [--dry-run] [--force-sentences]
"""

import sys, json, re, os, time
from datetime import datetime
import requests

DRY_RUN         = "--dry-run"         in sys.argv
FORCE_SENTENCES = "--force-sentences" in sys.argv  # 強制跑例句審核（不管今天是不是週日）

API_BASE       = os.environ.get("VOCAB_API_BASE", "http://192.168.1.106:8501")
ADMIN_USER     = os.environ.get("VOCAB_ADMIN_USER", "admin")
ADMIN_PASS     = os.environ.get("VOCAB_ADMIN_PASS", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCRKOilVyIx7f_Ef94Xfh5_B5Vjl45gLxQ")
GEMINI_MODEL   = "gemini-2.5-flash"

SENTENCE_BATCH = 100   # 每週審核例句數量
LLM_BATCH_SIZE = 10    # 每次 LLM call 合併幾個項目

LOG = []


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG.append(line)


# ── Gemini API ────────────────────────────────────────────────────────────────

def gemini_chat(prompt: str, max_tokens: int = 800) -> str:
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.1}
        },
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def gemini_json(prompt: str, max_tokens: int = 800) -> list | dict:
    text = gemini_chat(prompt, max_tokens)
    if text.startswith("```"):
        text = re.sub(r"```\w*\n?", "", text).strip()
    return json.loads(text)


# ── Backend API helpers ───────────────────────────────────────────────────────

def login() -> str:
    if not ADMIN_PASS:
        print("❌ 請設定 VOCAB_ADMIN_PASS 環境變數")
        sys.exit(1)
    resp = requests.post(
        f"{API_BASE}/api/auth/login",
        data={"username": ADMIN_USER, "password": ADMIN_PASS},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def api_get(path: str, token: str, **params):
    resp = requests.get(f"{API_BASE}{path}",
                        headers={"Authorization": f"Bearer {token}"},
                        params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, token: str, body: dict):
    if DRY_RUN:
        return {}
    resp = requests.post(f"{API_BASE}{path}",
                         headers={"Authorization": f"Bearer {token}"},
                         json=body, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ── Step 1: Removal vote heuristic (0 token) ─────────────────────────────────

BRANDS = {"toyota","honda","benz","mercedes","bmw","nintendo","sony","samsung",
          "apple","google","microsoft","amazon","facebook","twitter","instagram",
          "pepsi","coca-cola","starbucks","mcdonald","ikea","nike","adidas"}
ABBREVIATIONS = {"nhs","lcd","cpu","gpu","dna","rna","usa","uk","eu","un",
                 "nato","who","imf","gdp","gop"}
OBSOLETE = {"epinions","friendster","myspace","digg","netscape"}


def heuristic_classify(word: str, meaning: str):
    w = word.lower()
    if w in BRANDS:       return "delete", f"品牌名稱"
    if w in ABBREVIATIONS: return "delete", f"縮寫/簡稱"
    if w in OBSOLETE:      return "delete", f"已消失的網站/服務"
    if len(meaning) <= 4 and not any(c in meaning for c in "的是一種"):
        return "review", "meaning 過短，可能是音譯人名"
    return "keep", "無明顯問題"


def step1_removal_votes(token: str):
    log("── Step 1: 移除投票審核（heuristic）──")
    try:
        flagged = api_get("/api/words/removal-votes", token)
    except Exception as e:
        log(f"  ⚠️  無法取得投票列表：{e}")
        return 0

    if not flagged:
        log("  ✅ 無待審核移除投票")
        return 0

    deleted = 0
    for w in flagged:
        action, reason = heuristic_classify(w["word"], w["meaning"])
        if action == "delete":
            log(f"  🗑  {w['word']} — {reason}（票數 {w.get('removal_vote_count',0)}）")
            api_post(f"/api/words/{w['id']}/delete", token, {})
            deleted += 1
        else:
            log(f"  ⏭  {w['word']} — {reason}，保留")

    log(f"  結果：刪除 {deleted} / 保留 {len(flagged)-deleted}")
    return deleted


# ── Step 2: Meta sentence regex (0 token) ────────────────────────────────────

_META_RE = re.compile(
    r"the\s+(idea|concept|notion|term|word|use|usage)\s+of\s+\w+"
    r"|is\s+(a|an)\s+(common|important|key|useful|basic)\s+(word|term|concept)"
    r"|the\s+word\s+['\"]?\w+['\"]?\s+is\s+used"
    r"|beginners\s+(often|sometimes|frequently)"
    r"|is\s+used\s+in\s+many\s+contexts",
    re.IGNORECASE
)


def step2_meta_sentences(token: str):
    log("── Step 2: Meta 例句偵測（regex）──")
    try:
        rows = api_get("/api/words/pending-sentences", token, batch_size=500, offset=0)
    except Exception as e:
        log(f"  ⚠️  無法取得例句列表：{e}")
        return 0

    flagged = [r for r in rows if _META_RE.search(r.get("example_sentence", ""))]
    if not flagged:
        log(f"  ✅ 無 meta 例句（掃描 {len(rows)} 筆）")
        return 0

    log(f"  🔍 發現 {len(flagged)} 筆 meta 例句，送 LLM 替換")
    replaced = 0

    for i in range(0, len(flagged), LLM_BATCH_SIZE):
        batch = flagged[i:i + LLM_BATCH_SIZE]
        items_json = json.dumps([
            {"id": r["id"], "word": r["word"],
             "meaning": r["meaning"], "sentence": r["example_sentence"]}
            for r in batch
        ], ensure_ascii=False)

        prompt = f"""以下例句屬於「meta 型」（只描述單字概念，而非示範實際用法），請為每個提供更好的例句。

{items_json}

規則：
- 好的例句：句子自然地使用這個單字，讓讀者能從語境推測意思
- 不要用「The word X is...」或「X is a common term...」等描述式開頭
- 例句長度：10-20 個英文單字

只回傳 JSON array，每項格式：{{"id": ..., "new_sentence": "..."}}
不要加其他文字。"""

        try:
            results = gemini_json(prompt, max_tokens=600)
            for item in results:
                api_post(f"/api/words/{item['id']}/review-sentence", token,
                         {"new_sentence": item["new_sentence"]})
                log(f"  🔄 {item['id']} → {item['new_sentence'][:60]}")
                replaced += 1
            time.sleep(0.5)
        except Exception as e:
            log(f"  ⚠️  LLM 替換失敗：{e}")

    log(f"  結果：替換 {replaced} 筆 meta 例句")
    return replaced


# ── Step 3: Suggested meaning review (LLM, batched) ──────────────────────────

def step3_suggested_meanings(token: str):
    log("── Step 3: 建議定義審核（Gemini 批次）──")
    try:
        pending = api_get("/api/words/pending-suggestions", token)
    except Exception as e:
        log(f"  ⚠️  無法取得建議列表：{e}")
        return 0

    if not pending:
        log("  ✅ 無待審核定義建議")
        return 0

    log(f"  📋 找到 {len(pending)} 個建議，批次審核中…")
    accepted = rejected = 0

    for i in range(0, len(pending), LLM_BATCH_SIZE):
        batch = pending[i:i + LLM_BATCH_SIZE]
        items_json = json.dumps([
            {"id": r["id"], "word": r["word"],
             "current": r["meaning"], "suggestion": r["suggested_meaning"]}
            for r in batch
        ], ensure_ascii=False)

        prompt = f"""你是英文單字審核員。請判斷每個建議定義是否比現有定義更準確、更易懂。

{items_json}

判斷標準：
- 翻譯是否正確？
- 是否比現有定義更簡潔易懂？
- 是否有不雅或錯誤內容？

只回傳 JSON array，每項格式：{{"id": ..., "accept": true/false, "reason": "20字內"}}
不要加其他文字。"""

        try:
            results = gemini_json(prompt, max_tokens=500)
            for item in results:
                accept = item.get("accept", False)
                reason = item.get("reason", "")
                word_id = item["id"]
                row = next((r for r in batch if r["id"] == word_id), {})
                symbol = "✅" if accept else "❌"
                log(f"  {symbol} {row.get('word','?')} — {reason}")
                api_post(f"/api/words/{word_id}/review-suggestion", token, {
                    "accept": accept,
                    "new_meaning": row.get("suggested_meaning") if accept else None
                })
                if accept: accepted += 1
                else: rejected += 1
            time.sleep(0.5)
        except Exception as e:
            log(f"  ⚠️  LLM 審核失敗：{e}")

    log(f"  結果：接受 {accepted}  拒絕 {rejected}")
    return accepted + rejected


# ── Step 4: Sentence quality review (weekly, LLM batched) ─────────────────────

def step4_sentence_quality(token: str):
    today = datetime.now().weekday()  # 0=Monday, 6=Sunday
    if today != 6 and not FORCE_SENTENCES:
        log("── Step 4: 例句品質審核（跳過，非週日）──")
        return 0

    log(f"── Step 4: 例句品質審核（Gemini 批次，{SENTENCE_BATCH} 筆）──")
    try:
        rows = api_get("/api/words/pending-sentences", token,
                       batch_size=SENTENCE_BATCH, offset=0)
    except Exception as e:
        log(f"  ⚠️  無法取得例句列表：{e}")
        return 0

    # 已由 Step 2 處理過 meta 句，這裡跳過 regex 命中的（避免重複）
    to_review = [r for r in rows if not _META_RE.search(r.get("example_sentence", ""))]
    if not to_review:
        log("  ✅ 無待審核例句")
        return 0

    log(f"  📝 審核 {len(to_review)} 筆例句…")
    replaced = 0

    for i in range(0, len(to_review), LLM_BATCH_SIZE):
        batch = to_review[i:i + LLM_BATCH_SIZE]
        items_json = json.dumps([
            {"id": r["id"], "word": r["word"],
             "meaning": r["meaning"], "sentence": r["example_sentence"]}
            for r in batch
        ], ensure_ascii=False)

        prompt = f"""你是英文教材審核員。請判斷每個例句是否能有效幫助學習者理解單字意思。

{items_json}

評分標準：
- good=true：例句自然地示範單字用法，語境清楚
- good=false：例句只是描述概念、定義式、或語境不清楚
- 若 good=false，提供替代例句（10-20 個英文單字）

只回傳 JSON array，每項格式：
{{"id": ..., "good": true/false, "new_sentence": "若 good=false 才填，否則空字串"}}
不要加其他文字。"""

        try:
            results = gemini_json(prompt, max_tokens=800)
            for item in results:
                if not item.get("good") and item.get("new_sentence"):
                    row = next((r for r in batch if r["id"] == item["id"]), {})
                    log(f"  🔄 {row.get('word','?')} → {item['new_sentence'][:60]}")
                    api_post(f"/api/words/{item['id']}/review-sentence", token,
                             {"new_sentence": item["new_sentence"]})
                    replaced += 1
            time.sleep(0.5)
        except Exception as e:
            log(f"  ⚠️  LLM 審核失敗：{e}")

    log(f"  結果：替換 {replaced} 筆例句")
    return replaced


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log(f"=== VocabTrainer Nightly Review {'[DRY RUN] ' if DRY_RUN else ''}===")
    log(f"    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    token = login()

    d1 = step1_removal_votes(token)
    d2 = step2_meta_sentences(token)
    d3 = step3_suggested_meanings(token)
    d4 = step4_sentence_quality(token)

    total = d1 + d2 + d3 + d4
    log(f"\n=== 完成：共處理 {total} 項 ===")
    if DRY_RUN:
        log("[DRY RUN] 未寫入任何變更")


if __name__ == "__main__":
    main()
