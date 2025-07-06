import pygame
import sys
import os
import json
import random
import csv
import Levenshtein
import joblib
from sklearn.linear_model import SGDClassifier
import speech_recognition as sr

pygame.init()

# === WINDOW ===
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("LexisPlay")

# === COLORS ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
GREEN = (0, 200, 0)
RED = (200, 50, 50)
YELLOW = (255, 255, 0)
BLUE = (50, 50, 200)

# === FILES ===
WORDS_FILE = "words.json"
ATTEMPTS_FILE = "attempts.json"
MODEL_FILE = "word_feedback_model.joblib"
TRAINING_LOG = "training_log.csv"
classes = ["correct", "almost", "incorrect"]

# === FONTS ===
def get_fonts(height):
    large = max(30, height // 10)
    small = max(16, height // 30)
    return pygame.font.Font(None, large), pygame.font.Font(None, small)

# === WORDS ===
if os.path.exists(WORDS_FILE):
    with open(WORDS_FILE) as f:
        words = json.load(f)
else:
    words = {
        "easy": [{"word": "apple"}, {"word": "hello"}, {"word": "joy"}],
        "difficult": [{"word": "butterfly"}, {"word": "chocolate"}, {"word": "scissors"}]
    }
    with open(WORDS_FILE, "w") as f:
        json.dump(words, f, indent=2)

# === ATTEMPTS ===
if os.path.exists(ATTEMPTS_FILE):
    with open(ATTEMPTS_FILE) as f:
        attempts_db = json.load(f)
else:
    attempts_db = {"easy": {}, "difficult": {}}

for diff in ["easy", "difficult"]:
    for w in words[diff]:
        if w["word"] not in attempts_db[diff]:
            attempts_db[diff][w["word"]] = 0
with open(ATTEMPTS_FILE, "w") as f:
    json.dump(attempts_db, f, indent=2)

# === MODEL ===
if os.path.exists(MODEL_FILE):
    model = joblib.load(MODEL_FILE)
else:
    model = SGDClassifier(loss="log_loss")
    model.partial_fit([[0, 1], [1, 0], [0.5, 0.5]], ["correct", "incorrect", "almost"], classes=classes)

# === HELPERS ===
def draw_gradient_background(screen, width, height, start_color, end_color):
    for y in range(height):
        ratio = y / height
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))

def draw_text(text, font, color, x, y):
    txt = font.render(text, True, color)
    rect = txt.get_rect(center=(x, y))
    screen.blit(txt, rect)

# === ML ===
def levenshtein(a, b):
    return Levenshtein.distance(a, b)

def bigram_similarity(a, b):
    def get_bigrams(w):
        return set(w[i:i+2] for i in range(len(w)-1)) if len(w) >= 2 else {w}
    A = get_bigrams(a)
    B = get_bigrams(b)
    return len(A & B) / len(A | B) if A | B else 0

def combined_feedback(user, correct):
    d = levenshtein(user, correct)
    s = bigram_similarity(user, correct)
    if d == 0 or s >= 0.9:
        return "correct"
    elif d == 1 or s >= 0.7:
        return "almost"
    else:
        return "incorrect"

def log_attempt(user, correct, lev, bigram, label):
    with open(TRAINING_LOG, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([user, correct, lev, bigram, label])

# === SYLLABLE SPLIT ===
def split_syllables(word):
    vowels = "aeiou"
    count = 0
    prev = False
    for c in word:
        if c in vowels:
            if not prev:
                count += 1
                prev = True
        else:
            prev = False
    return ["syll"] * max(count, 1)

# === ADD WORD MENU ===
def add_word_menu():
    input_box = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 40)
    color = pygame.Color('gray')
    active = False
    text = ''
    adding = True

    while adding:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(e.pos):
                    active = not active
                else:
                    active = False
            elif e.type == pygame.KEYDOWN and active:
                if e.key == pygame.K_RETURN:
                    word = text.strip().lower()
                    if word:
                        sylls = len(split_syllables(word))
                        diff = "easy" if sylls <= 2 else "difficult"
                        words[diff].append({"word": word})
                        with open(WORDS_FILE, "w") as f:
                            json.dump(words, f, indent=2)
                        adding = False
                elif e.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += e.unicode

        draw_gradient_background(screen, WIDTH, HEIGHT, WHITE, (200, 200, 255))
        _, FONT_SMALL = get_fonts(HEIGHT)
        draw_text("Add new word:", FONT_SMALL, BLACK, WIDTH//2, HEIGHT//2 - 40)
        pygame.draw.rect(screen, color, input_box, 2)
        txt2 = FONT_SMALL.render(text, True, BLACK)
        screen.blit(txt2, (input_box.x+5, input_box.y+5))
        pygame.display.flip()

# === MIC ===
def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak now...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio).lower()
    except:
        return input("Could not recognize. Type word: ").strip().lower()

