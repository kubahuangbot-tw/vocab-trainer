"""
訓練邏輯模組 - Spaced Repetition System
基於錯誤頻率自動調整單字出現權重
"""
import random
from word_list import WORD_LIST
from storage import Storage
from example_sentences import get_example_sentence

# 難度對應表 (internal level)
DIFFICULTY_MAP = {
    "A1": [1],      # 基礎
    "A2": [1, 2],   # 基礎 + 初級
    "B1": [2, 3],   # 初級 + 中級
    "B2": [3, 4],   # 中級 + 中高級
    "B3": [4],      # 中高級
    "C1": [4, 5],   # 中高級 + 高級
    "C2": [5],      # 高級
}

# 難度名稱對應 internal level
DIFFICULTY_LEVELS = {
    "A1": 1,
    "A2": 2,
    "B1": 3,
    "B2": 4,
    "B3": 5,
    "C1": 6,
    "C2": 7,
}

class VocabTrainer:
    """單字訓練器"""
    
    def __init__(self, user_id=None):
        # 嘗試使用 SQLite，失敗則回退到 CSV
        try:
            import storage_sqlite as sqlite_storage
            self.use_sqlite = True
            self.sqlite_storage = sqlite_storage
            self.user_id = user_id
        except:
            self.use_sqlite = False
        
        self.storage = Storage()
        self.current_words = []
        self.current_index = 0
        self.mode = "mixed"  # random, weak, mixed
        self.difficulty = "A2"  # 預設難度
        self.current_question = None  # 儲存當前題目
    
    def select_words(self, count=10, mode="mixed", difficulty="A2", review_ratio=0.7):
        """
        選擇要練習的單字
        - random: 完全隨機
        - weak: 優先選擇錯誤次數多的
        - mixed: 根據 review_ratio 設定 (預設 70% 弱點 + 30% 新單字)
        - difficulty: 難度範圍 (A1-C2)
        - review_ratio: 複習比例 (0-1), 例如 0.3 = 30% 複習, 70% 新題
        """
        self.mode = mode
        self.difficulty = difficulty
        
        # 根據難度範圍過濾單字 (只顯示有中文定義的)
        def has_chinese_meaning(d):
            meaning = d.get('meaning', '')
            return meaning.strip() and any('\u4e00' <= c <= '\u9fff' for c in meaning)
        
        if '-' in difficulty:
            min_diff, max_diff = difficulty.split('-')
            min_level = DIFFICULTY_LEVELS.get(min_diff, 1)
            max_level = DIFFICULTY_LEVELS.get(max_diff, 7)
            available_words = [w for w, d in WORD_LIST.items() 
                             if min_level <= d.get('level', 1) <= max_level
                             and has_chinese_meaning(d)]  # 只需要中文
        else:
            allowed_levels = DIFFICULTY_MAP.get(difficulty, [1, 2])
            available_words = [w for w, d in WORD_LIST.items() 
                             if d.get('level', 1) in allowed_levels
                             and has_chinese_meaning(d)]  # 只需要中文
        
        progress = self.storage.get_progress()
        
        if mode == "random" or mode == "debug_fixed":
            # 優先選擇未測試過的單字
            untested = [w for w in available_words if w not in progress]
            if len(untested) >= count:
                words = random.sample(untested, count)
            elif len(untested) > 0:
                # 取全部未測試 + 補一些已測試的
                words = untested + random.sample(
                    [w for w in available_words if w not in untested], 
                    count - len(untested)
                )
            else:
                words = random.sample(available_words, min(count, len(available_words)))
        
        elif mode == "weak":
            # 嘗試從 SQLite 取得弱點單字
            if self.use_sqlite and self.user_id:
                weak_words = self.sqlite_storage.get_weak_words(self.user_id, count * 2)
                # SQLite 回傳格式: [(word, {meaning: ...}), ...]
                weak_words_list = [w[0] for w in weak_words if w[0] in available_words]
            else:
                weak_words = self.storage.get_weak_words(count * 2)
                weak_words_list = [w[0] for w in weak_words if w[0] in available_words]
            
            if len(weak_words_list) < count:
                remaining = [w for w in available_words if w not in weak_words_list]
                words = weak_words_list + random.sample(remaining, count - len(weak_words_list))
                words = words[:count]
            else:
                words = weak_words_list[:count]
        
        else:  # mixed - 使用自訂比例
            weak_count = int(count * review_ratio)
            new_count = count - weak_count
            
            # 取得弱點單字
            if self.use_sqlite and self.user_id:
                weak_words = self.sqlite_storage.get_weak_words(self.user_id, weak_count * 2)
                weak_list = [w[0] for w in weak_words if w[0] in available_words][:weak_count]
                
                # 從 SQLite 取得已學習的單字
                user_progress = self.sqlite_storage.get_user_progress(self.user_id)
                learned = set(user_progress.keys())
            else:
                weak_words = self.storage.get_weak_words(weak_count * 2)
                weak_list = [w[0] for w in weak_words if w[0] in available_words][:weak_count]
                learned = set(progress.keys())
            
            remaining = [w for w in available_words if w not in learned]
            new_words = random.sample(remaining, min(new_count, len(remaining)))
            
            words = weak_list + new_words
            random.shuffle(words)
        
        self.current_words = words
        self.current_index = 0
        return words
    
    def get_current_word(self):
        """获取當前要練習的單字"""
        if self.current_index >= len(self.current_words):
            return None
        word = self.current_words[self.current_index]
        return {
            'word': word,
            'meaning': WORD_LIST[word]['meaning'],
            'level': WORD_LIST[word].get('level', 1)
        }
    
    def check_answer(self, user_answer):
        """檢查答案並記錄"""
        current = self.get_current_word()
        if not current:
            return None
        
        word = current['word']
        correct_meaning = current['meaning']
        
        # 簡易比對 (忽略大小寫和空白)
        is_correct = user_answer.strip().lower() == correct_meaning.lower()
        
        # 更新進度
        self.storage.update_progress(word, correct_meaning, is_correct)
        
        # 標記為已測試
        self.storage.mark_tested(word)
        
        if not is_correct:
            # 記錄錯誤
            example = get_example_sentence(word)
            self.storage.add_wrong_record(word, correct_meaning, user_answer, example)
        
        # 前進到下一題
        self.current_index += 1
        
        return {
            'correct': is_correct,
            'word': word,
            'correct_meaning': correct_meaning,
            'your_answer': user_answer,
            'example': get_example_sentence(word) if not is_correct else ""
        }
    
    def get_next_question(self):
        """獲取下一個問題 (選擇題模式) - 固定選項不會變"""
        current = self.get_current_word()
        if not current:
            return None
        
        # 如果已經有儲存的題目且單字相同，直接回傳
        if self.current_question and self.current_question.get('word') == current['word']:
            return self.current_question
        
        # 產生4個選項 (1個正確 + 3個錯誤)
        word = current['word']
        correct = current['meaning']
        
        # 隨機選3個錯誤選項 (只取中文定義)
        all_meanings = [w['meaning'] for w in WORD_LIST.values() 
                      if w.get('meaning', '').strip() 
                      and any('\u4e00' <= c <= '\u9fff' for c in w['meaning'])]
        wrong_options = random.sample([m for m in all_meanings if m != correct], 3)
        
        options = wrong_options + [correct]
        random.shuffle(options)
        
        # 儲存題目避免 rerun 時改變
        self.current_question = {
            'word': word,
            'options': options,
            'correct_answer': correct,
            'level': current['level']
        }
        
        return self.current_question
        
        return {
            'word': word,
            'options': options,
            'correct_answer': correct,
            'level': current['level']
        }
    
    def review_wrong_words(self, count=10):
        """複習錯誤的單字"""
        wrong_records = self.storage.get_wrong_records()
        
        # 按單字分組
        word_dict = {}
        for record in wrong_records:
            word = record['word']
            if word not in word_dict:
                word_dict[word] = record
        
        words = list(word_dict.keys())[:count]
        return [(w, word_dict[w]['meaning']) for w in words]
    
    def reset_session(self):
        """重置 session"""
        self.current_index = 0