#!/usr/bin/env python3
"""
單字庫管理工具 (VocabManager)
=========================
用途：維護單字庫資料

功能：
1. 從 API 查詢單字並新增
2. 批次翻譯現有單字
3. 匯入/匯出單字
4. 查詢/修改單字
5. 統計分析

使用方式：
    python3 vocab_manager.py add <單字>           # 新增單字
    python3 vocab_manager.py translate            # 翻譯所有英文定義
    python3 vocab_manager.py status             # 查看統計
    python3 vocab_manager.py list              # 列出所有單字
    python3 vocab_manager.py export <檔案>      # 匯出 CSV
    python3 vocab_manager.py import <檔案>      # 匯入 CSV
"""

import json
import sys
import os
import time
import urllib.request
import urllib.parse
import requests
from datetime import datetime

# 設定
WORDS_FILE = 'words.json'
BACKUP_FILE = 'words_backup.json'

# ========== 翻譯服務 ==========
class TranslationService:
    """翻譯服務基底類"""
    def translate(self, text, source='en', target='zh-TW'):
        raise NotImplementedError

class GoogleTranslate(TranslationService):
    """Google Translate API (非官方)"""
    def translate(self, text, source='en', target='zh-TW'):
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source}&tl={target}&dt=t&q={urllib.parse.quote(text[:80])}"
            data = json.loads(urllib.request.urlopen(url, timeout=5).read())
            if data[0] and data[0][0]:
                return data[0][0][0][:100]
        except Exception as e:
            print(f"翻譯錯誤: {e}")
        return None

class MyMemoryTranslate(TranslationService):
    """MyMemory API (需要 API key 才能提高額度)"""
    def __init__(self, api_key=None):
        self.api_key = api_key
    
    def translate(self, text, source='en', target='zh-TW'):
        try:
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={source}|{target}"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            return data.get('responseData', {}).get('translatedText', '')[:100]
        except:
            return None

