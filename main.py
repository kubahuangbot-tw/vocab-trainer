#!/usr/bin/env python3
"""
VocabTrainer - 英文單字訓練系統
CLI 介面
"""

import sys
import random

# 確保可以引入同目錄的模組
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trainer import VocabTrainer
from storage import Storage

def print_header():
    print("=" * 50)
    print("📚 VocabTrainer - 英文單字訓練系統")
    print("=" * 50)

def cmd_train(args):
    """訓練模式"""
    trainer = VocabTrainer()
    
    mode = args[0] if args else "mixed"
    count = 10
    
    print(f"\n🎯 開始訓練 (模式: {mode})")
    print("-" * 40)
    
    words = trainer.select_words(count, mode)
    print(f"已選擇 {len(words)} 個單字\n")
    
    correct_count = 0
    error_count = 0
    
    for i, word in enumerate(words, 1):
        word_data = trainer.get_current_word()
        print(f"【{i}/{len(words)}】單字: {word}")
        print(f"   難度: {'⭐' * word_data['level']}")
        
        # 選擇題模式
        question = trainer.get_next_question()
        print("\n   選項:")
        for idx, option in enumerate(question['options'], 1):
            print(f"     {idx}. {option}")
        
        answer = input("\n   你的答案 (輸入編號 1-4): ").strip()
        
        try:
            idx = int(answer) - 1
            user_answer = question['options'][idx] if 0 <= idx < 4 else "Invalid"
        except:
            user_answer = answer
        
        result = trainer.check_answer(user_answer)
        
        if result['correct']:
            print("   ✅ 正確!")
            correct_count += 1
        else:
            print(f"   ❌ 錯誤!")
            print(f"   正確答案: {result['correct_meaning']}")
            print(f"   你的答案: {result['your_answer']}")
            print(f"   📝 例句: {result['example']}")
            error_count += 1
        
        print()
    
    print("-" * 40)
    print(f"📊 結果: 正確 {correct_count} / 錯誤 {error_count}")
    print(f"   正確率: {correct_count/(correct_count+error_count)*100:.1f}%")

def cmd_quiz(args):
    """快速測驗模式"""
    trainer = VocabTrainer()
    
    count = int(args[0]) if args and args[0].isdigit() else 5
    mode = "random" if len(args) > 1 and args[1] == "random" else "weak"
    
    print(f"\n🔥 快速測驗 ({count} 題, 模式: {mode})")
    print("-" * 40)
    
    trainer.select_words(count, mode)
    correct = 0
    
    for i in range(count):
        q = trainer.get_next_question()
        if not q:
            break
            
        print(f"\n【{i+1}】{q['word']}")
        for idx, opt in enumerate(q['options'], 1):
            print(f"  {idx}. {opt}")
        
        ans = input("答案: ").strip()
        try:
            user_ans = q['options'][int(ans)-1]
        except:
            user_ans = ans
            
        is_correct = user_ans == q['correct_answer']
        if is_correct:
            correct += 1
            print("✅")
        else:
            print(f"❌ 正確: {q['correct_answer']}")
        
        # 更新進度
        trainer.storage.update_progress(q['word'], q['correct_answer'], is_correct)
    
    print(f"\n📊 得分: {correct}/{count} ({correct/count*100:.0f}%)")

def cmd_review(args):
    """複習錯誤的單字"""
    trainer = VocabTrainer()
    count = int(args[0]) if args and args[0].isdigit() else 10
    
    print(f"\n📖 複習錯誤單字 (最多 {count} 個)")
    print("-" * 40)
    
    wrong_words = trainer.review_wrong_words(count)
    
    if not wrong_words:
        print("目前沒有錯誤記錄!")
        return
    
    for i, (word, meaning) in enumerate(wrong_words, 1):
        print(f"{i}. {word} - {meaning}")
    
    print("\n選擇要練習的單字編號 (或按Enter結束):")
    choice = input("> ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(wrong_words):
        word, meaning = wrong_words[int(choice)-1]
        print(f"\n🎯 單字: {word}")
        print(f"   意思: {meaning}")
        
        from example_sentences import get_example_sentence
        print(f"   例句: {get_example_sentence(word)}")
        
        # 測驗
        test = input("\n輸入意思: ").strip()
        if test.lower() == meaning.lower():
            print("✅ 正確!")
        else:
            print(f"❌ 錯誤! 正確答案是: {meaning}")

def cmd_stats(args):
    """查看學習統計"""
    storage = Storage()
    stats = storage.get_stats()
    
    print_header()
    print("\n📊 學習統計")
    print("-" * 40)
    print(f"總學習單字數: {stats['total_words']}")
    print(f"總正確次數: {stats['total_correct']}")
    print(f"總錯誤次數: {stats['total_errors']}")
    print(f"正確率: {stats['accuracy']:.1f}%")
    
    if stats['weak_words']:
        print("\n⚠️ 需要加強的單字:")
        for word, data in stats['weak_words'][:5]:
            print(f"  • {word} (錯誤 {data['error_count']} 次)")

def cmd_list(args):
    """列出所有單字"""
    from word_list import WORD_LIST
    
    level = args[0] if args else None
    
    if level and level.isdigit():
        from word_list import get_words_by_level
        words = get_words_by_level(int(level))
    else:
        words = WORD_LIST
    
    print(f"\n📚 單字庫 (共 {len(words)} 個)")
    print("-" * 40)
    
    for word, data in list(words.items())[:20]:
        print(f"  {word}: {data['meaning']} (Level {data.get('level', 1)})")
    
    if len(words) > 20:
        print(f"  ... 還有 {len(words)-20} 個單字")

def cmd_help():
    """顯示幫助"""
    print_header()
    print("""
使用方法: python main.py <命令> [參數]

命令:
  train [模式]      開始訓練 (random/weak/mixed)
  quiz [數量]      快速測驗
  review [數量]    複習錯誤的單字
  stats            查看學習統計
  list [難度]      列出單字 (1-5)
  help             顯示幫助

範例:
  python main.py train mixed    # 混合模式訓練
  python main.py quiz 5 weak    # 弱點測驗5題
  python main.py review 10     # 複習10個錯字
  python main.py stats          # 查看統計
  python main.py list 2        # 列出 Level 2 單字
""")

def main():
    if len(sys.argv) < 2:
        cmd_help()
        return
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    commands = {
        'train': cmd_train,
        'quiz': cmd_quiz,
        'review': cmd_review,
        'stats': cmd_stats,
        'list': cmd_list,
        'help': cmd_help,
    }
    
    if cmd in commands:
        commands[cmd](args)
    else:
        print(f"未知命令: {cmd}")
        cmd_help()

if __name__ == '__main__':
    main()