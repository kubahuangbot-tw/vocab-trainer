#!/usr/bin/env python3
"""批次翻譯所有剩餘單字"""
import json, urllib.request, urllib.parse, time, sys

WORDS_FILE = 'words.json'

def translate(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-TW&dt=t&q={urllib.parse.quote(text[:80])}"
        resp = urllib.request.urlopen(url, timeout=8)
        data = json.loads(resp.read())
        if data[0] and data[0][0]:
            return data[0][0][0][:100]
    except:
        return ''
    return ''

# 讀取
with open(WORDS_FILE, 'r', encoding='utf-8') as f:
    words = json.load(f)

# 找出需要翻譯的
to_translate = []
for word, info in words.items():
    meaning = info.get('meaning', '')
    if meaning.strip() and not any('\u4e00' <= c <= '\u9fff' for c in meaning):
        to_translate.append((word, info))
    elif not meaning.strip():
        to_translate.append((word, info))

total = len(to_translate)
print(f"需要翻譯: {total} 個")

# 批次翻譯
translated = 0
for i, (word, info) in enumerate(to_translate):
    if not info.get('meaning', '').strip():
        # 無定義的嘗試用單字本身當作翻譯
        # 這裡我們先跳過，讓用戶手動新增
        continue
    
    result = translate(info['meaning'])
    if result:
        info['meaning'] = result
        translated += 1
    
    # 每 100 個存檔並顯示進度
    if (i + 1) % 100 == 0:
        with open(WORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(words, f, ensure_ascii=False, indent=2)
        chinese = sum(1 for w, i in words.items() if i.get('meaning', '').strip() and any('\u4e00' <= c <= '\u9fff' for c in i['meaning']))
        print(f"進度: {i+1}/{total}, 中文: {chinese}")
    
    time.sleep(0.08)

# 最後存檔
with open(WORDS_FILE, 'w', encoding='utf-8') as f:
    json.dump(words, f, ensure_ascii=False, indent=2)

chinese = sum(1 for w, i in words.items() if i.get('meaning', '').strip() and any('\u4e00' <= c <= '\u9fff' for c in i['meaning']))
print(f"完成! 翻譯: {translated} 個, 總中文: {chinese}")