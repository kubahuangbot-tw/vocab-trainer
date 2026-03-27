"""單字庫審查腳本 - 輔助 sub-agent"""
import json
import os

WORDS_FILE = "words_review.json"

def load_words():
    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_words(words):
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

def get_chinese_words():
    """取得需要審查的中文單字"""
    words = load_words()
    chinese = {w: d for w, d in words.items() 
              if d.get('meaning', '') and any('\u4e00' <= c <= '\u9fff' for c in d['meaning'])}
    return chinese

def update_word(word, meaning, level=None, word_type=None):
    """更新單字"""
    words = load_words()
    if word in words:
        words[word]['meaning'] = meaning
        if level:
            words[word]['level'] = level
        if word_type:
            words[word]['type'] = word_type
        save_words(words)
        return True
    return False

def get_progress():
    """取得審查進度"""
    words = load_words()
    total = len(words)
    chinese = sum(1 for w, d in words.items() 
                if d.get('meaning', '') and any('\u4e00' <= c <= '\u9fff' for c in d['meaning']))
    reviewed = sum(1 for w, d in words.items() 
                  if d.get('meaning', '') and any('\u4e00' <= c <= '\u9fff' for c in d['meaning'])
                  and d.get('reviewed', False))
    return total, chinese, reviewed

if __name__ == "__main__":
    total, chinese, reviewed = get_progress()
    print(f"總單字: {total}")
    print(f"中文: {chinese}")
    print(f"已審查: {reviewed}")
