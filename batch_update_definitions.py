#!/usr/bin/env python3
"""
批次補完單字定義 - 多線程版本
"""
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

WORDS_FILE = 'words.json'
LOG_FILE = 'batch_update.log'
MAX_WORKERS = 5  # 同時執行緒數
DELAY = 0.5  # 最小間隔

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def fetch_definition(word):
    """查詢單字定義"""
    try:
        resp = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data and 'meanings' in data[0]:
                meaning = data[0]['meanings'][0]['definitions'][0]['definition']
                part = data[0]['meanings'][0].get('partOfSpeech', '')
                return word, meaning[:100], part
    except:
        pass
    return word, None, None

def main():
    log("=== 批次更新開始 (多線程) ===")
    
    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        words = json.load(f)
    
    # 找出沒有定義的單字
    no_def_words = [w for w, info in words.items() if not info.get('meaning', '').strip()]
    total = len(no_def_words)
    
    log(f"總共有 {total} 個單字沒有定義")
    
    updated = 0
    failed = 0
    
    # 使用執行緒池
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_definition, word): word for word in no_def_words}
        
        for i, future in enumerate(as_completed(futures)):
            word, meaning, part = future.result()
            
            if meaning:
                words[word]['meaning'] = meaning
                if part:
                    words[word]['type'] = part
                updated += 1
            else:
                failed += 1
            
            # 每 50 個輸出進度
            if (i + 1) % 50 == 0:
                log(f"進度: {i+1}/{total} (更新: {updated}, 失敗: {failed})")
            
            # 每 100 個存檔
            if (i + 1) % 100 == 0:
                with open(WORDS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(words, f, ensure_ascii=False, indent=2)
                log(f"已儲存進度")
            
            time.sleep(DELAY)
    
    # 最後存檔
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    
    log(f"=== 完成 ===")
    log(f"更新: {updated} 個, 失敗: {failed} 個")

if __name__ == '__main__':
    main()