"""
快速匯入常用單字 - 精選150個基礎單字
"""
import requests
import time
from word_list import WORD_LIST, add_word

# 精選150個常用單字
QUICK_WORDS = [
    ("able", 1), ("about", 1), ("above", 1), ("accept", 2), ("account", 2), ("across", 1),
    ("action", 2), ("activity", 2), ("actually", 2), ("address", 2), ("adult", 2),
    ("affect", 2), ("after", 1), ("again", 1), ("against", 2), ("air", 1), ("all", 1),
    ("allow", 2), ("almost", 2), ("alone", 2), ("along", 1), ("already", 2), ("also", 1),
    ("always", 2), ("american", 2), ("among", 2), ("amount", 2), ("analysis", 3),
    ("animal", 1), ("answer", 1), ("anyone", 1), ("anything", 1), ("appear", 2),
    ("apply", 2), ("approach", 2), ("area", 2), ("argue", 2), ("around", 1),
    ("arrive", 2), ("article", 2), ("artist", 2), ("assume", 2), ("attack", 2),
    ("attention", 2), ("audience", 2), ("author", 2), ("authority", 3), ("available", 2),
    ("avoid", 2), ("away", 1), ("baby", 1), ("back", 1), ("ball", 1), ("bank", 1),
    ("base", 1), ("beat", 1), ("beautiful", 2), ("because", 1), ("become", 2),
    ("before", 1), ("begin", 2), ("behavior", 3), ("behind", 1), ("believe", 2),
    ("benefit", 2), ("best", 1), ("better", 2), ("between", 2), ("bill", 2),
    ("black", 1), ("blood", 2), ("blue", 1), ("board", 1), ("body", 1), ("book", 1),
    ("both", 1), ("boy", 1), ("break", 1), ("bring", 2), ("brother", 1),
    ("budget", 2), ("build", 2), ("building", 2), ("business", 2), ("buy", 1),
    ("call", 1), ("camera", 2), ("campaign", 3), ("cancer", 2), ("capital", 3),
    ("card", 1), ("care", 2), ("career", 2), ("case", 2), ("catch", 2),
    ("cause", 2), ("cell", 2), ("center", 2), ("century", 2), ("certain", 2),
    ("chair", 1), ("challenge", 2), ("chance", 2), ("change", 1), ("charge", 2),
    ("check", 1), ("child", 1), ("choice", 2), ("choose", 2), ("church", 1),
    ("city", 1), ("claim", 2), ("class", 1), ("clear", 1), ("close", 1),
    ("coach", 2), ("cold", 1), ("college", 2), ("color", 1), ("come", 1),
    ("common", 2), ("community", 2), ("company", 2), ("compare", 2), ("computer", 2),
    ("concept", 3), ("concern", 2), ("condition", 2), ("conference", 2),
    ("consider", 2), ("consumer", 2), ("contain", 2), ("continue", 2), ("control", 2),
    ("cost", 2), ("country", 1), ("course", 2), ("court", 2), ("cover", 2),
    ("create", 2), ("crime", 2), ("culture", 2), ("cup", 1), ("current", 2),
    ("customer", 2), ("cut", 1), ("dark", 1), ("data", 2), ("daughter", 1),
    ("dead", 1), ("deal", 1), ("death", 2), ("debate", 2), ("decade", 2),
    ("decide", 2), ("decision", 2), ("deep", 2), ("degree", 2), ("demand", 3),
    ("describe", 2), ("design", 2), ("despite", 2), ("detail", 2), ("determine", 3),
    ("develop", 2), ("difference", 2), ("different", 2), ("difficult", 2), ("dinner", 1),
    ("direct", 2), ("director", 2), ("discover", 2), ("discuss", 2), ("disease", 2),
    ("doctor", 1), ("document", 2), ("dog", 1), ("door", 1), ("down", 1),
    ("draw", 1), ("dream", 1), ("drive", 1), ("drop", 1), ("drug", 2),
    ("during", 1), ("each", 1), ("early", 1), ("east", 1), ("easy", 1),
    ("economic", 3), ("economy", 3), ("edge", 2), ("effect", 2), ("effort", 2),
    ("either", 2), ("election", 3), ("employee", 2), ("end", 1), ("energy", 2),
    ("enjoy", 2), ("enough", 1), ("enter", 2), ("environment", 3), ("equal", 2),
    ("error", 2), ("escape", 2), ("establish", 3), ("even", 1), ("event", 2),
    ("ever", 1), ("every", 1), ("everyone", 1), ("evidence", 2), ("exact", 2),
    ("example", 2), ("except", 2), ("exercise", 2), ("exist", 2), ("experience", 2),
    ("expert", 2), ("explain", 2), ("eye", 1), ("face", 1), ("fact", 1),
    ("factor", 3), ("fail", 2), ("fall", 1), ("family", 1), ("famous", 2),
    ("fast", 1), ("father", 1), ("fear", 2), ("feel", 1), ("feeling", 2),
    ("field", 2), ("fight", 1), ("figure", 2), ("fill", 1), ("film", 1),
    ("final", 2), ("financial", 3), ("find", 1), ("finger", 1), ("finish", 2),
    ("fire", 1), ("firm", 2), ("first", 1), ("fish", 1), ("floor", 1),
    ("focus", 2), ("follow", 1), ("food", 1), ("foot", 1), ("force", 2),
    ("foreign", 2), ("forget", 2), ("form", 1), ("forward", 2), ("found", 2),
    ("free", 1), ("freedom", 2), ("friend", 1), ("front", 1), ("full", 1),
    ("function", 3), ("future", 2), ("game", 1), ("garden", 1), ("general", 2),
    ("generation", 3), ("girl", 1), ("give", 1), ("glass", 1), ("goal", 2),
    ("good", 1), ("government", 2), ("ground", 1), ("group", 2), ("grow", 1),
    ("guess", 1), ("gun", 1), ("guy", 1), ("hair", 1), ("half", 1),
    ("hand", 1), ("happen", 1), ("happy", 1), ("hard", 1), ("have", 1),
    ("head", 1), ("health", 2), ("hear", 1), ("heart", 1), ("heat", 1),
    ("help", 1), ("here", 1), ("high", 1), ("history", 2), ("hold", 1),
    ("home", 1), ("hope", 2), ("hospital", 1), ("hotel", 1), ("hour", 1),
    ("house", 1), ("however", 2), ("human", 2), ("hundred", 1), ("husband", 1),
    ("idea", 2), ("identify", 3), ("image", 2), ("imagine", 2), ("impact", 3),
    ("important", 2), ("improve", 3), ("include", 2), ("increase", 2), ("indeed", 2),
    ("indicate", 3), ("individual", 2), ("industry", 3), ("information", 2),
    ("inside", 1), ("instead", 2), ("interest", 2), ("interview", 2), ("into", 1),
    ("invest", 2), ("involve", 2), ("issue", 2), ("itself", 2), ("join", 1),
    ("just", 1), ("keep", 1), ("kill", 2), ("kind", 1), ("know", 1),
    ("knowledge", 3), ("land", 1), ("language", 2), ("large", 1), ("last", 1),
    ("late", 1), ("later", 2), ("laugh", 1), ("law", 2), ("lawyer", 2),
    ("lead", 2), ("leader", 2), ("learn", 1), ("least", 2), ("leave", 1),
    ("left", 1), ("legal", 3), ("less", 2), ("letter", 1), ("level", 2),
    ("life", 1), ("light", 1), ("like", 1), ("likely", 2), ("line", 1),
    ("list", 1), ("listen", 1), ("little", 1), ("live", 1), ("local", 2),
    ("long", 1), ("look", 1), ("lose", 1), ("loss", 2), ("love", 1),
    ("machine", 2), ("magazine", 2), ("main", 1), ("major", 2), ("make", 1),
    ("male", 2), ("man", 1), ("manage", 2), ("management", 3), ("manager", 2),
    ("many", 1), ("market", 2), ("marriage", 2), ("material", 2), ("matter", 2),
    ("maybe", 1), ("mean", 1), ("measure", 2), ("media", 2), ("medical", 2),
    ("meet", 1), ("meeting", 2), ("member", 2), ("memory", 2), ("mention", 2),
    ("message", 2), ("method", 3), ("middle", 1), ("might", 1), ("military", 3),
    ("mind", 1), ("minute", 1), ("miss", 1), ("mission", 2), ("model", 2),
    ("modern", 2), ("moment", 2), ("money", 2), ("month", 1), ("more", 1),
    ("morning", 1), ("most", 1), ("mother", 1), ("move", 1), ("movement", 2),
    ("movie", 1), ("much", 1), ("music", 1), ("must", 1), ("myself", 1),
    ("name", 1), ("nation", 2), ("national", 2), ("natural", 2), ("nature", 2),
    ("near", 1), ("nearly", 2), ("necessary", 2), ("need", 1), ("network", 2),
    ("never", 1), ("news", 1), ("newspaper", 2), ("next", 1), ("nice", 1),
    ("night", 1), ("none", 1), ("normal", 2), ("north", 1), ("note", 1),
    ("nothing", 1), ("notice", 2), ("now", 1), ("number", 1), ("occur", 2),
    ("offer", 2), ("office", 1), ("officer", 2), ("official", 2), ("often", 2),
    ("once", 1), ("only", 1), ("onto", 1), ("open", 1), ("operation", 3),
    ("opinion", 2), ("order", 1), ("organization", 3), ("other", 1), ("others", 1),
    ("outside", 1), ("over", 1), ("own", 1), ("owner", 2), ("page", 1),
    ("pain", 2), ("paper", 1), ("parent", 2), ("part", 1), ("particular", 3),
    ("partner", 2), ("party", 1), ("pass", 1), ("past", 1), ("patient", 2),
    ("pattern", 3), ("peace", 2), ("people", 1), ("perform", 2), ("perhaps", 2),
    ("period", 2), ("permit", 2), ("person", 1), ("personal", 2), ("phone", 1),
    ("physical", 3), ("pick", 1), ("picture", 1), ("piece", 1), ("place", 1),
    ("plan", 1), ("plant", 1), ("play", 1), ("player", 1), ("please", 1),
    ("point", 1), ("police", 2), ("policy", 3), ("political", 3), ("politics", 3),
    ("poor", 1), ("popular", 2), ("population", 3), ("position", 2), ("positive", 3),
    ("possible", 2), ("power", 2), ("practice", 2), ("prepare", 2), ("present", 2),
    ("president", 2), ("press", 2), ("pressure", 3), ("pretty", 1), ("prevent", 2),
    ("price", 2), ("private", 2), ("probably", 2), ("problem", 1), ("process", 3),
    ("produce", 2), ("product", 2), ("program", 2), ("project", 2), ("property", 3),
    ("protect", 2), ("prove", 2), ("provide", 2), ("public", 1), ("pull", 1),
    ("purpose", 2), ("push", 1), ("quality", 3), ("question", 1), ("quickly", 2),
    ("quite", 1), ("race", 1), ("radio", 1), ("raise", 2), ("range", 2),
    ("rate", 2), ("rather", 2), ("reach", 2), ("read", 1), ("ready", 1),
    ("real", 1), ("reality", 2), ("realize", 2), ("really", 1), ("reason", 2),
    ("receive", 2), ("recent", 2), ("recognize", 3), ("record", 2), ("reduce", 3),
    ("region", 3), ("relate", 2), ("remain", 2), ("remember", 2), ("remove", 2),
    ("report", 2), ("represent", 3), ("require", 2), ("research", 3),
    ("resource", 3), ("respond", 2), ("response", 3), ("rest", 1), ("result", 2),
    ("return", 1), ("reveal", 3), ("rich", 2), ("right", 1), ("rise", 1),
    ("risk", 2), ("road", 1), ("rock", 1), ("role", 2), ("room", 1),
    ("rule", 2), ("safe", 1), ("same", 1), ("save", 1), ("scene", 2),
    ("school", 1), ("science", 2), ("scientist", 3), ("score", 2), ("season", 1),
    ("seat", 1), ("second", 1), ("section", 2), ("security", 3), ("seek", 2),
    ("seem", 1), ("sell", 1), ("senate", 3), ("send", 1), ("senior", 3),
    ("sense", 2), ("series", 3), ("serious", 2), ("serve", 2), ("service", 2),
    ("seven", 1), ("several", 2), ("sexual", 3), ("shake", 1), ("share", 1),
    ("shoot", 2), ("short", 1), ("should", 1), ("show", 1), ("side", 1),
    ("sign", 2), ("significant", 3), ("similar", 2), ("simple", 1), ("simply", 2),
    ("since", 1), ("sing", 1), ("single", 2), ("sister", 1), ("site", 2),
    ("situation", 3), ("size", 1), ("skill", 2), ("small", 1), ("smile", 1),
    ("social", 2), ("society", 3), ("soldier", 2), ("some", 1), ("somebody", 1),
    ("someone", 1), ("something", 1), ("sometimes", 2), ("son", 1), ("song", 1),
    ("soon", 1), ("sort", 1), ("sound", 1), ("source", 3), ("south", 1),
    ("southern", 2), ("space", 2), ("speak", 1), ("special", 2), ("specific", 3),
    ("speech", 2), ("spend", 1), ("spirit", 2), ("sport", 1), ("spring", 1),
    ("staff", 2), ("stage", 2), ("stand", 1), ("standard", 2), ("star", 1),
    ("start", 1), ("state", 1), ("statement", 2), ("station", 1), ("stay", 1),
    ("step", 1), ("still", 1), ("stock", 2), ("stop", 1), ("store", 1),
    ("story", 1), ("strategy", 3), ("street", 1), ("strength", 3), ("strike", 2),
    ("string", 2), ("strong", 1), ("student", 1), ("study", 1), ("stuff", 2),
    ("style", 2), ("subject", 2), ("success", 2), ("successful", 3), ("suddenly", 2),
    ("suffer", 2), ("suggest", 2), ("summer", 1), ("support", 2), ("suppose", 2),
    ("sure", 1), ("surface", 2), ("system", 2), ("table", 1), ("take", 1),
    ("talk", 1), ("task", 1), ("tax", 2), ("teach", 1), ("teacher", 1),
    ("team", 1), ("technology", 3), ("television", 2), ("tell", 1), ("tend", 2),
    ("term", 2), ("test", 1), ("text", 1), ("than", 1), ("thank", 1),
    ("their", 1), ("them", 1), ("themselves", 2), ("then", 1), ("theory", 3),
    ("there", 1), ("these", 1), ("they", 1), ("thing", 1), ("think", 1),
    ("third", 1), ("this", 1), ("those", 1), ("though", 2), ("thought", 2),
    ("thousand", 1), ("threat", 3), ("three", 1), ("through", 1), ("throughout", 3),
    ("throw", 1), ("thus", 2), ("time", 1), ("today", 1), ("together", 2),
    ("tonight", 2), ("total", 2), ("tough", 2), ("toward", 2), ("town", 1),
    ("trade", 2), ("tradition", 3), ("train", 1), ("training", 2), ("travel", 1),
    ("treat", 2), ("treatment", 3), ("tree", 1), ("trial", 2), ("trip", 1),
    ("trouble", 2), ("true", 1), ("truth", 2), ("turn", 1), ("type", 1),
    ("under", 1), ("understand", 2), ("unit", 2), ("until", 1), ("upon", 2),
    ("usually", 2), ("value", 2), ("various", 3), ("very", 1), ("victim", 3),
    ("view", 1), ("village", 1), ("violence", 3), ("visit", 1), ("voice", 1),
    ("vote", 2), ("wait", 1), ("walk", 1), ("wall", 1), ("want", 1),
    ("watch", 1), ("water", 1), ("weapon", 2), ("wear", 1), ("week", 1),
    ("well", 1), ("west", 1), ("western", 2), ("what", 1), ("whatever", 2),
    ("when", 1), ("where", 1), ("whether", 2), ("which", 1), ("while", 1),
    ("white", 1), ("who", 1), ("whole", 1), ("whom", 2), ("whose", 2),
    ("why", 1), ("wide", 1), ("wife", 1), ("will", 1), ("win", 1),
    ("window", 1), ("wish", 1), ("with", 1), ("within", 2), ("without", 2),
    ("woman", 1), ("wonder", 2), ("word", 1), ("work", 1), ("worker", 2),
    ("world", 1), ("worry", 2), ("would", 1), ("write", 1), ("writer", 2),
    ("wrong", 1), ("yard", 1), ("yeah", 1), ("year", 1), ("yellow", 1),
    ("yes", 1), ("yet", 1), ("you", 1), ("young", 1), ("your", 1),
    ("yourself", 2), ("zero", 1)
]

def quick_import():
    """快速匯入不重複的單字"""
    imported = 0
    skipped = 0
    
    print("開始快速匯入...")
    
    for word, level in QUICK_WORDS:
        if word.lower() in WORD_LIST:
            skipped += 1
            continue
        
        # 嘗試取得定義 (使用簡化的定義)
        try:
            resp = requests.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
                timeout=3
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data and 'meanings' in data[0]:
                    meaning = data[0]['meanings'][0]['definitions'][0]['definition']
                    add_word(word.lower(), meaning, level)
                    imported += 1
        except:
            # 如果查不到定義，跳過
            skipped += 1
        
        time.sleep(0.1)  # 避免太快
    
    print(f"\n=== 完成 ===")
    print(f"成功: {imported}")
    print(f"跳過: {skipped}")
    print(f"總單字數: {len(WORD_LIST)}")
    
    return imported, skipped

if __name__ == "__main__":
    quick_import()