"""
資料儲存模組 - 處理CSV讀寫
"""
import csv
import os
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PROGRESS_FILE = DATA_DIR / "progress.csv"
WRONG_WORDS_FILE = DATA_DIR / "wrong_words.csv"


class Storage:
    """處理學習進度與錯誤記錄"""
    
    def __init__(self):
        self._init_files()
    
    def _init_files(self):
        """初始化CSV文件"""
        # 進度文件
        if not PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['word', 'correct_count', 'error_count', 'last_reviewed', 'weight', 'meaning'])
        
        # 錯誤記錄文件
        if not WRONG_WORDS_FILE.exists():
            with open(WRONG_WORDS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['word', 'meaning', 'error_time', 'your_answer', 'example_sentence'])
    
    # ========== 進度管理 ==========
    def get_progress(self):
        """讀取所有單字學習進度"""
        progress = {}
        if not PROGRESS_FILE.exists():
            return progress
        
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                progress[row['word']] = {
                    'correct_count': int(row.get('correct_count', 0)),
                    'error_count': int(row.get('error_count', 0)),
                    'last_reviewed': row.get('last_reviewed', ''),
                    'weight': float(row.get('weight', 1)),
                    'meaning': row.get('meaning', '')
                }
        return progress
    
    def update_progress(self, word, meaning, correct=True):
        """更新單字學習進度"""
        progress = self.get_progress()
        now = datetime.now().strftime('%Y-%m-%d')
        
        if word not in progress:
            progress[word] = {
                'correct_count': 0,
                'error_count': 0,
                'last_reviewed': now,
                'weight': 1,
                'meaning': meaning
            }
        
        if correct:
            progress[word]['correct_count'] += 1
            # 正確時降低權重 (最少為1)
            progress[word]['weight'] = max(1, progress[word]['weight'] * 0.8)
        else:
            progress[word]['error_count'] += 1
            # 錯誤時增加權重
            progress[word]['weight'] = progress[word]['weight'] * 2 + 1
        
        progress[word]['last_reviewed'] = now
        
        # 寫回文件
        with open(PROGRESS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['word', 'correct_count', 'error_count', 'last_reviewed', 'weight', 'meaning'])
            for word, data in progress.items():
                writer.writerow([
                    word, 
                    data['correct_count'], 
                    data['error_count'], 
                    data['last_reviewed'], 
                    data['weight'],
                    data['meaning']
                ])
    
    def get_weak_words(self, top_n=20):
        """获取最弱的單字 (錯誤次數最多)"""
        progress = self.get_progress()
        sorted_words = sorted(
            progress.items(), 
            key=lambda x: x[1]['error_count'], 
            reverse=True
        )
        return sorted_words[:top_n]
    
    # ========== 錯誤記錄 ==========
    def add_wrong_record(self, word, meaning, your_answer, example=""):
        """記錄錯誤的單字"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(WRONG_WORDS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([word, meaning, now, your_answer, example])
    
    def get_wrong_records(self):
        """讀取所有錯誤記錄"""
        records = []
        if not WRONG_WORDS_FILE.exists():
            return records
        
        with open(WRONG_WORDS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return records
    
    def get_stats(self):
        """获取學習統計"""
        progress = self.get_progress()
        
        total_words = len(progress)
        total_correct = sum(p['correct_count'] for p in progress.values())
        total_errors = sum(p['error_count'] for p in progress.values())
        
        # 找出最弱的單字
        weak_words = self.get_weak_words(10)
        
        return {
            'total_words': total_words,
            'total_correct': total_correct,
            'total_errors': total_errors,
            'accuracy': total_correct / (total_correct + total_errors) * 100 if (total_correct + total_errors) > 0 else 0,
            'weak_words': weak_words
        }
    
    # ========== 測試歷史記錄 ==========
    TESTED_FILE = DATA_DIR / "tested_words.json"
    
    def get_tested_words(self):
        """獲取已測試過的單字"""
        if not self.TESTED_FILE.exists():
            return {}
        
        with open(self.TESTED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def mark_tested(self, word):
        """標記單字為已測試"""
        tested = self.get_tested_words()
        if word not in tested:
            tested[word] = {
                'tested_count': 1,
                'last_tested': datetime.now().strftime('%Y-%m-%d')
            }
        else:
            tested[word]['tested_count'] += 1
            tested[word]['last_tested'] = datetime.now().strftime('%Y-%m-%d')
        
        with open(self.TESTED_FILE, 'w', encoding='utf-8') as f:
            json.dump(tested, f, ensure_ascii=False, indent=2)
    
    def get_untested_words(self, word_list):
        """獲取尚未測試過的單字"""
        tested = set(self.get_tested_words().keys())
        return [w for w in word_list if w not in tested]
    
    def get_tested_count(self):
        """獲取已測試單字數"""
        return len(self.get_tested_words())