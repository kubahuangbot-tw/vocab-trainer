"""
大量匯入單字到 7000+
使用 Free Dictionary API
"""
import requests
import time
import json
from word_list import WORD_LIST, add_word

# 常見英文單字頻率列表 (精選7000個)
# 按頻率排序，越前面越常用
COMMON_WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    "is", "are", "was", "were", "been", "has", "had", "did", "does", "doing",
    "able", "able", "about", "above", "accept", "according", "account", "across", "action", "activity",
    "actual", "actually", "add", "address", "admin", "admit", "adult", "affect", "afford", "afraid",
    "after", "afternoon", "again", "against", "agent", "agree", "agreement", "ahead", "allow", "almost",
    "alone", "along", "already", "also", "although", "always", "american", "among", "amount", "analysis",
    "ancient", "and", "animal", "another", "answer", "anyone", "anything", "appear", "application", "apply",
    "approach", "area", "argue", "arm", "around", "arrive", "art", "article", "artist", "assume",
    "attack", "attend", "audience", "author", "authority", "available", "avoid", "away", "baby", "back",
    "bad", "bag", "ball", "bank", "bar", "base", "basic", "basis", "basket", "bath",
    "battle", "beach", "bear", "beat", "beautiful", "beauty", "because", "become", "bed", "bedroom",
    "before", "begin", "behavior", "behind", "believe", "bell", "belong", "below", "bench", "benefit",
    "best", "better", "between", "beyond", "big", "bill", "billion", "bird", "bit", "black",
    "blame", "blank", "blind", "blood", "blow", "blue", "board", "boat", "body", "boil",
    "bone", "book", "born", "both", "bottle", "bottom", "bowl", "box", "boy", "brain",
    "branch", "brave", "bread", "break", "breast", "breath", "bridge", "bright", "bring", "broken",
    "brother", "brown", "brush", "build", "building", "burn", "bus", "business", "busy", "buy",
    "cake", "calendar", "call", "calm", "camera", "camp", "campaign", "cancer", "candle", "cap",
    "capital", "captain", "card", "care", "careful", "carry", "case", "cash", "cat", "catch",
    "cause", "ceiling", "cell", "cent", "center", "central", "century", "chair", "chance", "change",
    "charge", "chart", "cheap", "check", "chest", "chief", "child", "choice", "choose", "church",
    "city", "claim", "class", "clean", "clear", "climb", "clock", "close", "cloth", "clothes",
    "cloud", "club", "coach", "coal", "coast", "coat", "coffee", "cold", "collect", "college",
    "color", "column", "come", "comment", "common", "community", "company", "compare", "complete", "computer",
    "concern", "condition", "conference", "congress", "connect", "consider", "contain", "continue", "control", "cook",
    "cool", "copy", "corn", "corner", "cost", "cotton", "could", "count", "country", "course",
    "court", "cousin", "cover", "cow", "cream", "crime", "cross", "crowd", "cry", "cup",
    "current", "cut", "dance", "dark", "data", "daughter", "day", "dead", "deal", "dear",
    "death", "debt", "decide", "decision", "deep", "degree", "demand", "depend", "describe", "desert",
    "design", "despite", "detail", "determine", "develop", "development", "dictionary", "die", "difference", "different",
    "difficult", "dinner", "direct", "director", "discover", "discuss", "disease", "dish", "disk", "display",
    "distance", "divide", "doctor", "document", "dog", "dollar", "door", "double", "down", "draw",
    "dream", "dress", "drink", "drive", "drop", "drug", "dry", "duck", "during", "each",
    "ear", "early", "earn", "earth", "east", "easy", "eat", "edge", "effect", "effort",
    "egg", "eight", "either", "eleven", "else", "employ", "empty", "end", "enemy", "energy",
    "engine", "english", "enjoy", "enough", "enter", "entire", "equal", "error", "escape", "establish",
    "even", "evening", "event", "ever", "every", "everyone", "everything", "evidence", "exact", "example",
    "except", "excuse", "exercise", "exist", "expect", "experience", "expert", "explain", "eye", "face",
    "fact", "fail", "fall", "family", "famous", "farm", "fast", "father", "favor", "fear",
    "feed", "feel", "feeling", "few", "field", "fight", "figure", "fill", "film", "final",
    "finally", "find", "fine", "finger", "finish", "fire", "firm", "fish", "fit", "five",
    "fix", "flag", "flat", "flight", "floor", "flow", "flower", "fluid", "fly", "focus",
    "follow", "food", "foot", "football", "force", "forest", "forget", "form", "format", "former",
    "forward", "four", "free", "freedom", "freeze", "fresh", "friend", "fright", "from", "front",
    "fruit", "full", "fun", "function", "fund", "funny", "furniture", "further", "future", "gain",
    "game", "garage", "garden", "gas", "gather", "general", "generation", "gentle", "german", "german",
    "get", "gift", "girl", "give", "glad", "glass", "gold", "good", "govern", "grand",
    "grass", "gray", "great", "green", "gross", "ground", "group", "grow", "growth", "guess",
    "guest", "guide", "guitar", "gun", "guy", "hair", "half", "hall", "hand", "handle",
    "hang", "happen", "happy", "harbor", "hard", "hardware", "harm", "hat", "hate", "have",
    "head", "health", "hear", "heart", "heat", "heaven", "heavy", "height", "held", "hell",
    "help", "here", "hero", "hidden", "high", "hill", "history", "hit", "hold", "hole",
    "holiday", "holy", "home", "honest", "honor", "hook", "hope", "horse", "hospital", "hot",
    "hotel", "hour", "house", "hover", "how", "however", "huge", "human", "hundred", "hungry",
    "hunt", "hurry", "hurt", "ice", "idea", "identify", "image", "imagine", "impact", "import",
    "impose", "impossible", "improve", "include", "income", "increase", "indeed", "indicate", "individual", "industry",
    "inferior", "inform", "information", "inside", "instead", "insult", "intelligence", "intend", "intense", "interest",
    "interfere", "internal", "international", "internet", "interpret", "interview", "into", "introduce", "invade", "invent",
    "invest", "investigate", "invite", "involve", "iron", "island", "issue", "it", "item", "itself",
    "jacket", "jail", "jazz", "jeans", "jerk", "join", "joint", "joke", "joy", "judge",
    "juice", "jump", "junior", "jury", "just", "keen", "keep", "kept", "key", "kick",
    "kid", "kill", "killer", "kind", "king", "kiss", "kitchen", "knee", "knife", "knock",
    "know", "knowledge", "lack", "ladder", "lady", "lake", "lamp", "land", "language", "large",
    "last", "late", "later", "laugh", "launch", "law", "lawn", "lawyer", "lay", "lead",
    "leader", "learn", "least", "leave", "lecture", "left", "leg", "legal", "lemon", "lend",
    "length", "less", "lesson", "let", "letter", "level", "lie", "life", "lift", "light",
    "like", "likely", "limb", "limit", "line", "link", "lion", "lip", "list", "listen",
    "little", "live", "lively", "liver", "living", "load", "loan", "lock", "lonely", "long",
    "look", "loop", "lord", "lose", "loss", "lost", "lot", "loud", "love", "lovely",
    "low", "lower", "luck", "lucky", "lunch", "lung", "machine", "mad", "magazine", "mail",
    "main", "maintain", "major", "majority", "make", "male", "mall", "man", "manage", "manner",
    "manual", "many", "map", "mark", "market", "marriage", "marry", "mass", "master", "match",
    "material", "matter", "maybe", "me", "meal", "mean", "meaning", "meanwhile", "measure", "meat",
    "mechanic", "medal", "medical", "medicine", "meet", "meeting", "member", "memory", "men", "mental",
    "mention", "message", "metal", "method", "middle", "might", "mild", "mile", "milk", "million",
    "mind", "mine", "minister", "minor", "minute", "miss", "missile", "mission", "mistake", "mix",
    "mixture", "mobile", "modern", "modest", "modify", "moment", "monitor", "month", "mood", "moon",
    "more", "morning", "most", "mother", "motion", "motor", "mount", "mountain", "mouse", "mouth",
    "move", "movement", "movie", "much", "multiply", "murder", "muscle", "museum", "music", "must",
    "mysterious", "myself", "nail", "name", "narrow", "nation", "national", "native", "natural", "nature",
    "near", "nearly", "necessary", "neck", "need", "neighbor", "neither", "nerve", "never", "new",
    "news", "newspaper", "next", "nice", "night", "nine", "noble", "nobody", "nod", "noise",
    "noisy", "none", "noodle", "nor", "normal", "north", "northern", "nose", "not", "note",
    "nothing", "notice", "notion", "novel", "now", "nowhere", "nuclear", "nurse", "occur", "ocean",
    "offer", "office", "officer", "official", "often", "oil", "okay", "old", "on", "once",
    "one", "only", "onto", "open", "operate", "opinion", "opponent", "opportunity", "oppose", "opposite",
    "optimistic", "option", "or", "orange", "order", "organ", "organize", "original", "other", "otherwise",
    "ought", "our", "ourselves", "out", "outcome", "output", "outside", "oval", "oven", "over",
    "overall", "overcome", "overlook", "owe", "own", "owner", "pace", "pack", "package", "page",
    "pain", "paint", "painting", "pair", "pan", "panel", "paper", "parent", "park", "part",
    "particular", "partner", "party", "pass", "passage", "passenger", "passion", "passive", "past", "path",
    "patient", "pattern", "pause", "pave", "pay", "peace", "peak", "pen", "pencil", "penny",
    "people", "per", "percent", "perfect", "perform", "perhaps", "period", "permit", "person", "personal",
    "persuade", "pet", "phone", "photo", "phrase", "physical", "piano", "pick", "picnic", "piece",
    "pile", "pilot", "pin", "pink", "pint", "pipe", "pity", "place", "plain", "plan",
    "plane", "plant", "plastic", "plate", "play", "player", "please", "pleased", "pleasure", "plenty",
    "pocket", "poem", "poet", "poetry", "point", "poison", "pole", "police", "polite", "political",
    "politician", "politics", "pollute", "poor", "pop", "popular", "population", "port", "pose", "position",
    "positive", "possible", "possibly", "post", "pot", "potato", "pound", "pour", "powder", "power",
    "practical", "practice", "praise", "predict", "prefer", "prepare", "presence", "present", "preserve", "president",
    "press", "pressure", "pretend", "pretty", "prevent", "prevent", "previous", "price", "pride", "priest",
    "primarily", "primary", "print", "prior", "prison", "private", "prize", "probably", "problem", "procedure",
    "process", "produce", "product", "professional", "professor", "profit", "program", "progress", "project", "prominent",
    "promise", "promote", "promising", "prompt", "proper", "properly", "property", "proposal", "propose", "prospect",
    "protect", "protest", "proud", "prove", "provide", "province", "provision", "provoke", "psychological", "public",
    "pull", "pulse", "pump", "punch", "punish", "purchase", "pure", "purple", "purpose", "pursue",
    "push", "put", "puzzle", "qualify", "quality", "quantity", "quarter", "queen", "question", "quick",
    "quickly", "quiet", "quite", "quote", "race", "radar", "radio", "rail", "rain", "raise",
    "rally", "ranch", "range", "rank", "rapid", "rare", "rate", "rather", "ratio", "reach",
    "react", "read", "reader", "ready", "real", "reality", "realize", "really", "reason", "recall",
    "receive", "recent", "recently", "recipe", "recognize", "record", "recover", "reduce", "refer", "refine",
    "reflect", "reform", "refuse", "regard", "regardless", "regime", "region", "regional", "register", "regret",
    "regular", "regulate", "reinforce", "reject", "relate", "relation", "relative", "relax", "release", "relevant",
    "reliable", "relief", "relieve", "remain", "remarkable", "remember", "remind", "remote", "remove", "render",
    "renew", "rent", "repair", "repeat", "replace", "reply", "report", "represent", "republic", "request",
    "require", "rescue", "research", "reserve", "resign", "resist", "resolve", "resort", "resource", "respect",
    "respond", "response", "responsible", "rest", "restaurant", "restore", "restrict", "result", "resume", "retain",
    "retire", "return", "reveal", "revenue", "reverse", "review", "revise", "revive", "reward", "rhythm",
    "rib", "ribbon", "rice", "rich", "rid", "ride", "ridge", "rifle", "right", "rigid", "ring",
    "riot", "ripe", "rise", "risk", "rival", "river", "road", "roast", "rob", "rock", "role",
    "roll", "roof", "room", "root", "rope", "rose", "rot", "rotate", "rotten", "rough", "round",
    "route", "routine", "row", "rub", "rubber", "rude", "ruin", "rule", "rush", "rust",
    "sacred", "saddle", "sad", "saddle", "sadness", "safe", "safety", "said", "sail", "saint",
    "salad", "sale", "sales", "salt", "same", "sample", "sand", "sang", "sank", "sat",
    "satisfaction", "satisfied", "satisfy", "sauce", "sausage", "save", "say", "scale", "scare",
    "scene", "schedule", "scheme", "school", "science", "scientist", "scope", "score", "scout", "scrape",
    "screen", "screw", "script", "sea", "search", "season", "seat", "second", "secret", "section",
    "sector", "secure", "see", "seed", "seek", "seem", "segment", "seize", "seldom", "select",
    "selection", "self", "sell", "semester", "semiconductor", "senate", "senator", "send", "senior",
    "sensation", "sense", "sensitive", "sentence", "separate", "sequence", "serial", "series", "serious",
    "servant", "serve", "service", "set", "settle", "several", "severe", "sew", "sex", "sexual",
    "shade", "shadow", "shake", "shall", "shallow", "shame", "shape", "share", "sharp", "shave",
    "she", "sheep", "sheet", "shelf", "shell", "shelter", "sheriff", "shield", "shift", "shine",
    "ship", "shirt", "shock", "shoe", "shoot", "shop", "shopping", "shore", "short", "shot",
    "should", "shoulder", "shout", "show", "shower", "shrug", "shut", "shy", "sick", "side",
    "sight", "sign", "signal", "significance", "significant", "silence", "silent", "silver", "similar", "simple",
    "simplify", "simply", "sin", "since", "sing", "singer", "sinking", "sister", "sit", "site",
    "situation", "size", "skate", "sketch", "ski", "skill", "skin", "skirt", "skull", "slave",
    "sleep", "slice", "slide", "slight", "slim", "slip", "slope", "slow", "slowly", "small",
    "smart", "smell", "smile", "smoke", "smooth", "snake", "snap", "snow", "so", "soap",
    "soccer", "social", "society", "soft", "soil", "solar", "soldier", "sole", "solid", "solution",
    "solve", "some", "somebody", "somehow", "someone", "something", "sometimes", "somewhat", "somewhere", "son",
    "song", "soon", "sore", "sorrow", "sorry", "sort", "soul", "sound", "soup", "sour",
    "source", "south", "southeast", "southern", "space", "span", "spare", "speak", "speaker", "special",
    "specific", "speech", "speed", "spell", "spend", "sphere", "spice", "spider", "spin", "spirit",
    "spite", "split", "spoil", "spoke", "sponsor", "spoon", "sport", "spot", "spread", "spring",
    "spy", "square", "squeeze", "stability", "stable", "stack", "staff", "stage", "stain", "stair",
    "stake", "stamp", "stand", "standard", "star", "stare", "start", "state", "station", "statistic",
    "statue", "status", "stay", "steal", "steam", "steel", "steep", "steer", "stem", "step",
    "stereo", "stick", "stiff", "still", "sting", "stir", "stock", "stomach", "stone", "stool",
    "stop", "storage", "store", "storm", "story", "stove", "straight", "strain", "strange", "strap",
    "straw", "stream", "street", "strength", "stress", "stretch", "strict", "strike", "string", "strip",
    "strive", "stroke", "strong", "strongly", "struck", "structure", "struggle", "stubborn", "stuck", "student",
    "studied", "studio", "study", "stuff", "stupid", "style", "subject", "substance", "substantial", "substitute",
    "suburb", "succeed", "success", "successful", "such", "sudden", "suddenly", "suffer", "sugar", "suggest",
    "suggestion", "suit", "sum", "summary", "summer", "sun", "sunny", "super", "superior", "supervise",
    "supplement", "supply", "support", "suppose", "supposed", "supreme", "sure", "surface", "surgeon", "surgery",
    "surplus", "surprise", "surround", "survey", "survival", "survive", "suspect", "suspend", "sustain", "swallow",
    "swear", "sweat", "sweep", "sweet", "swept", "swift", "swim", "swing", "switch", "sword",
    "symbol", "sympathetic", "sympathy", "system", "table", "tablet", "tackle", "tactic", "tag", "tail",
    "take", "tale", "talent", "talk", "tall", "tank", "tap", "tape", "target", "task", "taste",
    "taught", "tax", "taxi", "tea", "teach", "teacher", "team", "tear", "technical", "technique",
    "technology", "teenager", "teeth", "telephone", "television", "tell", "temperature", "temporary", "tempt", "tend",
    "tendency", "tender", "tennis", "tense", "tension", "tent", "term", "terrible", "territory", "test",
    "text", "than", "thank", "that", "the", "theater", "theatre", "theft", "their", "them", "theme",
    "themselves", "then", "theoretical", "theory", "there", "therefore", "these", "they", "thick", "thin",
    "thing", "think", "thinking", "third", "those", "though", "thought", "thread", "threat", "threaten",
    "three", "thrill", "thrive", "throat", "through", "throughout", "throw", "thumb", "thunder", "thus",
    "ticket", "tide", "tidy", "tie", "tight", "till", "time", "tiny", "tip", "tire",
    "tired", "title", "to", "toast", "tobacco", "today", "toe", "together", "toilet", "token",
    "told", "tomato", "tomorrow", "ton", "tone", "tongue", "tonight", "tool", "tooth", "top",
    "topic", "torch", "total", "touch", "tough", "tour", "tourist", "toward", "tower", "town",
    "toy", "trace", "track", "trade", "tradition", "traffic", "tragedy", "trail", "train", "training",
    "transfer", "transform", "transit", "translate", "transmit", "transparent", "transport", "trap", "travel", "tray",
    "treasure", "treat", "treatment", "tree", "tremendous", "trend", "trial", "tribe", "trick", "trigger",
    "trim", "trip", "troop", "trouble", "truck", "truly", "trunk", "trust", "truth", "try",
    "tube", "tuck", "tune", "tunnel", "turn", "tutor", "twelve", "twenty", "twice", "twin",
    "twist", "type", "typical", "ugly", "ultimate", "umbrella", "uncle", "under", "undergo", "understand",
    "undo", "undoubtedly", "unemployment", "unexpected", "unfair", "unhappy", "uniform", "union", "unique", "unit",
    "unite", "unity", "universal", "universe", "university", "unknown", "unless", "unlike", "until", "unusual",
    "up", "update", "upgrade", "upon", "upper", "upset", "upstairs", "urban", "urge", "usage",
    "use", "used", "useful", "usual", "utility", "vacation", "vacuum", "vague", "valid", "valley",
    "valuable", "value", "van", "vanish", "variable", "variation", "variety", "various", "vary", "vast",
    "vegetable", "vehicle", "vein", "venture", "verb", "verify", "version", "vertical", "very", "vessel",
    "vest", "veteran", "via", "victim", "victory", "video", "view", "village", "violate", "violence",
    "violent", "violin", "virtual", "virtue", "virus", "vision", "visit", "visual", "vital", "vitamin",
    "vivid", "vocabulary", "voice", "volcano", "volume", "voluntary", "volunteer", "vote", "voyage", "wage",
    "wait", "wake", "walk", "wall", "wander", "want", "war", "warm", "warn", "warrant", "wash",
    "waste", "watch", "water", "wave", "way", "weak", "wealth", "weapon", "wear", "weather",
    "web", "wedding", "week", "weekend", "weekly", "weigh", "weight", "weird", "welcome", "weld",
    "welfare", "well", "west", "western", "wet", "what", "whatever", "wheat", "wheel", "when",
    "whenever", "where", "wherever", "whether", "which", "while", "whisper", "whistle", "white", "who",
    "whoever", "whole", "whom", "whose", "why", "wide", "widely", "wife", "wild", "will",
    "willing", "win", "wind", "window", "wine", "wing", "winner", "winter", "wire", "wisdom",
    "wise", "wish", "with", "withdraw", "within", "without", "witness", "woman", "wonder", "wonderful",
    "wood", "wooden", "wool", "word", "work", "worker", "world", "worm", "worry", "worse",
    "worst", "worth", "would", "wound", "wrap", "wrist", "write", "writing", "wrong", "yard",
    "yeah", "year", "yell", "yellow", "yes", "yet", "yield", "you", "young", "your", "yours",
    "yourself", "youth", "zero", "zone"
]

