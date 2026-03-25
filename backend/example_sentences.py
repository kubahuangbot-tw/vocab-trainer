"""
例句資料庫 - 單字的用法說明
"""

EXAMPLE_SENTENCES = {
    # Basic
    "hello": "Hello, how are you today?",
    "world": "The world is full of possibilities.",
    "good": "This is a good idea.",
    "morning": "Good morning! Did you sleep well?",
    "night": "Good night, sweet dreams!",
    "thank": "Thank you for your help.",
    "please": "Please open the door.",
    "sorry": "I'm sorry for being late.",
    "yes": "Yes, I agree with you.",
    "no": "No, I don't think so.",
    "love": "I love reading books.",
    "like": "I like playing basketball.",
    "want": "I want to learn English.",
    "need": "I need a new computer.",
    "help": "Can you help me?",
    "eat": "Let's eat dinner together.",
    "drink": "I want to drink water.",
    "sleep": "I need to sleep early tonight.",
    "walk": "Let's walk to the park.",
    "run": "I run every morning.",
    
    # Common
    "beautiful": "The sunset is beautiful.",
    "important": "Education is important.",
    "different": "Each person is different.",
    "difficult": "This problem is difficult.",
    "easy": "This task is easy.",
    "happy": "She looks very happy.",
    "sad": "Don't be sad, everything will be fine.",
    "angry": "He is angry about the news.",
    "tired": "I'm tired after working all day.",
    "busy": "I'm busy with my project.",
    "free": "Are you free this weekend?",
    "ready": "I'm ready to go.",
    "new": "I bought a new phone.",
    "old": "This is an old building.",
    "big": "The house is big enough.",
    "small": "I live in a small apartment.",
    "long": "The movie is very long.",
    "short": "The meeting was short.",
    "hot": "It's very hot today.",
    "cold": "It's cold in winter.",
    "water": "Please drink more water.",
    "food": "I love Japanese food.",
    "house": "This is my house.",
    "home": "Home is where the heart is.",
    "school": "I go to school every day.",
    "work": "I have a lot of work to do.",
    "time": "Time is precious.",
    "money": "Money isn't everything.",
    "people": "Many people like traveling.",
    "family": "I love my family.",
    
    # Intermediate
    "understand": "I understand what you mean.",
    "remember": "I remember that day.",
    "forget": "Don't forget to call me.",
    "learn": "We learn something new every day.",
    "teach": "She teaches English.",
    "study": "I study at the library.",
    "read": "I like to read novels.",
    "write": "I write in my journal every day.",
    "speak": "Can you speak English?",
    "listen": "Listen to this song.",
    "watch": "Let's watch a movie.",
    "think": "I think it's a good plan.",
    "know": "I know the answer.",
    "believe": "I believe in you.",
    "hope": "I hope you feel better.",
    "dream": "Follow your dreams.",
    "decide": "I decide to go abroad.",
    "try": "Try your best.",
    "fail": "Don't be afraid to fail.",
    "success": "Success comes from hard work.",
    "achieve": "Achieve your goals.",
    "improve": "We need to improve our service.",
    "change": "Change is inevitable.",
    "start": "Let's start the meeting.",
    "stop": "Stop talking please.",
    "continue": "Continue your good work.",
    "finish": "When will you finish?",
    "create": "Create something amazing.",
    "build": "Build your future.",
    "destroy": "Don't destroy the environment.",
    
    # Advanced
    "establish": "We need to establish a new system.",
    "implement": "Implement this plan carefully.",
    "evaluate": "Let's evaluate the results.",
    "analyze": "Analyze the data carefully.",
    "comprehend": "Comprehend the main idea.",
    "appreciate": "I appreciate your help.",
    "demonstrate": "Demonstrate your skills.",
    "illustrate": "Illustrate with examples.",
    "distinguish": "Distinguish between right and wrong.",
    "emphasize": "Emphasize the key points.",
    
    # Vocabulary
    "ubiquitous": "Smartphones have become ubiquitous in modern life.",
    "eloquent": "She gave an eloquent speech.",
    "pragmatic": "We need a pragmatic solution.",
    "ambiguous": "The instructions are ambiguous.",
    "resilient": "Children are very resilient.",
}

def get_example_sentence(word):
    """获取單字的例句"""
    return EXAMPLE_SENTENCES.get(word.lower(), f"Example: The word '{word}' is used in many contexts.")

def add_example(word, sentence):
    """添加新的例句"""
    EXAMPLE_SENTENCES[word.lower()] = sentence