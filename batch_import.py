"""
大量匯入常用單字 (300個)
"""
import requests
import time
import random
from word_list import WORD_LIST, add_word

# 常用單字列表 (精選300個)
COMMON_WORDS = [
    "able", "about", "above", "accept", "according", "account", "across", "action", "activity",
    "actually", "address", "administration", "admit", "adult", "affect", "after", "again", "against",
    "agency", "agent", "agree", "agreement", "ahead", "allow", "almost", "alone", "along",
    "already", "also", "although", "always", "american", "among", "amount", "analysis", "ancient",
    "animal", "another", "answer", "anyone", "anything", "appear", "application", "apply", "approach",
    "area", "argue", "around", "arrive", "article", "artist", "assume", "attack", "attention",
    "attorney", "audience", "author", "authority", "available", "avoid", "away", "baby", "back",
    "ball", "bank", "base", "beat", "beautiful", "because", "become", "before", "begin",
    "behavior", "behind", "believe", "benefit", "best", "better", "between", "beyond", "bill",
    "billion", "bit", "black", "blood", "blue", "board", "body", "book", "both",
    "boy", "break", "bring", "brother", "budget", "build", "building", "business", "buy",
    "call", "camera", "campaign", "cancer", "candidate", "capital", "card", "care", "career",
    "carry", "case", "catch", "cause", "cell", "center", "central", "century", "certain",
    "certainly", "chair", "challenge", "chance", "change", "character", "charge", "check", "child",
    "choice", "choose", "church", "citizen", "city", "civil", "claim", "class", "clear",
    "clearly", "close", "coach", "code", "cold", "collection", "college", "color", "come",
    "commercial", "common", "community", "company", "compare", "computer", "concept", "concern",
    "condition", "conference", "congress", "consider", "constant", "consumer", "contain", "continue",
    "control", "cost", "could", "count", "country", "couple", "course", "court", "cover",
    "create", "crime", "cultural", "culture", "cup", "current", "customer", "cut", "dark",
    "data", "daughter", "dead", "deal", "death", "debate", "decade", "decide", "decision",
    "deep", "defense", "degree", "delete", "demand", "democratic", "describe", "design", "despite",
    "detail", "determine", "develop", "development", "difference", "different", "difficult", "dinner",
    "direct", "director", "discover", "discuss", "disease", "doctor", "document", "dog", "door",
    "down", "draw", "dream", "drive", "drop", "drug", "during", "each", "early",
    "east", "easy", "economic", "economy", "edge", "edit", "effect", "effort", "eight",
    "either", "election", "employee", "end", "energy", "enjoy", "enough", "enter", "entire",
    "environment", "episode", "equal", "error", "escape", "establish", "even", "evening",
    "event", "ever", "every", "everybody", "everyone", "evidence", "exact", "exactly", "example",
    "except", "excuse", "exercise", "exist", "experience", "expert", "explain", "eye", "face",
    "fact", "factor", "fail", "fall", "family", "famous", "fast", "father", "favor",
    "fear", "federal", "feel", "feeling", "field", "fight", "figure", "fill", "film",
    "final", "finally", "financial", "find", "finger", "finish", "fire", "firm", "first",
    "fish", "floor", "focus", "follow", "food", "foot", "force", "foreign", "forest",
    "forget", "form", "former", "forward", "found", "four", "free", "freedom", "friend",
    "front", "full", "function", "fund", "future", "game", "garden", "gas", "general",
    "generation", "girl", "give", "glass", "goal", "good", "government", "ground", "group",
    "grow", "growth", "guess", "gun", "guy", "hair", "half", "hand", "hang",
    "happen", "happy", "hard", "have", "head", "health", "hear", "heart", "heat",
    "help", "here", "herself", "high", "himself", "history", "hold", "home", "hope",
    "hospital", "hotel", "hour", "house", "however", "human", "hundred", "husband", "idea",
    "identify", "image", "imagine", "impact", "important", "improve", "include", "including",
    "increase", "indeed", "indicate", "individual", "industry", "information", "inside", "insist",
    "instead", "interest", "interview", "into", "invest", "investment", "involve", "issue",
    "item", "itself", "join", "just", "keep", "kill", "kind", "kitchen", "know",
    "knowledge", "land", "language", "large", "last", "late", "later", "laugh", "law",
    "lawyer", "lay", "lead", "leader", "learn", "least", "leave", "left", "leg",
    "legal", "less", "letter", "level", "lie", "life", "light", "like", "likely",
    "line", "list", "listen", "little", "live", "local", "long", "look", "lose",
    "loss", "lost", "love", "machine", "magazine", "main", "maintain", "major", "majority",
    "make", "male", "man", "manage", "management", "manager", "manner", "many", "market",
    "marriage", "material", "matter", "maybe", "mean", "measure", "media", "medical", "meet",
    "meeting", "member", "memory", "mention", "message", "method", "middle", "might", "military",
    "million", "mind", "minute", "miss", "mission", "mistake", "model", "modern", "moment",
    "money", "month", "more", "morning", "most", "mother", "mouth", "move", "movement",
    "movie", "much", "must", "myself", "name", "nation", "national", "natural", "nature",
    "near", "nearly", "necessary", "need", "network", "never", "news", "newspaper",
    "next", "nice", "night", "none", "normal", "north", "note", "nothing", "notice",
    "now", "number", "occur", "offer", "office", "officer", "official", "often", "oil",
    "okay", "old", "once", "only", "onto", "open", "operation", "opinion", "option",
    "order", "organization", "original", "other", "others", "outside", "over", "own",
    "owner", "page", "pain", "painting", "paper", "parent", "part", "participant",
    "particular", "particularly", "partner", "party", "pass", "past", "patient", "pattern",
    "peace", "people", "perform", "performance", "perhaps", "period", "permanent", "permit",
    "person", "personal", "phone", "photo", "physical", "pick", "picture", "piece",
    "place", "plan", "plant", "platform", "play", "player", "please", "point", "police",
    "policy", "political", "politician", "politics", "poor", "popular", "population", "position",
    "positive", "possible", "power", "practice", "prepare", "present", "president", "press",
    "pressure", "pretty", "prevent", "price", "private", "probably", "problem", "process",
    "produce", "product", "professional", "professor", "program", "project", "property", "protect",
    "prove", "provide", "public", "pull", "purpose", "push", "quality", "question", "quickly",
    "quite", "race", "radio", "raise", "range", "rate", "rather", "reach", "read",
    "ready", "real", "reality", "realize", "really", "reason", "receive", "recent", "recently",
    "recognize", "record", "reduce", "reflect", "region", "relate", "relation", "remain",
    "remember", "remove", "report", "represent", "require", "research", "resource", "respond",
    "response", "rest", "result", "return", "reveal", "rich", "right", "rise", "risk",
    "road", "rock", "role", "room", "rule", "safe", "same", "save", "scene",
    "school", "science", "scientist", "score", "season", "seat", "second", "section",
    "security", "seek", "seem", "sell", "senate", "send", "senior", "sense",
    "series", "serious", "serve", "service", "seven", "several", "sexual", "shake",
    "share", "shoot", "short", "shot", "should", "shoulder", "show", "side",
    "sign", "significant", "similar", "simple", "simply", "since", "sing", "single",
    "sister", "site", "situation", "size", "skill", "small", "smile", "social",
    "society", "soldier", "some", "somebody", "someone", "something", "sometimes", "son",
    "song", "soon", "sort", "sound", "source", "south", "southern", "space", "speak",
    "special", "specific", "speech", "spend", "spirit", "sport", "spring", "staff",
    "stage", "stand", "standard", "star", "start", "state", "statement", "station",
    "stay", "step", "still", "stock", "stop", "store", "story", "strategy", "street",
    "strength", "strike", "string", "strong", "strongly", "student", "study", "stuff",
    "style", "subject", "success", "successful", "suddenly", "suffer", "suggest", "summer",
    "support", "suppose", "sure", "surface", "system", "table", "take", "talk", "task",
    "tax", "teach", "teacher", "team", "technology", "television", "tell", "temperature",
    "tend", "term", "test", "text", "than", "thank", "that", "their", "them",
    "themselves", "then", "theory", "there", "these", "they", "thing", "think", "third",
    "this", "those", "though", "thought", "thousand", "threat", "three", "through",
    "throughout", "throw", "thus", "time", "today", "together", "tonight", "total",
    "tough", "toward", "town", "trade", "tradition", "train", "training", "travel",
    "treat", "treatment", "tree", "trial", "trip", "trouble", "true", "truth", "turn",
    "type", "under", "understand", "unit", "until", "upon", "usually", "value", "various",
    "very", "victim", "view", "village", "violence", "visit", "voice", "vote", "wait",
    "walk", "wall", "want", "watch", "water", "weapon", "wear", "week", "weight",
    "well", "west", "western", "what", "whatever", "when", "where", "whether", "which",
    "while", "white", "who", "whole", "whom", "whose", "why", "wide", "wife",
    "will", "win", "window", "wish", "with", "within", "without", "woman", "wonder",
    "word", "work", "worker", "world", "worry", "would", "write", "writer", "wrong",
    "yard", "yeah", "year", "yellow", "yes", "yet", "you", "young", "your",
    "yourself", "zero"
]

def batch_import(target_count=300):
    """批量匯入單字"""
    imported = 0
    failed = []
    
    print(f"開始匯入 {target_count} 個單字...")
    
    for i, word in enumerate(COMMON_WORDS[:target_count]):
        # 檢查是否已存在
        if word.lower() in WORD_LIST:
            continue
        
        # 取得定義
        try:
            resp = requests.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data and 'meanings' in data[0]:
                    meaning = data[0]['meanings'][0]['definitions'][0]['definition']
                    part = data[0]['meanings'][0].get('partOfSpeech', 'unknown')
                    
                    # 根據難度分配
                    if i < 100:
                        level = 1
                    elif i < 200:
                        level = 2
                    else:
                        level = 3
                    
                    add_word(word.lower(), meaning, level)
                    imported += 1
                    
                    if imported % 20 == 0:
                        print(f"已匯入 {imported} 個...")
                    
            time.sleep(0.2)
        except Exception as e:
            failed.append(word)
            continue
    
    print(f"\n=== 完成 ===")
    print(f"成功匯入: {imported} 個")
    print(f"失敗: {len(failed)} 個")
    print(f"總單字數: {len(WORD_LIST)}")
    
    return imported, failed

if __name__ == "__main__":
    batch_import(300)