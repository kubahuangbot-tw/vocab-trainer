"""
單字庫 - 從 JSON 檔案載入
"""
import json
import os

# 預設路徑
WORDS_FILE = os.path.join(os.path.dirname(__file__), 'words.json')

def load_words():
    """從 JSON 檔案載入單字"""
    if os.path.exists(WORDS_FILE):
        with open(WORDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_words(words):
    """儲存單字到 JSON 檔案"""
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

# 單字庫
WORD_LIST = load_words()

def add_word(word, meaning, level=3):
    """新增單字"""
    WORD_LIST[word.lower()] = {
        'meaning': meaning,
        'level': level
    }
    save_words(WORD_LIST)

def get_word(word):
    """取得單字資訊"""
    return WORD_LIST.get(word.lower())

# 匯出常用函式
__all__ = ['WORD_LIST', 'add_word', 'get_word', 'load_words', 'save_words']