# === MENU ===
def menu():
    running = True
    while running:
        screen.fill(WHITE)
        _, FONT_SMALL = get_fonts(HEIGHT)
        btn_w, btn_h = 160, 40
        btn_x = WIDTH // 2 - btn_w // 2

        easy_btn = pygame.Rect(btn_x, 200, btn_w, btn_h)
        diff_btn = pygame.Rect(btn_x, 250, btn_w, btn_h)
        add_btn = pygame.Rect(btn_x, 300, btn_w, btn_h)
        quit_btn = pygame.Rect(btn_x, 350, btn_w, btn_h)

        pygame.draw.rect(screen, GREEN, easy_btn)
        pygame.draw.rect(screen, RED, diff_btn)
        pygame.draw.rect(screen, GRAY, add_btn)
        pygame.draw.rect(screen, GRAY, quit_btn)

        draw_text("Easy", FONT_SMALL, WHITE, easy_btn.centerx, easy_btn.centery)
        draw_text("Difficult", FONT_SMALL, WHITE, diff_btn.centerx, diff_btn.centery)
        draw_text("Add Word", FONT_SMALL, BLACK, add_btn.centerx, add_btn.centery)
        draw_text("Quit", FONT_SMALL, BLACK, quit_btn.centerx, quit_btn.centery)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if easy_btn.collidepoint(e.pos):
                    main_game("easy")
                elif diff_btn.collidepoint(e.pos):
                    main_game("difficult")
                elif add_btn.collidepoint(e.pos):
                    add_word_menu()
                elif quit_btn.collidepoint(e.pos):
                    pygame.quit(); sys.exit()

# === GAME ===
def main_game(diff):
    idx = 0
    running = True
    shuffle_btn = pygame.Rect(10, 50, 90, 30)

    while running:
        FONT_BIG, FONT_SMALL = get_fonts(HEIGHT)
        draw_gradient_background(screen, WIDTH, HEIGHT, WHITE, (200, 200, 255))
        word = words[diff][idx]["word"]
        draw_text(word, FONT_BIG, BLUE, WIDTH//2, HEIGHT//3)

        # Shuffle button
        pygame.draw.rect(screen, GRAY, shuffle_btn)
        draw_text("Shuffle", FONT_SMALL, BLACK, shuffle_btn.centerx, shuffle_btn.centery)

        # Right-side buttons
        speak_btn = pygame.Rect(WIDTH - 200, 150, 180, 40)
        mic_btn = pygame.Rect(WIDTH - 200, 200, 180, 40)
        ai_assist_btn = pygame.Rect(WIDTH - 200, 250, 180, 40)
        ai_help_btn = pygame.Rect(WIDTH - 200, 300, 180, 40)

        pygame.draw.rect(screen, GRAY, speak_btn)
        pygame.draw.rect(screen, GRAY, mic_btn)
        pygame.draw.rect(screen, GRAY, ai_assist_btn)
        pygame.draw.rect(screen, GRAY, ai_help_btn)

        draw_text("Speak Word", FONT_SMALL, BLACK, speak_btn.centerx, speak_btn.centery)
        draw_text("Mic", FONT_SMALL, BLACK, mic_btn.centerx, mic_btn.centery)
        draw_text("AI Assist", FONT_SMALL, BLACK, ai_assist_btn.centerx, ai_assist_btn.centery)
        draw_text("AI Help", FONT_SMALL, BLACK, ai_help_btn.centerx, ai_help_btn.centery)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                joblib.dump(model, MODEL_FILE)
                pygame.quit(); sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if shuffle_btn.collidepoint(e.pos):
                    random.shuffle(words[diff])
                    idx = 0
                elif speak_btn.collidepoint(e.pos):
                    os.system(f'espeak "{word}"')
                elif mic_btn.collidepoint(e.pos):
                    user = recognize_speech()
                    lev = levenshtein(user, word)
                    bigram = bigram_similarity(user, word)
                    label = combined_feedback(user, word)
                    model.partial_fit([[lev, bigram]], [label])
                    log_attempt(user, word, lev, bigram, label)
                    joblib.dump(model, MODEL_FILE)

                    print(f"You said: {user} → {label}")

                    attempts_db[diff][word] = attempts_db[diff].get(word, 0) + 1
                    with open(ATTEMPTS_FILE, "w") as f:
                        json.dump(attempts_db, f, indent=2)

                    idx = (idx + 1) % len(words[diff])

                elif ai_assist_btn.collidepoint(e.pos):
                    os.system(f'espeak "Try again. Say it slowly."')
                elif ai_help_btn.collidepoint(e.pos):
                    os.system(f'espeak "The word is {word}"')

# === GO ===
menu()
