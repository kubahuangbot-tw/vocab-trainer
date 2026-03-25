#!/usr/bin/env python3
"""
批次匯入例句
1. Oxford 5000 raw → 直接使用高品質例句
2. 剩餘單字 → 根據詞性產生模板例句
"""
import json, sys
sys.path.insert(0, '/home/deck/study/vocab_trainer')
from storage_sqlite import get_db, init_db

OXFORD_FILE = '/home/deck/study/vocab_trainer/oxford_5000_raw.json'
WORDS_JSON  = '/home/deck/study/vocab_trainer/backend/words.json'

# 詞性模板（英文例句，目標單字用 {word} 代入）
TEMPLATES = {
    'verb':        [
        "She decided to {word} the situation carefully.",
        "He tried to {word} everything before moving on.",
        "They had to {word} in order to succeed.",
    ],
    'noun':        [
        "The {word} was more important than anyone had expected.",
        "Everyone noticed the {word} immediately.",
        "Without a proper {word}, progress would be impossible.",
    ],
    'adjective':   [
        "The result was surprisingly {word}.",
        "Her response was {word} and well-considered.",
        "It was a {word} experience for all involved.",
    ],
    'adverb':      [
        "She spoke {word} and clearly to the audience.",
        "He handled the matter {word} and professionally.",
    ],
    'default':     [
        "The concept of {word} is widely discussed in academic circles.",
        "Understanding {word} is essential for advanced learners.",
    ],
}

import random

def get_template_sentence(word, word_type):
    key = word_type.lower() if word_type else 'default'
    options = TEMPLATES.get(key, TEMPLATES['default'])
    template = random.choice(options)
    return template.replace('{word}', word)


def run():
    init_db()

    # Load Oxford examples
    with open(OXFORD_FILE) as f:
        oxford = json.load(f)

    oxford_ex = {}
    for v in oxford.values():
        w = v.get('word', '').lower().strip()
        ex = v.get('example', '').strip()
        if w and ex:
            oxford_ex[w] = ex

    # Load words.json for word types
    with open(WORDS_JSON) as f:
        word_list = json.load(f)

    with get_db() as conn:
        cursor = conn.cursor()

        # Get all words without example sentences
        rows = cursor.execute(
            "SELECT id, word, word_type FROM words WHERE example_sentence IS NULL OR example_sentence = ''"
        ).fetchall()

        oxford_count = 0
        template_count = 0

        for row in rows:
            word_id, word, word_type = row['id'], row['word'], row['word_type']

            if word in oxford_ex:
                sentence = oxford_ex[word]
                oxford_count += 1
            else:
                wtype = word_type or word_list.get(word, {}).get('type', '')
                sentence = get_template_sentence(word, wtype)
                template_count += 1

            cursor.execute(
                "UPDATE words SET example_sentence = ? WHERE id = ?",
                (sentence, word_id)
            )

        conn.commit()

    print(f"完成！")
    print(f"  Oxford 高品質例句: {oxford_count:,}")
    print(f"  模板生成例句:      {template_count:,}")
    print(f"  總計:              {oxford_count + template_count:,}")

    # Verify
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        covered = conn.execute(
            "SELECT COUNT(*) FROM words WHERE example_sentence IS NOT NULL AND example_sentence != ''"
        ).fetchone()[0]
    print(f"\n覆蓋率: {covered:,} / {total:,} ({covered/total*100:.1f}%)")


if __name__ == '__main__':
    run()
