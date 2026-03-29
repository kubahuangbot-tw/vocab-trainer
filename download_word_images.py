#!/usr/bin/env python3
"""
單字圖片下載器 v2
搜尋順序：Wikimedia Commons → Pixabay（fallback）
1. 從 NAS 拉最新 vocab.db 到 local
2. 對每個缺圖的單字，先試 Wikimedia，再試 Pixabay
3. 下載並 resize 到 400px 寬，存到 data/word_images/{word}.jpg
4. 更新 DB image_path，同步到 NAS

執行方式：
  python3 download_word_images.py           # 全部跑（只補沒有圖的字）
  python3 download_word_images.py --test 10 # 只跑前 10 個測試
"""

import sqlite3, os, sys, time, logging, subprocess, requests, argparse
from pathlib import Path
from PIL import Image
from io import BytesIO

# ── 設定 ──────────────────────────────────────────────
NAS_HOST    = "kubabot@192.168.1.109"
NAS_SSH_KEY = Path.home() / ".ssh" / "nas_key"
NAS_DB_PATH = "/volume1/botfoler/vocabtrainer_v3/data/vocab.db"

BASE_DIR    = Path(__file__).parent
LOCAL_DB    = BASE_DIR / "data" / "vocab.db"
IMAGE_DIR   = BASE_DIR / "data" / "word_images"
LOG_FILE    = BASE_DIR / "data" / "download_images.log"

IMAGE_WIDTH  = 400
SLEEP_SEC    = 0.3

PIXABAY_KEY = "55213355-c13688f3cfacec0808b20ba40"
PEXELS_KEY  = "lIBhGAB004nemVlgJkvgj8g9y0rKG9hwVFY9kIXIPWVPDRl0K6436G0p"

HEADERS = {
    'User-Agent': 'VocabTrainer/1.0 (educational project; private use)'
}

# ── logging ───────────────────────────────────────────
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)

# ── Step 1：從 NAS 拉最新 DB ──────────────────────────
def pull_db_from_nas():
    log.info("📥 從 NAS 拉取最新 vocab.db ...")
    cmd = [
        "scp", "-i", str(NAS_SSH_KEY),
        "-o", "StrictHostKeyChecking=no",
        f"{NAS_HOST}:{NAS_DB_PATH}",
        str(LOCAL_DB)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"SCP 失敗: {result.stderr}")
        sys.exit(1)
    size_mb = LOCAL_DB.stat().st_size / 1024 / 1024
    log.info(f"✅ DB 已更新：{LOCAL_DB} ({size_mb:.1f} MB)")

# ── Step 2：讀取單字清單 ──────────────────────────────
def load_words(limit=None):
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    sql = "SELECT id, word, word_type FROM words ORDER BY difficulty, word"
    if limit:
        sql += f" LIMIT {limit}"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return rows

# ── Step 3a：Wikimedia Commons 搜尋 ───────────────────
def search_wikimedia(word, word_type):
    wt = (word_type or '').lower()
    if wt in ('verb', 'v', 'vt', 'vi'):
        query = f"{word}ing"
    elif wt in ('adjective', 'adj'):
        query = f"{word} illustration"
    else:
        query = word

    try:
        r = requests.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "list": "search",
            "srsearch": f"{query} photo",
            "srnamespace": "6",
            "srlimit": "8",
            "format": "json"
        }, headers=HEADERS, timeout=8)
        results = r.json().get("query", {}).get("search", [])
        if not results:
            return None

        for result in results:
            title = result["title"]
            r2 = requests.get("https://commons.wikimedia.org/w/api.php", params={
                "action": "query", "titles": title,
                "prop": "imageinfo", "iiprop": "url|mediatype",
                "iiurlwidth": str(IMAGE_WIDTH),
                "format": "json"
            }, headers=HEADERS, timeout=8)
            pages = r2.json().get("query", {}).get("pages", {})
            page = next(iter(pages.values()), {})
            info = page.get("imageinfo", [{}])[0]
            thumb = info.get("thumburl")
            media = info.get("mediatype", "")
            if thumb and media in ("BITMAP", ""):
                return thumb
            time.sleep(0.1)
    except Exception:
        pass
    return None

# ── Step 3b：Pixabay 搜尋（fallback 1）───────────────
def search_pixabay(word):
    try:
        r = requests.get("https://pixabay.com/api/", params={
            "key": PIXABAY_KEY,
            "q": word,
            "image_type": "photo",
            "safesearch": "true",
            "per_page": 3,
            "min_width": 300,
        }, timeout=8)
        hits = r.json().get("hits", [])
        if hits:
            return hits[0].get("webformatURL")
    except Exception:
        pass
    return None

# ── Step 3c：Pexels 搜尋（fallback 2）────────────────
def search_pexels(word):
    try:
        r = requests.get("https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_KEY},
            params={"query": word, "per_page": 3},
            timeout=8)
        photos = r.json().get("photos", [])
        if photos:
            return photos[0]["src"]["medium"]
    except Exception:
        pass
    return None

