#!/usr/bin/env python3
"""批次翻譯單字定義為中文 - 穩定版"""
import json
import time
import requests

WORDS_FILE = 'words.json'

def translate(text):
    """翻譯成中文"""
    try:
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text[:80])}&langpair=en|zh-TW"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get('responseData', {}).get('translatedText', '')
            if result and result != text:  # 確保有翻譯
                return result[:100]
    except Exception as e:
        print(f"Error: {e}")
    return ''

def main():
    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        words = json.load(f)
    
    # 找出需要翻譯的 (目前是英文)
    need_translate = []
    for w, info in words.items():
        meaning = info.get('meaning', '')
        if meaning and not any('\u4e00' <= c <= '\u9fff' for c in meaning):
            need_translate.append((w, info))
    
    total = len(need_translate)
    print(f"需要翻譯: {total} 個")
    
    translated = 0
    failed = 0
    
    for i, (w, info) in enumerate(need_translate):
        result = translate(info['meaning'])
        
        if result:
            info['meaning'] = result
            translated += 1
        else:
            failed += 1
        
        # 每 50 個存檔並顯示進度
        if (i + 1) % 50 == 0:
            with open(WORDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(words, f, ensure_ascii=False, indent=2)
            print(f"進度: {i+1}/{total} (成功: {translated}, 失敗: {failed})")
        
        time.sleep(0.3)  # 避免太快
    
    # 最後存檔
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    
    print(f"完成! 成功: {translated}, 失敗: {failed}")

if __name__ == '__main__':
    main()