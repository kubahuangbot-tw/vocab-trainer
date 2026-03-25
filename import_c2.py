#!/usr/bin/env python3
"""
匯入 C2 程度單字並自動翻譯
C2 單字來源：Cambridge C2 Proficiency / Academic Word List / GRE 高頻詞彙
"""
import sys, time
sys.path.insert(0, '/home/deck/study/vocab_trainer')
from storage_sqlite import get_db, translate_word, init_db

# ===== C2 高頻單字清單（約 300 個）=====
C2_WORDS = [
    # Academic / Formal
    "aberration","abhor","abject","abjure","abscond","abstain","abstruse",
    "accrue","acrimony","acumen","adamant","admonish","adroit","adversarial",
    "affable","affluent","aggrandize","alacrity","alleviate","amalgamate",
    "ambiguous","ameliorate","anachronism","anecdotal","anomalous","antipathy",
    "antiquated","apathy","appease","approbation","arduous","articulate",
    "ascertain","assiduous","assuage","astute","atrophy","audacious","augment",
    "auspicious","austere","avarice","axiomatic",

    "belabor","belie","bellicose","benevolent","berate","bolster","bombastic",
    "boorish","brevity","brusque","bureaucratic",

    "cacophony","callous","candid","capitulate","capricious","censure",
    "charlatan","circumspect","clandestine","coerce","cogent","complacent",
    "complicity","conciliate","condescend","convoluted","corroborate","credulous",
    "culpable","cursory",

    "dauntless","debilitate","decry","deferential","defunct","delineate",
    "demur","denunciation","deplore","deprecate","deride","desiccate",
    "desolate","despondent","deter","didactic","diffident","digress",
    "dilettante","discern","disdain","disparate","dissonance","dogmatic",
    "dubious","duplicity",

    "ebullient","eccentric","egregious","eloquent","eminent","empirical",
    "enervate","ephemeral","equivocate","erudite","esoteric","euphemism",
    "exacerbate","exemplary","exhaustive","exonerate","expedient","explicable",
    "explicit","extraneous",

    "facetious","fallacious","fastidious","feckless","fervent","flagrant",
    "flippant","florid","fluctuate","fortuitous","frugal","furtive",

    "garrulous","grandiose","gratuitous","gravity","gregarious","guile",

    "hackneyed","harangue","haughty","hegemony","heretical","homogeneous",
    "hyperbole","hypothetical",

    "idiosyncratic","ignominious","immutable","impartial","impetuous",
    "impudent","inchoate","incongruous","indifferent","indolent","inert",
    "innocuous","insidious","intractable","inveterate","irascible",

    "juxtapose","laconic","lament","languid","loquacious","lucid","ludicrous",

    "magnanimous","malevolent","meticulous","mollify","morose","mundane",
    "munificent",

    "nefarious","negligent","nonchalant","nuanced",

    "obfuscate","obsequious","obstinate","obtuse","onerous","opaque",
    "ostracize","overwrought",

    "paradox","paucity","pedantic","perfidious","perfunctory","perturb",
    "petulant","placate","platitude","poignant","pompous","pragmatic",
    "preclude","pretentious","prevaricate","proclivity","prodigal",
    "profligate","proliferate","propitious","prudent","pugnacious",

    "quandary","querulous",

    "recalcitrant","reclusive","rectify","refute","remiss","repudiate",
    "resilient","reticent","rhetoric","rigorous",

    "sagacious","sanction","scrupulous","serendipity","skeptical","solicitous",
    "speculative","spurious","stagnate","steadfast","stoic","stringent",
    "subservient","succinct","superfluous","sycophant",

    "taciturn","tangential","tedious","tenacious","terse","tractable",
    "transient","turbulent",

    "ubiquitous","unequivocal","usurp",

    "vacillate","verbose","vindicate","volatile","voracious",

    "wane","wary","whimsical",

    "zealous","zeal",
]

WORDS_JSON = '/home/deck/study/vocab_trainer/backend/words.json'

def import_c2_words():
    import json
    init_db()

    # 載入現有 words.json
    with open(WORDS_JSON, 'r', encoding='utf-8') as f:
        word_list = json.load(f)

    with get_db() as conn:
        cursor = conn.cursor()

        inserted = 0
        skipped = 0
        failed = 0

        for i, word in enumerate(C2_WORDS):
            word = word.strip().lower()

            # 檢查 DB 是否已存在
            cursor.execute("SELECT id, cefr FROM words WHERE word = ?", (word,))
            existing = cursor.fetchone()

            if existing:
                if existing['cefr'] != 'c2':
                    cursor.execute(
                        "UPDATE words SET cefr='c2', difficulty=6 WHERE word=?",
                        (word,)
                    )
                    conn.commit()
                    # 也更新 words.json
                    if word in word_list:
                        word_list[word]['level'] = 6
                    print(f"  ↑ 升級 {word} → C2")
                skipped += 1
                continue

            # 翻譯
            meaning = translate_word(word)
            if not meaning:
                print(f"  ✗ 翻譯失敗: {word}")
                failed += 1
                continue

            # 寫入 DB
            cursor.execute("""
                INSERT INTO words (word, meaning, cefr, difficulty, created_at)
                VALUES (?, ?, 'c2', 6, CURRENT_TIMESTAMP)
            """, (word, meaning))
            conn.commit()

            # 寫入 words.json
            word_list[word] = {'meaning': meaning, 'level': 6, 'type': ''}

            inserted += 1
            print(f"  ✓ [{i+1}/{len(C2_WORDS)}] {word}: {meaning}")
            time.sleep(0.3)

        # 儲存 words.json
        with open(WORDS_JSON, 'w', encoding='utf-8') as f:
            json.dump(word_list, f, ensure_ascii=False, indent=2)

        print(f"\n完成！新增: {inserted}, 已存在: {skipped}, 失敗: {failed}")
        print(f"words.json 已更新，共 {len(word_list)} 個單字")


if __name__ == "__main__":
    import_c2_words()