# ── Step 4：下載並儲存 ────────────────────────────────
def download_and_save(url, save_path):
    resp = requests.get(url, headers=HEADERS, timeout=12)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content)).convert('RGB')
    w, h = img.size
    new_h = max(1, int(h * IMAGE_WIDTH / w))
    img = img.resize((IMAGE_WIDTH, new_h), Image.LANCZOS)
    img.save(save_path, 'JPEG', quality=85)

# ── Step 5：更新 DB image_path ────────────────────────
def update_db_image_paths():
    conn = sqlite3.connect(LOCAL_DB)
    cur = conn.cursor()
    files = list(IMAGE_DIR.glob('*.jpg'))
    updated = 0
    for f in files:
        word = f.stem.replace('_', ' ')
        cur.execute('UPDATE words SET image_path=? WHERE LOWER(word)=LOWER(?)', (str(f), word))
        if cur.rowcount > 0:
            updated += 1
    conn.commit()
    conn.close()
    return updated

# ── Step 6：同步到 NAS ────────────────────────────────
def sync_to_nas():
    log.info("📤 同步 DB 到 NAS ...")
    with open(LOCAL_DB, 'rb') as f:
        data = f.read()
    result = subprocess.run(
        ["ssh", "-i", str(NAS_SSH_KEY), "-o", "StrictHostKeyChecking=no",
         NAS_HOST, f"cat > {NAS_DB_PATH}"],
        input=data, capture_output=True
    )
    if result.returncode == 0:
        log.info("✅ DB 同步完成")
    else:
        log.error(f"DB 同步失敗: {result.stderr.decode()}")

# ── 主流程 ────────────────────────────────────────────
def run(test_limit=None):
    if not test_limit:
        pull_db_from_nas()
    else:
        log.info(f"🧪 測試模式：只跑前 {test_limit} 個單字（不拉 NAS DB）")

    words = load_words(limit=test_limit)
    total   = len(words)
    done    = 0
    skipped = 0
    wiki_ok = 0
    pixabay_ok = 0
    pexels_ok  = 0
    failed  = 0
    failed_words = []

    log.info(f"📚 共 {total} 個單字，開始下載圖片到 {IMAGE_DIR} ...")

    for i, row in enumerate(words):
        word = row['word'].lower().strip()
        safe = word.replace(' ', '_').replace('/', '_').replace('\\', '_')
        save_path = IMAGE_DIR / f"{safe}.jpg"

        # 斷點續傳
        if save_path.exists() and save_path.stat().st_size > 1024:
            skipped += 1
            continue

        source = None
        try:
            # 1st: Wikimedia
            url = search_wikimedia(word, row['word_type'])
            if url:
                source = 'wiki'
            else:
                # 2nd: Pixabay fallback
                url = search_pixabay(word)
                if url:
                    source = 'pixabay'
                else:
                    # 3rd: Pexels fallback
                    url = search_pexels(word)
                    if url:
                        source = 'pexels'

            if not url:
                raise ValueError("所有來源均找不到圖片")

            download_and_save(url, save_path)
            done += 1
            if source == 'wiki':
                wiki_ok += 1
            elif source == 'pixabay':
                pixabay_ok += 1
            else:
                pexels_ok += 1

            if done % 50 == 0 or test_limit:
                log.info(f"  [{i+1}/{total}] ✅ {word} [{source}] ({save_path.stat().st_size//1024}KB)")
        except Exception as e:
            failed += 1
            failed_words.append(f"{word}: {e}")
            if test_limit:
                log.warning(f"  [{i+1}/{total}] ❌ {word}: {e}")

        time.sleep(SLEEP_SEC)

    # ── 更新 DB & 同步 NAS ────────────────────────────
    if not test_limit:
        updated = update_db_image_paths()
        log.info(f"🗄️  DB 更新 {updated} 筆 image_path")
        sync_to_nas()

    # ── 摘要 ──────────────────────────────────────────
    summary = (
        f"\n{'='*55}\n"
        f"🖼️  單字圖片下載完成！\n"
        f"  ✅ 成功下載: {done} (Wiki:{wiki_ok} / Pixabay:{pixabay_ok} / Pexels:{pexels_ok})\n"
        f"  ⏭️  跳過(已存在): {skipped}\n"
        f"  ❌ 失敗: {failed}\n"
        f"  📁 儲存路徑: {IMAGE_DIR}\n"
        f"{'='*55}"
    )
    log.info(summary)

    if failed_words:
        fail_log = IMAGE_DIR / "failed.txt"
        fail_log.write_text('\n'.join(failed_words), encoding='utf-8')
        log.info(f"  失敗清單: {fail_log}")

    return done, skipped, failed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', type=int, help='只跑前N個單字（測試用）')
    args = parser.parse_args()
    run(test_limit=args.test)
