#!/usr/bin/env python3
"""使用 Google Translate API 翻譯"""
import json
import time
import urllib.request
import urllib.parse

WORDS_FILE = 'words.json'

def translate(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-TW&dt=t&q={urllib.parse.quote(text[:100])}"
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if data[0] and data[0][0]:
            return data[0][0][0][:100]
    except Exception as e:
        print(f"Error: {e}")
    return ''

def main():
    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        words = json.load(f)
    
    # 找出需要翻譯的
    need_translate = [(w, info) for w, info in words.items() if info.get('meaning', '') and not any('\u4e00' <= c <= '\u9fff' for c in info['meaning'])]
    
    total = len(need_translate)
    print(f"需要翻譯: {total} 個")
    
    translated = 0
    for i, (w, info) in enumerate(need_translate):
        result = translate(info['meaning'])
        if result:
            info['meaning'] = result
            translated += 1
        
        if (i + 1) % 100 == 0:
            with open(WORDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(words, f, ensure_ascii=False, indent=2)
            print(f"進度: {i+1}/{total}")
        
        time.sleep(0.1)  # 避免太頻繁
    
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    
    print(f"完成! 翻譯了 {translated} 個")

if __name__ == '__main__':
    main()