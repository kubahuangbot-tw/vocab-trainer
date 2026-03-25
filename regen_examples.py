#!/usr/bin/env python3
"""
重新生成模板例句，使用更多樣化的句型
只重新生成「模板句」，保留 Oxford 真實例句不動
"""
import sys, random
sys.path.insert(0, '/home/deck/study/vocab_trainer')
from storage_sqlite import get_db, init_db

# ===== 多樣化模板（每種詞性 15+ 個句型）=====
TEMPLATES = {
    'verb': [
        "She had to {word} the situation before things got worse.",
        "He managed to {word} successfully despite the challenges.",
        "They decided to {word} early rather than wait.",
        "It's important to {word} when the opportunity arises.",
        "Learning how to {word} properly takes time and practice.",
        "The teacher asked her students to {word} the exercise.",
        "You should {word} carefully before making any decision.",
        "He was the first to {word} when the need arose.",
        "We often need to {word} in order to move forward.",
        "The manager instructed the team to {word} immediately.",
        "It can be difficult to {word} under pressure.",
        "Many people choose to {word} rather than face the problem.",
        "She learned to {word} from her mentor's advice.",
        "The expert advised him to {word} as soon as possible.",
        "Without the ability to {word}, progress becomes impossible.",
    ],
    'noun': [
        "The {word} was far more significant than anyone had expected.",
        "She demonstrated a deep understanding of {word}.",
        "His {word} impressed everyone in the room.",
        "A strong sense of {word} is essential in this field.",
        "The {word} became the central topic of the discussion.",
        "Without {word}, the project would have failed completely.",
        "She developed a unique approach to {word} over the years.",
        "His lack of {word} was immediately apparent.",
        "The report highlighted the importance of {word}.",
        "Their {word} set them apart from the competition.",
        "A thorough grasp of {word} is required for this role.",
        "The professor emphasized the role of {word} in society.",
        "She built her career around her expertise in {word}.",
        "The concept of {word} has evolved significantly over time.",
        "Developing {word} requires both patience and dedication.",
    ],
    'adjective': [
        "The outcome was remarkably {word} given the circumstances.",
        "Her response was {word} and well thought out.",
        "He found the experience surprisingly {word}.",
        "The situation became increasingly {word} as time passed.",
        "Everyone agreed that the result was {word}.",
        "It was {word} of her to react so calmly.",
        "The atmosphere in the room felt {word} and tense.",
        "His tone was {word}, leaving no room for doubt.",
        "She remained {word} even under intense pressure.",
        "The decision seemed {word} to most of the committee.",
        "A {word} approach is often the most effective.",
        "The landscape looked {word} in the early morning light.",
        "Being {word} in such situations requires real strength.",
        "His manner was {word}, which made others uncomfortable.",
        "The critic described the performance as {word}.",
    ],
    'adverb': [
        "She spoke {word}, making every word count.",
        "He acted {word} when the situation demanded it.",
        "The team performed {word} throughout the competition.",
        "She responded {word} to the unexpected question.",
        "He approached the problem {word} and logically.",
        "The surgeon operated {word} and with great care.",
        "They communicated {word} with each other.",
        "She handled the criticism {word} and professionally.",
        "He moved {word} through the crowd.",
        "The artist painted {word}, with deliberate strokes.",
    ],
    'default': [
        "The idea of {word} is often misunderstood by beginners.",
        "Scholars have long debated the meaning of {word}.",
        "Understanding {word} is a key part of advanced learning.",
        "She encountered {word} for the first time during her studies.",
        "The book devoted an entire chapter to the concept of {word}.",
        "Many experts consider {word} to be fundamental in this area.",
        "He struggled to explain {word} to his younger brother.",
        "The lesson on {word} proved to be the most memorable.",
        "A proper grasp of {word} opens many intellectual doors.",
        "The professor's lecture on {word} drew a large audience.",
        "She wrote her thesis on the subject of {word}.",
        "The documentary explored the origins and impact of {word}.",
        "Debating the nuances of {word} helped sharpen her thinking.",
        "He spent weeks researching {word} for his presentation.",
        "The seminar focused specifically on the topic of {word}.",
    ],
}

# Templates that are bad (to replace)
BAD_PATTERNS = [
    'widely discussed in academic circles',
    'essential for advanced learners',
    'decided to {word} carefully',
    'tried to {word} before moving on',
    'had to {word} in order to succeed',
    'was more important than anyone had expected',
    'Everyone noticed the {word} immediately',
    'Without a proper {word}, progress would be impossible',
    'surprisingly {word}',
    'response was {word} and well-considered',
    'was a {word} experience for all involved',
    'spoke {word} and clearly to the audience',
    'handled the matter {word} and professionally',
]


def is_template_sentence(sentence):
    for pat in BAD_PATTERNS:
        if pat.replace('{word}', '').strip().lower() in sentence.lower():
            return True
    return False


def generate_sentence(word, word_type):
    key = (word_type or '').lower().strip()
    # Normalise word type
    if key in ('v', 'vt', 'vi', 'verb'): key = 'verb'
    elif key in ('n', 'noun'): key = 'noun'
    elif key in ('adj', 'adjective'): key = 'adjective'
    elif key in ('adv', 'adverb'): key = 'adverb'
    else: key = 'default'

    templates = TEMPLATES.get(key, TEMPLATES['default'])
    template = random.choice(templates)
    return template.replace('{word}', word)


def run():
    init_db()
    random.seed()  # ensure real randomness

    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            "SELECT id, word, word_type, example_sentence FROM words"
        ).fetchall()

        replaced = 0
        kept = 0

        for row in rows:
            sentence = row['example_sentence'] or ''
            if is_template_sentence(sentence):
                new_sentence = generate_sentence(row['word'], row['word_type'])
                cursor.execute(
                    "UPDATE words SET example_sentence = ? WHERE id = ?",
                    (new_sentence, row['id'])
                )
                replaced += 1
            else:
                kept += 1

        conn.commit()

    print(f"完成！")
    print(f"  保留原有例句（Oxford）: {kept:,}")
    print(f"  重新生成模板例句:       {replaced:,}")

    # Quick check for variety
    with get_db() as conn:
        rows = conn.execute(
            "SELECT example_sentence FROM words WHERE example_sentence IS NOT NULL ORDER BY RANDOM() LIMIT 10"
        ).fetchall()
    print("\n隨機抽樣 10 個例句:")
    for r in rows:
        print(f"  • {r[0]}")


if __name__ == '__main__':
    run()