# ========== 單字庫管理 ==========
class VocabManager:
    def __init__(self, words_file=WORDS_FILE):
        self.words_file = words_file
        self.translator = GoogleTranslate()
        self._load()
    
    def _load(self):
        """載入單字庫"""
        if os.path.exists(self.words_file):
            with open(self.words_file, 'r', encoding='utf-8') as f:
                self.words = json.load(f)
        else:
            self.words = {}
    
    def save(self):
        """儲存單字庫"""
        with open(self.words_file, 'w', encoding='utf-8') as f:
            json.dump(self.words, f, ensure_ascii=False, indent=2)
    
    def backup(self):
        """備份單字庫"""
        if os.path.exists(self.words_file):
            with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.words, f, ensure_ascii=False, indent=2)
            print(f"✅ 已備份到 {BACKUP_FILE}")
    
    def add_word(self, word, meaning=None, level=3, translate=False):
        """新增單字"""
        word = word.lower().strip()
        if not word:
            return False, "單字不能為空"
        
        # 如果沒有 meaning，嘗試翻譯
        if translate and not meaning:
            meaning = self.translator.translate(word)
            if meaning:
                print(f"  → 翻譯: {meaning}")
        
        if meaning:
            # 檢查是否為中文
            is_chinese = any('\u4e00' <= c <= '\u9fff' for c in meaning)
            
            self.words[word] = {
                'meaning': meaning,
                'level': level,
                'type': '',
                'updated': datetime.now().isoformat()
            }
            status = "🟢 中文" if is_chinese else "🔵 英文"
            return True, f"新增 {word}: {meaning} ({status})"
        else:
            return False, "需要提供 meaning 或啟用翻譯"
    
    def update_word(self, word, meaning=None, level=None):
        """更新單字"""
        word = word.lower()
        if word not in self.words:
            return False, f"單字 {word} 不存在"
        
        if meaning:
            self.words[word]['meaning'] = meaning
        if level:
            self.words[word]['level'] = level
        
        self.words[word]['updated'] = datetime.now().isoformat()
        return True, f"更新 {word} 成功"
    
    def delete_word(self, word):
        """刪除單字"""
        word = word.lower()
        if word in self.words:
            del self.words[word]
            return True, f"刪除 {word}"
        return False, f"單字 {word} 不存在"
    
    def get_word(self, word):
        """取得單字"""
        return self.words.get(word.lower())
    
    def translate_all(self, limit=None):
        """翻譯所有英文定義"""
        english_words = []
        for word, info in self.words.items():
            meaning = info.get('meaning', '')
            if meaning.strip() and not any('\u4e00' <= c <= '\u9fff' for c in meaning):
                english_words.append((word, info))
        
        total = len(english_words)
        if limit:
            english_words = english_words[:limit]
        
        print(f"翻譯中: {len(english_words)} / {total} 個...")
        
        translated = 0
        for i, (word, info) in enumerate(english_words):
            result = self.translator.translate(info['meaning'])
            if result:
                info['meaning'] = result
                info['updated'] = datetime.now().isoformat()
                translated += 1
            
            if (i + 1) % 50 == 0:
                print(f"  進度: {i+1}/{len(english_words)}")
            
            time.sleep(0.1)
        
        print(f"翻譯完成! ({translated}/{len(english_words)})")
        return translated
    
    def stats(self):
        """統計"""
        total = len(self.words)
        with_chinese = sum(1 for i in self.words.values() 
                         if i.get('meaning', '').strip() and any('\u4e00' <= c <= '\u9fff' for c in i['meaning']))
        with_english = sum(1 for i in self.words.values() 
                         if i.get('meaning', '').strip() and not any('\u4e00' <= c <= '\u9fff' for c in i['meaning']))
        no_meaning = total - with_chinese - with_english
        
        # 等級分布
        levels = {}
        for info in self.words.values():
            l = info.get('level', 3)
            levels[l] = levels.get(l, 0) + 1
        
        print(f"\n{'='*40}")
        print(f"單字庫統計")
        print(f"{'='*40}")
        print(f"總單字: {total}")
        print(f"✅ 中文定義: {with_chinese}")
        print(f"🔵 英文定義: {with_english}")
        print(f"⚫ 無定義: {no_meaning}")
        print(f"\n等級分布:")
        for l in sorted(levels.keys()):
            print(f"  Level {l}: {levels[l]}")
    
    def list_words(self, limit=20):
        """列出單字"""
        for i, (word, info) in enumerate(list(self.words.items())[:limit]):
            meaning = info.get('meaning', '')[:30]
            level = info.get('level', 3)
            is_cn = "🟢" if any('\u4e00' <= c <= '\u9fff' for c in meaning) else "🔵"
            print(f"{i+1}. {word} (L{level}) {is_cn} {meaning}")
        
        if len(self.words) > limit:
            print(f"... 還有 {len(self.words) - limit} 個")
    
    def export_csv(self, filename):
        """匯出 CSV"""
        import csv
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['word', 'meaning', 'level', 'type'])
            for word, info in self.words.items():
                writer.writerow([
                    word, 
                    info.get('meaning', ''),
                    info.get('level', 3),
                    info.get('type', '')
                ])
        print(f"✅ 已匯出到 {filename}")
    
    def import_csv(self, filename):
        """匯入 CSV"""
        import csv
        added = 0
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row.get('word', '').strip().lower()
                if word:
                    self.words[word] = {
                        'meaning': row.get('meaning', ''),
                        'level': int(row.get('level', 3)),
                        'type': row.get('type', '')
                    }
                    added += 1
        print(f"✅ 已匯入 {added} 個單字")

# ========== 主程式 ==========
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    vm = VocabManager()
    
    if cmd == 'add':
        if len(sys.argv) < 3:
            print("用法: python3 vocab_manager.py add <單字> [meaning]")
            sys.exit(1)
        
        word = sys.argv[2]
        meaning = sys.argv[3] if len(sys.argv) > 3 else None
        translate = '--translate' in sys.argv
        
        success, msg = vm.add_word(word, meaning, translate=translate)
        if success:
            vm.save()
            print(f"✅ {msg}")
        else:
            print(f"❌ {msg}")
    
    elif cmd == 'translate':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        vm.backup()
        vm.translate_all(limit)
        vm.save()
        vm.stats()
    
    elif cmd == 'status':
        vm.stats()
    
    elif cmd == 'list':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        vm.list_words(limit)
    
    elif cmd == 'export':
        if len(sys.argv) < 3:
            print("用法: python3 vocab_manager.py export <檔名>")
            sys.exit(1)
        vm.export_csv(sys.argv[2])
    
    elif cmd == 'import':
        if len(sys.argv) < 3:
            print("用法: python3 vocab_manager.py import <檔名>")
            sys.exit(1)
        vm.import_csv(sys.argv[2])
        vm.save()
    
    else:
        print(f"未知指令: {cmd}")
        print(__doc__)

if __name__ == '__main__':
    main()