def batch_import(target_count=7000):
    """批量匯入單字"""
    imported = 0
    skipped = 0
    failed = []
    
    # 現有單字
    existing = set(w.lower() for w in WORD_LIST.keys())
    
    print(f"開始匯入目標 {target_count} 個單字...")
    print(f"現有單字: {len(existing)}")
    
    # 進度檔
    progress_file = "/home/deck/study/vocab_trainer/data/import_progress.json"
    start_idx = 0
    
    try:
        with open(progress_file, 'r') as f:
            start_idx = json.load(f).get('index', 0)
            print(f"從進度 {start_idx} 繼續")
    except:
        pass
    
    for i, word in enumerate(COMMON_WORDS[start_idx:target_count], start_idx):
        word = word.lower().strip()
        
        if word in existing:
            skipped += 1
            continue
        
        try:
            resp = requests.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data and 'meanings' in data[0]:
                    # 取第一個定義
                    meaning = data[0]['meanings'][0]['definitions'][0]['definition']
                    part = data[0]['meanings'][0].get('partOfSpeech', 'unknown')
                    
                    # 根據單字頻率分配難度
                    if i < 1000:
                        level = 1  # 最常用
                    elif i < 3000:
                        level = 2  # 常用
                    elif i < 5000:
                        level = 3  # 中級
                    else:
                        level = 4  # 進階
                    
                    add_word(word, meaning, level)
                    imported += 1
                    existing.add(word)
                    
                    if imported % 50 == 0:
                        print(f"  進度: {imported} 個成功, {skipped} 跳過")
                        
                        # 儲存進度
                        with open(progress_file, 'w') as f:
                            json.dump({'index': i}, f)
                            
        except Exception as e:
            failed.append(word)
        
        # 避免太快
        time.sleep(0.15)
        
        # 每100個儲存一次進度
        if i % 100 == 0:
            with open(progress_file, 'w') as f:
                json.dump({'index': i}, f)
    
    print(f"\n=== 完成 ===")
    print(f"成功: {imported}")
    print(f"跳過: {skipped}")
    print(f"失敗: {len(failed)}")
    print(f"總單字數: {len(WORD_LIST)}")
    
    return imported, skipped

if __name__ == "__main__":
    batch_import(7000)