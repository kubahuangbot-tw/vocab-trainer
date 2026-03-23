"""
匯入單字庫 - 從網路取得單字定義
"""
import requests
import json
import time

def get_definition(word):
    """從 Free Dictionary API 取得單字定義"""
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        resp = requests.get(url, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            if data and 'meanings' in data[0]:
                # 取第一個意思
                meanings = data[0]['meanings']
                if meanings:
                    definition = meanings[0]['definitions'][0]['definition']
                    # 取得詞性
                    part_of_speech = meanings[0].get('partOfSpeech', 'unknown')
                    return {
                        'definition': definition,
                        'part_of_speech': part_of_speech
                    }
        return None
    except:
        return None

def import_words(words, level=2):
    """匯入單字到 word_list.py"""
    from word_list import WORD_LIST, add_word
    
    imported = []
    failed = []
    
    for i, word in enumerate(words):
        print(f"[{i+1}/{len(words)}] 處理: {word}")
        
        # 檢查是否已有
        if word.lower() in WORD_LIST:
            print(f"  → 已存在，跳過")
            continue
        
        # 取得定義
        result = get_definition(word)
        
        if result:
            add_word(word.lower(), result['definition'], level)
            imported.append(word)
            print(f"  → ✅ {result['part_of_speech']}: {result['definition'][:50]}...")
        else:
            failed.append(word)
            print(f"  → ❌ 無法取得定義")
        
        # 避免太快
        time.sleep(0.3)
    
    print(f"\n=== 匯入結果 ===")
    print(f"成功: {len(imported)}")
    print(f"失敗: {len(failed)}")
    
    return imported, failed

# 測試
if __name__ == "__main__":
    # 測試單字
    test_words = ["hello", "world", "computer", "python", "algorithm"]
    
    print("測試取得定義...")
    for w in test_words:
        result = get_definition(w)
        if result:
            print(f"{w}: [{result['part_of_speech']}] {result['definition']}")
        else:
            print(f"{w}: ❌ 無定義")
        time.sleep(0.5)