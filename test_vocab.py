"""
VocabTrainer 單元測試
"""
import unittest
import os
import sys
import tempfile
import shutil

# 加入專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestStorageSQLite(unittest.TestCase):
    """測試 SQLite 儲存模組"""
    
    @classmethod
    def setUpClass(cls):
        """測試前建立暫時資料庫"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.original_dir = os.getcwd()
        
        # 建立測試資料庫
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        from storage_sqlite import init_db, DB_PATH, DATA_DIR
        
        # 使用測試資料庫
        cls.test_db = os.path.join(cls.temp_dir, 'test_vocab.db')
        os.environ['TEST_DB_PATH'] = cls.test_db
        
        # 這是簡化測試，直接用實際資料庫
        from storage_sqlite import get_db
        init_db()
    
    @classmethod
    def tearDownClass(cls):
        """測試後清理"""
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_init_db(self):
        """測試資料庫初始化"""
        from storage_sqlite import get_db, get_word_count
        with get_db() as conn:
            cursor = conn.cursor()
            # 檢查表格是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn('words', tables)
            self.assertIn('users', tables)
            self.assertIn('user_progress', tables)
            self.assertIn('error_details', tables)
    
    def test_get_word_count(self):
        """測試取得單字數量"""
        from storage_sqlite import get_word_count
        count = get_word_count()
        self.assertGreater(count, 10000)  # 應該有超過 10000 個單字
    
    def test_get_user(self):
        """測試取得用戶"""
        from storage_sqlite import get_user, create_user
        
        # 建立測試用戶
        test_user = f"test_user_{id(self)}"
        create_user(test_user, "test123", "測試用戶")
        
        # 取得用戶
        user = get_user(test_user)
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], test_user)
    
    def test_add_word_auto_exists(self):
        """測試新增已存在的單字"""
        from storage_sqlite import add_word_auto, get_user
        
        user = get_user('guest')
        user_id = user['id'] if user else None
        
        # 新增已存在的單字
        result = add_word_auto('hello', user_id)
        
        self.assertTrue(result['success'])
        self.assertIn('已存在', result['message'])
    
    def test_add_word_auto_new(self):
        """測試新增新單字"""
        from storage_sqlite import add_word_auto, get_db
        
        test_word = f"testword_{id(self)}"
        result = add_word_auto(test_word, None)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['word'], test_word)
        
        # 清理測試資料
        with get_db() as conn:
            conn.execute("DELETE FROM words WHERE word = ?", (test_word,))
    
    def test_update_progress(self):
        """測試更新學習進度"""
        from storage_sqlite import update_progress, get_user, get_user_progress
        
        user = get_user('admin')
        if not user:
            self.skipTest("沒有 admin 用戶")
        
        # 更新進度
        update_progress(user['id'], 'hello', '你好', correct=True)
        update_progress(user['id'], 'hello', '你好', correct=False)
        
        # 檢查進度
        progress = get_user_progress(user['id'])
        self.assertIn('hello', progress)
    
    def test_get_weak_words(self):
        """測試取得弱點單字"""
        from storage_sqlite import get_weak_words, get_user
        
        user = get_user('kuba')
        if not user:
            self.skipTest("沒有 kuba 用戶")
        
        weak_words = get_weak_words(user['id'], 5)
        
        # 應該回傳 list
        self.assertIsInstance(weak_words, list)
    
    def test_calculate_time_weight(self):
        """測試時間權重計算"""
        from storage_sqlite import calculate_time_weight
        from datetime import datetime, timedelta
        
        # 3天前 → 權重 2.0
        recent = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
        weight = calculate_time_weight(recent)
        self.assertEqual(weight, 2.0)
        
        # 20天前 → 權重 1.0
        old = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S')
        weight = calculate_time_weight(old)
        self.assertEqual(weight, 1.0)
        
        # 無效日期 → 權重 1.0
        weight = calculate_time_weight(None)
        self.assertEqual(weight, 1.0)


class TestTranslateFunction(unittest.TestCase):
    """測試翻譯功能"""
    
    def test_translate_word(self):
        """測試單字翻譯"""
        from storage_sqlite import translate_word
        
        result = translate_word('hello')
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


if __name__ == '__main__':
    unittest.main()