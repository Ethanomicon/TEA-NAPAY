import pygame
import subprocess
import random
import speech_recognition as sr
import json
import os
import time
import re
import sys
import csv
import difflib
import pyttsx3
import joblib
from sklearn.linear_model import SGDClassifier

pygame.init()
tts_engine = pyttsx3.init()

# === ML SETUP (SGDClassifier) ===
MODEL_FILE = "word_feedback_model.joblib"
TRAINING_LOG = "training_log.csv"
classes = ["correct", "almost", "incorrect"]

if os.path.exists(MODEL_FILE):
    model = joblib.load(MODEL_FILE)
else:
    model = SGDClassifier(loss="log_loss")
    model.partial_fit([[0, 1], [1, 0], [0.5, 0.5]], ["correct", "incorrect", "almost"], classes=classes)

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
    file_exists = os.path.isfile(TRAINING_LOG)
    with open(TRAINING_LOG, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["user_attempt", "correct_word", "levenshtein", "bigram_similarity", "label"])
        writer.writerow([user, correct, lev, bigram, label])

def update_model_with_attempt(user_attempt, correct_word):
    lev = levenshtein(user_attempt, correct_word)
    bigram = bigram_similarity(user_attempt, correct_word)
    label = combined_feedback(user_attempt, correct_word)
    model.partial_fit([[lev, bigram]], [label])
    joblib.dump(model, MODEL_FILE)
    log_attempt(user_attempt, correct_word, lev, bigram, label)
    return label

def levenshtein(a, b):
    """Compute Levenshtein distance between two words."""
    if len(a) < len(b):
        return levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    previous_row = list(range(len(b) + 1))
    for i, c1 in enumerate(a):
        current_row = [i + 1]
        for j, c2 in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


MODEL_FILE = "word_feedback_model.joblib"
TRAINING_LOG = "training_log.csv"
classes = ["correct", "almost", "incorrect"]

if os.path.exists(MODEL_FILE):
    model = joblib.load(MODEL_FILE)
else:
    model = SGDClassifier(loss="log_loss")
    model.partial_fit([[0, 1], [1, 0], [0.5, 0.5]], ["correct", "incorrect", "almost"], classes=classes)

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

def update_model_with_attempt(user_attempt, correct_word):
    lev = levenshtein(user_attempt, correct_word)
    bigram = bigram_similarity(user_attempt, correct_word)
    label = combined_feedback(user_attempt, correct_word)
    model.partial_fit([[lev, bigram]], [label])
    joblib.dump(model, MODEL_FILE)
    log_attempt(user_attempt, correct_word, lev, bigram, label)
    return label

def suggest_similar_word(correct_word):
    suggestions = []
    for level_words in words.values():
        for word_data in level_words:
            word = word_data["word"]
            if word != correct_word and word[0] == correct_word[0] and abs(len(word) - len(correct_word)) <= 2:
                suggestions.append(word)
    return random.choice(suggestions) if suggestions else None


# --- BACKGROUND MUSIC SETUP ---
BACKGROUND_MUSIC_FILE = "bgm.ogg"
bgm_muted = False

ACH_POPPED_FILE = "achievement_popped.json"

def load_achievement_popped():
    if os.path.exists(ACH_POPPED_FILE):
        with open(ACH_POPPED_FILE, "r") as f:
            return json.load(f)
    return {}

def save_achievement_popped(achievement_popped):
    try:
        with open(ACH_POPPED_FILE, "w") as f:
            json.dump(achievement_popped, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save achievement_popped.json: {e}")

def reset_achievement_popped():
    if os.path.exists(ACH_POPPED_FILE):
        os.remove(ACH_POPPED_FILE)

def play_bgm(loop=True):
    global bgm_muted
    if not bgm_muted and not pygame.mixer.music.get_busy():
        try:
            pygame.mixer.music.load(BACKGROUND_MUSIC_FILE)
            pygame.mixer.music.play(-1 if loop else 0)
        except pygame.error:
            pass

def stop_bgm():
    pygame.mixer.music.stop()

def set_bgm_mute(mute):
    global bgm_muted
    bgm_muted = mute
    if mute:
        pygame.mixer.music.set_volume(0)
    else:
        pygame.mixer.music.set_volume(1)
        if not pygame.mixer.music.get_busy():
            play_bgm()
# --------------------------------

# Window settings
WIDTH, HEIGHT = 480, 320
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LexisPlay: Word Learning Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 149, 237)
GREEN = (34, 139, 34)
RED = (255, 69, 0)
GRAY = (200, 200, 200)
PURPLE = (128, 0, 128)
YELLOW = (255, 215, 0)

# Sounds
try:
    correct_sound = pygame.mixer.Sound('correct.wav')
    wrong_sound = pygame.mixer.Sound('wrong.wav')
    congrats_sound = pygame.mixer.Sound('congrats.wav')
except pygame.error:
    correct_sound = None
    wrong_sound = None
    congrats_sound = None

def play_sound(sound):
    if sound:
        sound.play()

def congrats_screen():
    global WIDTH, HEIGHT, screen
    stop_bgm()
    if congrats_sound:
        congrats_sound.play()
    import threading
    def run_tts():
        tts_engine.say("Congratulations! You finished this level. Excellent job! Always remember that practice makes perfect.")
        tts_engine.runAndWait()
    tts_thread = threading.Thread(target=run_tts)
    tts_thread.start()
    start_time = pygame.time.get_ticks()
    duration = 10000
    CUSTOM_FONT_SIZE = 25
    font = pygame.font.Font(None, CUSTOM_FONT_SIZE)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                font = pygame.font.Font(None, CUSTOM_FONT_SIZE)
        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))
        draw_text("Congratulations! You finished this level.", font, PURPLE, WIDTH // 2, HEIGHT // 2 - 60)
        draw_text("Excellent job!", font, PURPLE, WIDTH // 2, HEIGHT // 2)
        draw_text("Always remember that practice makes perfect.", font, PURPLE, WIDTH // 2, HEIGHT // 2 + 60)
        pygame.display.flip()
        if pygame.time.get_ticks() - start_time > duration:
            running = False
    tts_thread.join(timeout=0.5)
    play_bgm()

def get_fonts(height):
    large_size = max(20, height // 12)
    small_size = max(14, height // 24)
    hint_size = max(12, height // 30)
    return (
        pygame.font.Font(None, 22),   # FONT_LARGE
        pygame.font.Font(None, 20),   # FONT_SMALL
        pygame.font.Font(None, 12),    # FONT_HINT
    )

def draw_text(text, font, color, x, y, center=True):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(x, y) if center else (x, y))
    screen.blit(rendered, rect)
words = {
    "easy": [
    {"word": "apple"}, {"word": "candle"}, {"word": "button"}, {"word": "sunset"}, {"word": "pencil"},
    {"word": "flower"}, {"word": "window"}, {"word": "rabbit"}, {"word": "jelly"}, {"word": "cookie"},
    {"word": "dollar"}, {"word": "tiger"}, {"word": "butter"}, {"word": "ladder"}, {"word": "hammer"},
    {"word": "doctor"}, {"word": "kitten"}, {"word": "monkey"}, {"word": "paper"}, {"word": "rocket"},
    {"word": "puppy"}, {"word": "yellow"}, {"word": "mirror"}, {"word": "garden"}, {"word": "honey"},
    {"word": "jacket"}, {"word": "lion"}, {"word": "magic"}, {"word": "napkin"}, {"word": "ocean"},
    {"word": "pillow"}, {"word": "rainbow"}, {"word": "supper"}, {"word": "table"}, {"word": "under"},
    {"word": "zebra"}, {"word": "bottle"}, {"word": "basket"}, {"word": "cactus"}, {"word": "carpet"},
    {"word": "closet"}, {"word": "crayon"}, {"word": "dentist"}, {"word": "dragon"}, {"word": "eagle"},
    {"word": "engine"}, {"word": "feather"}, {"word": "helmet"}, {"word": "jungle"}, {"word": "spider"},
    {"word": "cat"}, {"word": "dog"}, {"word": "sun"}, {"word": "pen"}, {"word": "box"},
    {"word": "red"}, {"word": "blue"}, {"word": "rush"}, {"word": "jump"}, {"word": "site"},
    {"word": "bed"}, {"word": "car"}, {"word": "ball"}, {"word": "milk"}, {"word": "fish"},
    {"word": "bird"}, {"word": "tree"}, {"word": "leaf"}, {"word": "cup"}, {"word": "hat"},
    {"word": "shoe"}, {"word": "bag"}, {"word": "door"}, {"word": "clock"}, {"word": "frog"},
    {"word": "star"}, {"word": "rain"}, {"word": "snow"}, {"word": "wind"}, {"word": "fire"},
    {"word": "egg"}, {"word": "fork"}, {"word": "spoon"}, {"word": "plate"}, {"word": "glass"},
    {"word": "nose"}, {"word": "hand"}, {"word": "leg"}, {"word": "eye"}, {"word": "ear"},
    {"word": "top"}, {"word": "net"}, {"word": "zip"}, {"word": "sow"}, {"word": "cow"},
    {"word": "beast"}, {"word": "bus"}, {"word": "ship"}, {"word": "moon"}, {"word": "sky"}
],
    "difficult": [
        {"word": "scissor"},
        {"word": "chocolate"},
        {"word": "butterfly"},
        {"word": "island"},
        {"word": "sign"}
    ]
}

SAVE_FILE = "progress.json"
ATTEMPTS_FILE = "attempts.json"

def load_attempts():
    if os.path.exists(ATTEMPTS_FILE):
        with open(ATTEMPTS_FILE, "r") as f:
            return json.load(f)
    else:
        return {"easy": {}, "difficult": {}}

def save_attempts(attempts):
    try:
        with open(ATTEMPTS_FILE, "w") as f:
            json.dump(attempts, f, indent=2)
    except Exception as e:
        print(f"Error saving attempts.json: {e}")

def reset_attempts():
    if os.path.exists(ATTEMPTS_FILE):
        os.remove(ATTEMPTS_FILE)

def load_progress():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    else:
        return {"easy": 0, "difficult": 0}

def save_progress(progress):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save progress.json: {e}")

def reset_progress():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)

def speak_word(word):
    subprocess.call(['espeak', word])

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
        FONT_SMALL = pygame.font.Font(None, 30)
        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))
        draw_text("Listening... Speak now!", FONT_SMALL, BLACK, WIDTH // 2, HEIGHT // 2)
        pygame.display.flip()
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            result = recognizer.recognize_google(audio).strip().lower()
            return result
        except sr.WaitTimeoutError:
            return "Nothing / No speech detected."
        except sr.UnknownValueError:
            return "A thing that audio can't understand."
        except sr.RequestError as e:
            print(f"RequestError: {e}")
            return "Speech service unavailable. Please check your connection."

def achievements_menu():
    global screen, WIDTH, HEIGHT
    play_bgm()
    running = True
    back_button = pygame.Rect(10, 10, 60, 25)
    reset_button = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 80, 120, 28)
    mute_button = pygame.Rect(WIDTH - 100, 10, 90, 35)
    FONT_LARGE, FONT_SMALL, FONT_HINT = get_fonts(HEIGHT)

    # --- ACHIEVEMENT SOUND ---
    try:
        achievement_sound = pygame.mixer.Sound('achievement.wav')
    except pygame.error:
        achievement_sound = None

    # Popup state
    popup_active = False
    popup_message = ""
    popup_time = 0
    POPUP_DURATION = 2.5  # seconds

    # Load persistent popup "already shown" state
    achievement_popped = load_achievement_popped()

    scroll_y = 0
    is_dragging = False
    drag_offset = 0
    top_margin = 80
    bottom_margin = 80
    scrollbar_width = 18

    clock = pygame.time.Clock()
    while running:
        clock.tick(60)
        # Reload progress and attempts every frame to show reset and new unlocks instantly
        attempts_db = load_attempts()
        progress = load_progress()

        # Build achievements list fresh
        achievements = []
        easy_done = progress.get("easy", 0) >= len(words["easy"])
        achievements.append({
            "name": "Easy Peasy",
            "desc": "Complete all words in Easy level.",
            "unlocked": easy_done
        })
        difficult_done = progress.get("difficult", 0) >= len(words["difficult"])
        achievements.append({
            "name": "Diffi-cool",
            "desc": "Complete all words in Difficult level.",
            "unlocked": difficult_done
        })
        has_5_attempts = any(
            count >= 5 for diff in attempts_db for count in attempts_db[diff].values()
        )
        achievements.append({
            "name": "Practice Makes Perfect",
            "desc": "Get at least 5 attempts on a word.",
            "unlocked": has_5_attempts
        })
        has_10_attempts = any(
            count >= 10 for diff in attempts_db for count in attempts_db[diff].values()
        )
        achievements.append({
            "name": "Trial And Error",
            "desc": "Get at least 10 attempts on a word.",
            "unlocked": has_10_attempts
        })
        for diff in ["easy", "difficult"]:
            all_1 = all(attempts_db.get(diff, {}).get(word_data["word"], 0) == 1 for word_data in words[diff])
            achievements.append({
                "name": f"Excellent User ({diff.title()})",
                "desc": f"Finish all words in the {diff.title()} level with only 1 attempt per word.",
                "unlocked": all_1
            })
        # Progress summary rows
        progress_rows = []
        for i, diff in enumerate(["easy", "difficult"]):
            total_words = len(words[diff])
            completed = progress.get(diff, 0)
            progress_rows.append(f"{diff.capitalize()}: {completed} / {total_words} words completed")

        # Unified scrollable area for progress summary and achievements (centered)
        list_items = []
        for text in progress_rows:
            list_items.append(("progress", text))
        list_items.append(("spacer", None))
        for ach in achievements:
            list_items.append(("achievement", ach))

        ITEM_HEIGHT = 60
        PROGRESS_HEIGHT = 48
        SPACER_HEIGHT = 30

        # Calculate full content height
        content_height = 0
        for typ, data in list_items:
            if typ == "spacer":
                content_height += SPACER_HEIGHT
            elif typ == "progress":
                content_height += PROGRESS_HEIGHT
            else:
                content_height += ITEM_HEIGHT

        view_height = HEIGHT - top_margin - bottom_margin
        max_scroll = max(0, content_height - view_height)

        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))
        draw_text("Achievements / Progress", FONT_LARGE, BLUE, WIDTH // 2, 50)

        y = top_margin - int(scroll_y)

        # Progress summary (centered)
        progress_width = int(WIDTH * 0.6)
        progress_x = (WIDTH - progress_width) // 2
        py = y
        for i, text in enumerate(progress_rows):
            if py + PROGRESS_HEIGHT > top_margin and py < HEIGHT - bottom_margin:
                bar_rect = pygame.Rect(progress_x, py, progress_width, PROGRESS_HEIGHT - 8)
                pygame.draw.rect(screen, (100, 149, 237), bar_rect, border_radius=12)
                draw_text(text, FONT_SMALL, (255,255,255), bar_rect.centerx, bar_rect.centery)
            py += PROGRESS_HEIGHT

        # Achievement boxes (centered)
        ay = y + len(progress_rows) * PROGRESS_HEIGHT + SPACER_HEIGHT
        ach_box_width = int(WIDTH * 0.6)
        ach_x = (WIDTH - ach_box_width) // 2
        for idx, (typ, data) in enumerate(list_items[len(progress_rows)+1:]):
            if typ == "achievement":
                if ay + ITEM_HEIGHT < top_margin:
                    ay += ITEM_HEIGHT
                    continue
                if ay > HEIGHT - bottom_margin:
                    break
                color = (255, 215, 0) if data["unlocked"] else (200, 200, 200)  # Yellow if unlocked
                box_rect = pygame.Rect(ach_x, ay, ach_box_width, ITEM_HEIGHT-8)
                pygame.draw.rect(screen, color, box_rect, border_radius=14)
                pygame.draw.rect(screen, (128,0,128), box_rect, 2, border_radius=14)
                draw_text(data["name"], FONT_SMALL, (128, 0, 128) if data["unlocked"] else (0,0,0), box_rect.centerx, box_rect.top+18, center=True)
                draw_text(data["desc"], FONT_HINT, (40,40,40), box_rect.centerx, box_rect.top+38, center=True)
                # --- POPUP AND SOUND TRIGGER ---
                ach_name = data["name"]
                # Only pop up if unlocked, never shown before, and popup not active
                if data["unlocked"] and not achievement_popped.get(ach_name, False) and not popup_active:
                    popup_active = True
                    popup_message = f"Achievement Unlocked: {data['name']}"
                    popup_time = time.time()
                    if achievement_sound:
                        achievement_sound.stop()
                        achievement_sound.play()
                    achievement_popped[ach_name] = True
                    save_achievement_popped(achievement_popped)
                ay += ITEM_HEIGHT

        # --- DRAW THE POPUP ---
        if popup_active:
            elapsed = time.time() - popup_time
            if elapsed < POPUP_DURATION:
                popup_width = int(WIDTH * 0.6)
                popup_height = 60
                popup_x = (WIDTH - popup_width) // 2
                popup_y = 15
                pygame.draw.rect(screen, (255, 215, 0), (popup_x, popup_y, popup_width, popup_height), border_radius=12)
                pygame.draw.rect(screen, (128, 0, 128), (popup_x, popup_y, popup_width, popup_height), 3, border_radius=12)
                draw_text(popup_message, FONT_SMALL, (0, 0, 0), WIDTH // 2, popup_y + popup_height // 2, center=True)
            else:
                popup_active = False

        # Draw scrollbar to the right of the achievement area
        if max_scroll > 0:
            sb_area = HEIGHT - top_margin - bottom_margin
            bar_height = max(40, int(sb_area * sb_area / content_height))
            sb_track_height = sb_area - bar_height
            if sb_track_height > 0:
                bar_top = top_margin + int((scroll_y / max_scroll) * sb_track_height)
            else:
                bar_top = top_margin
            sb_x = ach_x + ach_box_width + 10
            pygame.draw.rect(screen, (200,200,200), (sb_x, top_margin, scrollbar_width, sb_area), 0, border_radius=8)
            pygame.draw.rect(screen, (128,0,128), (sb_x, bar_top, scrollbar_width, bar_height), 0, border_radius=8)

        # UI Buttons
        pygame.draw.rect(screen, (200,200,200), back_button)
        draw_text("Back", FONT_SMALL, (0,0,0), back_button.centerx, back_button.centery)
        pygame.draw.rect(screen, (255,69,0), reset_button)
        draw_text("Reset Progress", FONT_SMALL, (255,255,255), reset_button.centerx, reset_button.centery)
        pygame.draw.rect(screen, (100,149,237) if not bgm_muted else (200,200,200), mute_button)
        draw_text("Mute" if not bgm_muted else "Unmute", FONT_SMALL, (255,255,255), mute_button.centerx, mute_button.centery)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                reset_button.x = WIDTH // 2 - 100
                reset_button.y = HEIGHT - 100
                mute_button.x = WIDTH - 140
                FONT_LARGE, FONT_SMALL, FONT_HINT = get_fonts(HEIGHT)
                view_height = HEIGHT - top_margin - bottom_margin
                max_scroll = max(0, content_height - view_height)
                scroll_y = min(scroll_y, max_scroll)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    running = False
                elif reset_button.collidepoint(event.pos):
                    reset_progress()
                    reset_achievement_popped()  # Reset achievement popups
                    achievement_popped = {}    # Immediately update UI
                elif mute_button.collidepoint(event.pos):
                    set_bgm_mute(not bgm_muted)
                if max_scroll > 0:
                    ach_box_width = int(WIDTH * 0.6)
                    ach_x = (WIDTH - ach_box_width) // 2
                    sb_area = HEIGHT - top_margin - bottom_margin
                    bar_height = max(40, int(sb_area * sb_area / content_height))
                    sb_track_height = sb_area - bar_height
                    if sb_track_height > 0:
                        bar_top = top_margin + int((scroll_y / max_scroll) * sb_track_height)
                    else:
                        bar_top = top_margin
                    sb_x = ach_x + ach_box_width + 10
                    scrollbar_rect = pygame.Rect(sb_x, bar_top, scrollbar_width, bar_height)
                    if scrollbar_rect.collidepoint(event.pos):
                        is_dragging = True
                        drag_offset = event.pos[1] - bar_top
            elif event.type == pygame.MOUSEBUTTONUP:
                is_dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if is_dragging and max_scroll > 0:
                    sb_area = HEIGHT - top_margin - bottom_margin
                    bar_height = max(40, int(sb_area * sb_area / content_height))
                    sb_track_height = sb_area - bar_height
                    mouse_y = event.pos[1]
                    drag_y = mouse_y - drag_offset
                    drag_y = max(top_margin, min(drag_y, top_margin + sb_track_height))
                    percent = 0 if sb_track_height == 0 else (drag_y - top_margin) / sb_track_height
                    scroll_y = percent * max_scroll
            elif event.type == pygame.MOUSEWHEEL:
                scroll_y -= event.y * 40
                scroll_y = max(0, min(scroll_y, max_scroll))

def database_menu():
    global screen, WIDTH, HEIGHT
    play_bgm()
    running = True
    scroll_offset = 0
    scroll_speed = 1
    max_scroll = 0

    dragging_scrollbar = False
    scrollbar_thumb_rect = pygame.Rect(0, 0, 0, 0)
    drag_offset_y = 0

    back_button = pygame.Rect(10, 10, 60, 25)
    reset_button = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 60, 120, 28)  # moved higher
    mute_button = pygame.Rect(WIDTH - 100, 10, 90, 35)
    FONT_LARGE, FONT_SMALL, _ = get_fonts(HEIGHT)

    while running:
        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))
        draw_text("Attempts Database", FONT_LARGE, PURPLE, WIDTH // 2, HEIGHT // 12)

        pygame.draw.rect(screen, GRAY, back_button)
        draw_text("Back", FONT_SMALL, BLACK, back_button.centerx, back_button.centery)
        pygame.draw.rect(screen, RED, reset_button)
        draw_text("Reset Attempts", FONT_SMALL, WHITE, reset_button.centerx, reset_button.centery)
        pygame.draw.rect(screen, BLUE if not bgm_muted else GRAY, mute_button)
        draw_text("Mute" if not bgm_muted else "Unmute", FONT_SMALL, WHITE, mute_button.centerx, mute_button.centery)

        col_width = WIDTH // 3
        header_y = HEIGHT // 8 + 30
        row_height = 26
        bottom_padding = HEIGHT - reset_button.top  # Align bottom of list above reset button
        max_display_height = HEIGHT - header_y - bottom_padding
        max_display_rows = max_display_height // row_height

        headers = ["Easy", "Difficult"]
        attempts_db = load_attempts()
        easy_words = sorted([w["word"] for w in words["easy"]])
        difficult_words = sorted([w["word"] for w in words["difficult"]])
        max_rows = max(len(easy_words), len(difficult_words))
        max_scroll = max(0, max_rows - max_display_rows)

        for idx, header in enumerate(headers):
            draw_text(header, FONT_SMALL, BLUE, col_width * idx + col_width // 2, header_y)
        pygame.draw.line(screen, BLACK, (col_width * 0.05, header_y + 15), (WIDTH - col_width * 0.05, header_y + 15), 2)

        for row in range(scroll_offset, min(scroll_offset + max_display_rows, max_rows)):
            y = header_y + 25 + (row - scroll_offset) * row_height
            if row < len(easy_words):
                word = easy_words[row]
                attempts = attempts_db.get("easy", {}).get(word, 0)
                draw_text(f"{word}: {attempts}", FONT_SMALL, BLACK, col_width // 2, y)
            if row < len(difficult_words):
                word = difficult_words[row]
                attempts = attempts_db.get("difficult", {}).get(word, 0)
                draw_text(f"{word}: {attempts}", FONT_SMALL, BLACK, col_width * 2 + col_width // 2, y)

        if max_rows > max_display_rows:
            bar_x = WIDTH - 25
            bar_width = 15
            bar_track_y = header_y + 25
            bar_track_height = max_display_height

            pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_track_y, bar_width, bar_track_height))

            scroll_range = max_rows - max_display_rows
            scroll_ratio = scroll_offset / scroll_range if scroll_range > 0 else 0
            thumb_height = max(30, int((max_display_rows / max_rows) * bar_track_height))
            thumb_y = bar_track_y + int((bar_track_height - thumb_height) * scroll_ratio)

            scrollbar_thumb_rect = pygame.Rect(bar_x, thumb_y, bar_width, thumb_height)
            pygame.draw.rect(screen, (50, 100, 255), scrollbar_thumb_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                reset_button.x = WIDTH // 2 - 100
                reset_button.y = HEIGHT - 60
                mute_button.x = WIDTH - 140
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    running = False
                elif reset_button.collidepoint(event.pos):
                    reset_attempts()
                elif mute_button.collidepoint(event.pos):
                    set_bgm_mute(not bgm_muted)
                elif scrollbar_thumb_rect.collidepoint(event.pos):
                    dragging_scrollbar = True
                    drag_offset_y = event.pos[1] - scrollbar_thumb_rect.y
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging_scrollbar = False
            elif event.type == pygame.MOUSEMOTION:
                if dragging_scrollbar:
                    mouse_y = event.pos[1]
                    new_thumb_y = mouse_y - drag_offset_y
                    new_thumb_y = max(bar_track_y, min(bar_track_y + bar_track_height - thumb_height, new_thumb_y))
                    relative_position = (new_thumb_y - bar_track_y) / (bar_track_height - thumb_height)
                    scroll_offset = int(relative_position * (max_rows - max_display_rows))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN and scroll_offset < max_scroll:
                    scroll_offset += scroll_speed
                elif event.key == pygame.K_UP and scroll_offset > 0:
                    scroll_offset -= scroll_speed
            elif event.type == pygame.MOUSEWHEEL:
                if event.y < 0 and scroll_offset < max_scroll:
                    scroll_offset += scroll_speed
                elif event.y > 0 and scroll_offset > 0:
                    scroll_offset -= scroll_speed




def menu():
    global screen, WIDTH, HEIGHT
    play_bgm()
    running = True

    # Final small mute button
    mute_button = pygame.Rect(WIDTH - 80, 8, 65, 22)

    while running:
        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))

        # Small fonts for 480x320 screen
        FONT_LARGE = pygame.font.Font(None, 26)
        FONT_SMALL = pygame.font.Font(None, 14)

        draw_text("LexisPlay", FONT_LARGE, RED, WIDTH // 2, 30)
        draw_text("WORD LEARNING GAME", FONT_SMALL, RED, WIDTH // 2, 50)

        def draw_button_text(text, font, color, rect):
            lines = text.split('\n')
            total_height = sum(font.size(line)[1] for line in lines)
            y_offset = rect.centery - total_height // 2
            for line in lines:
                text_surface = font.render(line, True, color)
                text_rect = text_surface.get_rect(center=(rect.centerx, y_offset + font.get_height() // 2))
                screen.blit(text_surface, text_rect)
                y_offset += font.get_height()

        # --- Button size and position (match Easy level style) ---
        button_width = 160
        button_height = 35
        button_x = WIDTH // 2 - button_width // 2

        start_btn = pygame.Rect(button_x, 80, button_width, button_height)
        achievements_btn = pygame.Rect(button_x, 130, button_width, button_height)
        database_btn = pygame.Rect(button_x, 180, button_width, button_height)
        quit_btn = pygame.Rect(button_x, 230, button_width, button_height)
        mute_button = pygame.Rect(WIDTH - 100, 10, 90, 35)

        # --- Draw each button (match colors used in Easy level) ---
        pygame.draw.rect(screen, (60, 179, 113), start_btn)
        draw_button_text("Start", FONT_LARGE, WHITE, start_btn)

        pygame.draw.rect(screen, (70, 130, 180), achievements_btn)
        draw_button_text("Achievements", FONT_LARGE, WHITE, achievements_btn)

        pygame.draw.rect(screen, (255, 165, 0), database_btn)
        draw_button_text("Database", FONT_LARGE, WHITE, database_btn)

        pygame.draw.rect(screen, (138, 43, 226), quit_btn)
        draw_button_text("Quit", FONT_LARGE, WHITE, quit_btn)

        pygame.draw.rect(screen, (192, 192, 192), mute_button)
        draw_button_text("Mute" if not bgm_muted else "Unmute", FONT_LARGE, BLACK, mute_button)

        draw_text("Group 6 - Alpha Version 2025", FONT_LARGE, BLACK, WIDTH // 2, HEIGHT - 18)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.collidepoint(event.pos):
                    difficulty_menu()
                elif achievements_btn.collidepoint(event.pos):
                    achievements_menu()
                elif database_btn.collidepoint(event.pos):
                    database_menu()
                elif quit_btn.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
                elif mute_button.collidepoint(event.pos):
                    set_bgm_mute(not bgm_muted)
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT))
                mute_button = pygame.Rect(WIDTH - 100, 10, 90, 35)  # re-position after resize


def difficulty_menu():
    global screen, WIDTH, HEIGHT
    play_bgm()
    running = True

    # Smaller buttons for 3.5" screen
    back_button = pygame.Rect(10, 10, 60, 25)
    mute_button = pygame.Rect(WIDTH - 100, 10, 90, 35)

    # Use fixed small fonts
    FONT_LARGE = pygame.font.Font(None, 26)
    FONT_SMALL = pygame.font.Font(None, 14)

    # Button size
    btn_w = 180
    btn_h = 60
    btn_x = WIDTH // 2 - btn_w // 2

    # Positioned vertically with smaller spacing
    easy_btn = pygame.Rect(btn_x, 80, btn_w, btn_h)
    difficult_btn = pygame.Rect(btn_x, 150, btn_w, btn_h)

    while running:
        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))
        draw_text("Choose Difficulty", FONT_LARGE, BLUE, WIDTH // 2, 35)

        # Draw difficulty buttons
        pygame.draw.rect(screen, GREEN, easy_btn)
        draw_text("Easy", FONT_LARGE, WHITE, easy_btn.centerx, easy_btn.centery)

        pygame.draw.rect(screen, RED, difficult_btn)
        draw_text("Difficult", FONT_LARGE, WHITE, difficult_btn.centerx, difficult_btn.centery)

        # Draw UI buttons
        pygame.draw.rect(screen, GRAY, back_button)
        draw_text("Back", FONT_LARGE, BLACK, back_button.centerx, back_button.centery)

        pygame.draw.rect(screen, (105, 105, 105), mute_button)
        draw_text("Mute" if not bgm_muted else "Unmute", FONT_LARGE, BLACK, mute_button.centerx, mute_button.centery)


        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if easy_btn.collidepoint(event.pos):
                    stop_bgm()
                    random.shuffle(words["easy"])
                    main("easy")
                elif difficult_btn.collidepoint(event.pos):
                    stop_bgm()
                    main("difficult")
                elif back_button.collidepoint(event.pos):
                    return
                elif mute_button.collidepoint(event.pos):
                    set_bgm_mute(not bgm_muted)
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT))
                mute_button.x = WIDTH - 80


def split_syllables(word):
    word_lower = word.lower()
    # Unified exceptions dictionary
    syllable_exceptions = {
        "apple": ["app", "poll"],
        "candle": ["can", "dell"],
        "button": ["but", "ton"],
        "sunset": ["sun", "set"],
        "pencil": ["pen", "seal"],
        "flower": ["flah", "where"],
        "window": ["win", "dow"],
        "rabbit": ["rab", "bit"],
        "jelly": ["jell", "e"],
        "cookie": ["cook", "key"],
        "dollar": ["doll", "lar"],
        "tiger": ["tie", "gurr"],
        "butter": ["but", "ter"],
        "ladder": ["lad", "der"],
        "hammer": ["ham", "mer"],
        "doctor": ["doc", "tor"],
        "kitten": ["kit", "ten"],
        "monkey": ["mon", "key"],
        "paper": ["pay", "purr"],
        "rocket": ["rock", "et"],
        "puppy": ["puppy"],
        "yellow": ["yel", "low"],
        "mirror": ["mir", "ror"],
        "garden": ["gar", "den"],
        "honey": ["hon", "e"],
        "jacket": ["jack", "et"],
        "lion": ["lie", "on"],
        "magic": ["ma", "jeek"],
        "napkin": ["nap", "kin"],
        "ocean": ["o", "cean"],
        "pillow": ["pil", "low"],
        "rainbow": ["rain", "baw"],
        "supper": ["sup", "per"],
        "table": ["tay", "ball"],
        "under": ["un", "der"],
        "zebra": ["ze", "bra"],
        "bottle": ["bot", "tle"],
        "basket": ["bas", "ket"],
        "cactus": ["cac", "tus"],
        "carpet": ["car", "pet"],
        "closet": ["claw", "seth"],
        "crayon": ["cray", "on"],
        "dentist": ["den", "tist"],
        "dragon": ["drag", "gon"],
        "eagle": ["e", "gehl"],
        "engine": ["ehn", "gine"],
        "feather": ["feath", "there"],
        "helmet": ["hel", "met"],
        "jungle": ["john", "gehll"],
        "spider": ["spy", "der"],
        "cat": ["cat"],
        "dog": ["dog"],
        "sun": ["sun"],
        "first": ["first"],
        "box": ["box"],
        "red": ["red"],
        "blue": ["blue"],
        "rush": ["rush"],
        "jump": ["jump"],
        "site": ["site"],
        "bed": ["bed"],
        "car": ["car"],
        "ball": ["ball"],
        "milk": ["milk"],
        "fish": ["fish"],
        "bird": ["bird"],
        "tree": ["tree"],
        "leaf": ["leaf"],
        "cup": ["cup"],
        "hat": ["hat"],
        "shoe": ["shoe"],
        "bag": ["bag"],
        "door": ["door"],
        "clock": ["clock"],
        "frog": ["frog"],
        "star": ["star"],
        "rain": ["rain"],
        "snow": ["snow"],
        "wind": ["wind"],
        "fire": ["fire"],
        "egg": ["egg"],
        "fork": ["fork"],
        "spoon": ["spoon"],
        "plate": ["plate"],
        "glass": ["glass"],
        "nose": ["nose"],
        "hand": ["hand"],
        "leg": ["leg"],
        "eye": ["eye"],
        "ear": ["ear"],
        "top": ["top"],
        "set": ["set"],
        "zip": ["zip"],
        "sow": ["sow"],
        "cow": ["cow"],
        "beast": ["beast"],
        "bus": ["bus"],
        "ship": ["ship"],
        "moon": ["moon"],
        "sky": ["sky"],

    # Manual exceptions from your current code
        "mouse": ["mouse"],
        "scissor": ["sci", "ssor"],
        "chocolate": ["choc", "o", "late"],
        "butterfly": ["but", "ter", "fly"]
    }

    if word_lower in syllable_exceptions:
        return syllable_exceptions[word_lower]

    # Default syllable splitting via regex
    syllables = re.findall(r'[^aeiou]*[aeiou]+(?:[^aeiou]*$|[^aeiou](?=[^aeiou]))?', word, re.I)
    return syllables if syllables else [word]

phonetic_map = {
    "apple": "apple", "candle": "candle", "button": "button", "sunset": "sunset", "pencil": "pencil",
    "flower": "flower", "window": "window", "rabbit": "rabbit", "jelly": "jelly", "cookie": "cookie",
    "dollar": "dollar", "tiger": "tiger", "butter": "butter", "ladder": "ladder", "hammer": "hammer",
    "doctor": "doctor", "kitten": "kitten", "monkey": "monkey", "paper": "paper", "rocket": "rocket",
    "puppy": "puppy", "yellow": "yellow", "mirror": "mirror", "garden": "garden", "honey": "honey",
    "jacket": "jacket", "lion": "lion", "magic": "magic", "napkin": "napkin", "ocean": "ocean",
    "pillow": "pillow", "rainbow": "rainbow", "supper": "supper", "table": "table", "under": "under",
    "zebra": "zebra", "bottle": "bottle", "basket": "basket", "cactus": "cactus", "carpet": "carpet",
    "closet": "closet", "crayon": "crayon", "dentist": "dentist", "dragon": "dragon", "eagle": "eagle",
    "engine": "engine", "feather": "feather", "helmet": "helmet", "jungle": "jungle", "spider": "spider",
    "cat": "cat", "dog": "dog", "sun": "sun", "first": "first", "box": "box",
    "red": "red", "blue": "blue", "rush": "rush", "jump": "jump", "site": "site",
    "bed": "bed", "car": "car", "ball": "ball", "milk": "milk", "fish": "fish",
    "bird": "bird", "tree": "tree", "leaf": "leaf", "cup": "cup", "hat": "hat",
    "shoe": "shoe", "bag": "bag", "door": "door", "clock": "clock", "frog": "frog",
    "star": "star", "rain": "rain", "snow": "snow", "wind": "wind", "fire": "fire",
    "egg": "egg", "fork": "fork", "spoon": "spoon", "plate": "plate", "glass": "glass",
    "nose": "nose", "hand": "hand", "leg": "leg", "eye": "eye", "ear": "ear",
    "top": "top", "set": "set", "zip": "zip", "sow": "sow", "cow": "cow",
    "beast": "beast", "bus": "bus", "ship": "ship", "moon": "moon", "sky": "sky"
}

def speak_syllables(word):
    syllables = split_syllables(word)
    for syl in syllables:
        to_speak = phonetic_map.get(syl.lower(), syl)
        tts_engine.say(to_speak)
        tts_engine.runAndWait()
        time.sleep(0.3)



def syllable_feedback(word):
    sylls = split_syllables(word)
    for syl in sylls:
        to_speak = phonetic_map.get(syl.lower(), syl)
        subprocess.call(['espeak', to_speak])
        time.sleep(0.4)
    subprocess.call(['espeak', word])

def get_feedback_color(feedback):
    if "perfect" in feedback.lower() or "awesome" in feedback.lower():
        return (34, 139, 34)
    elif "very close" in feedback.lower() or "great job" in feedback.lower():
        return (255, 140, 0)
    elif "good try" in feedback.lower() or "let's break the word" in feedback.lower():
        return (255, 69, 0)
    elif "didn't hear anything" in feedback.lower():
        return (255, 69, 0)
    else:
        return (0, 0, 0)

def ai_assist_say_back(user_speech):
    if user_speech and user_speech.strip() != "":
        subprocess.call(['espeak', f"You said {user_speech}"])
    else:
        subprocess.call(['espeak', "I didn't hear anything."])

def main(difficulty):
    global screen, WIDTH, HEIGHT
    running = True
    current_word_index = 0
    message = ""
    message_color = BLACK
    hint_shown = False
    ai_hint_display = False
    attempts = 0

    option_rects = []
    current_options = []
    correct_word = ""
    hint = ""

    # Compact buttons for 480x320 screen
    back_button = pygame.Rect(10, 10, 60, 25)
    speak_button = pygame.Rect(WIDTH - 80, 10, 70, 22)
    help_button = pygame.Rect(WIDTH - 80, 75, 70, 22)
    ai_button = pygame.Rect(WIDTH - 80, 110, 70, 22)


    use_mic = (difficulty == "easy" or difficulty == "difficult")
    if use_mic:
        mic_button = pygame.Rect(WIDTH - 80, 42, 70, 22)

    progress = load_progress()
    attempts_db = load_attempts()

    flash_index = None
    flash_color = None
    flash_start_time = 0
    FLASH_DURATION = 500

    syllable_hint = []
    show_congrats = False
    ai_feedback = ""
    ai_feedback_time = 0
    AI_FEEDBACK_DURATION = 8
    ai_user_said = ""
    ai_user_said_time = 0

    def load_word(index):
        nonlocal correct_word, hint, message, message_color, current_options, option_rects, hint_shown, syllable_hint, attempts, ai_hint_display
        nonlocal ai_feedback, ai_feedback_time, ai_user_said, ai_user_said_time
        current_data = words[difficulty][index]
        correct_word = current_data["word"]
        hint = current_data.get("hint", "")
        message = ""
        message_color = BLACK
        hint_shown = False
        ai_hint_display = False
        attempts = attempts_db.get(difficulty, {}).get(correct_word, 0)
        syllable_hint = split_syllables(correct_word)
        ai_feedback = ""
        ai_feedback_time = 0
        ai_user_said = ""
        ai_user_said_time = 0
        if difficulty == "easy" or difficulty == "difficult":
            current_options = []
            option_rects = []
        else:
            current_options = current_data["options"][:]
            random.shuffle(current_options)
            option_rects = []
        return current_options, option_rects

    current_options, option_rects = load_word(current_word_index)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                speak_button.x = WIDTH - 140
                help_button.x = WIDTH - 140
                ai_button.x = WIDTH - 140
                if use_mic:
                    mic_button.x = WIDTH - 140
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if back_button.collidepoint(x, y):
                    play_bgm()
                    running = False
                    return
                if speak_button.collidepoint(x, y):
                    speak_word(correct_word)
                if use_mic and mic_button.collidepoint(x, y):
                    user_speech = recognize_speech()
                    attempts += 1
                    if difficulty not in attempts_db:
                        attempts_db[difficulty] = {}
                    attempts_db[difficulty][correct_word] = attempts
                    save_attempts(attempts_db)
                    if user_speech.strip() == correct_word.lower():
                        play_sound(correct_sound)
                        message = "Correct!"
                        message_color = GREEN
                        pygame.time.delay(700)
                        current_word_index += 1
                        progress[difficulty] = max(progress.get(difficulty, 0), current_word_index)
                        save_progress(progress)
                        if current_word_index >= len(words[difficulty]):
                            congrats_screen()
                            play_bgm()
                            return
                        else:
                            current_options, option_rects = load_word(current_word_index)
                    else:
                            play_sound(wrong_sound)
                            message = f"Try again. You said: \n {user_speech.capitalize()}"
                            message_color = RED

                            # 🔔 NEW: Show decision popup if 8 or more attempts
                            if attempts >= 8:
                                suggested_word = suggest_similar_word(correct_word)
                                if suggested_word:
                                    subprocess.call(
                                        ['espeak', 'Do you want to try another word?'])
                                    popup_font = pygame.font.Font(None, 22)
                                    popup_message = f"Try this similar word: {suggested_word.capitalize()}?"
                                    decision_made = False
                                    stay_on_word = True

                                    # Define button positions
                                    btn_width = 160
                                    btn_height = 40
                                    stay_button = pygame.Rect(WIDTH // 2 - btn_width - 10, HEIGHT // 2 + 40, btn_width,
                                                              btn_height)
                                    skip_button = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2 + 40, btn_width, btn_height)

                                    while not decision_made:
                                        for event in pygame.event.get():
                                            if event.type == pygame.QUIT:
                                                pygame.quit()
                                                sys.exit()
                                            elif event.type == pygame.MOUSEBUTTONDOWN:
                                                if stay_button.collidepoint(event.pos):
                                                    decision_made = True
                                                    stay_on_word = True
                                                elif skip_button.collidepoint(event.pos):
                                                    decision_made = True
                                                    stay_on_word = False

                                        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255),
                                                                 (216, 191, 216))

                                        draw_text("Having trouble with this word?", popup_font, RED, WIDTH // 2,
                                                  HEIGHT // 2 - 40)
                                        draw_text(popup_message, popup_font, BLACK, WIDTH // 2, HEIGHT // 2 - 10)
                                        draw_text("Choose an option below:", popup_font, PURPLE, WIDTH // 2,
                                                  HEIGHT // 2 + 15)

                                        # Draw buttons
                                        pygame.draw.rect(screen, (34, 139, 34), stay_button)
                                        draw_text("Stay on this word", popup_font, WHITE, stay_button.centerx,
                                                  stay_button.centery)

                                        pygame.draw.rect(screen, (255, 140, 0), skip_button)
                                        draw_text("Try another word", popup_font, WHITE, skip_button.centerx,
                                                  skip_button.centery)

                                        pygame.display.flip()

                                    if not stay_on_word:
                                        current_word_index += 1
                                        progress[difficulty] = max(progress.get(difficulty, 0), current_word_index)
                                        save_progress(progress)
                                        if current_word_index >= len(words[difficulty]):
                                            congrats_screen()
                                            play_bgm()
                                            return
                                        else:
                                            current_options, option_rects = load_word(current_word_index)

                if help_button.collidepoint(x, y):
                    speak_syllables(correct_word)
                    message = "Listen carefully to syllables!"
                    message_color = BLACK
                    hint_shown = True
                if ai_button.collidepoint(x, y):
                    user_speech = recognize_speech()
                    ai_feedback_label = update_model_with_attempt(user_speech, correct_word)

                    if ai_feedback_label == "correct":
                        ai_feedback = "Awesome! You said it perfectly!"
                    elif ai_feedback_label == "almost":
                        ai_feedback = "Great job! That was very close. Try again!"
                    else:
                        ai_feedback = "Not quite. Listen to the word and try again!"

                    ai_feedback_time = time.time()
                    ai_user_said = user_speech
                    ai_user_said_time = time.time()
                    ai_assist_say_back(user_speech)
                    subprocess.call(['espeak', ai_feedback])
                    syllable_feedback(correct_word)
                    message = ai_feedback
                    message_color = get_feedback_color(ai_feedback)
                    ai_hint_display = True

        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))
        FONT_LARGE, FONT_SMALL, FONT_HINT = get_fonts(HEIGHT)
        draw_text(f"Difficulty: {difficulty.capitalize()}", FONT_SMALL, BLACK, WIDTH // 2, 40)
        pygame.draw.rect(screen, GRAY, back_button)
        draw_text("Back", FONT_SMALL, BLACK, back_button.centerx, back_button.centery)
        if difficulty == "easy" or difficulty == "difficult":
            draw_text("Say it correctly. Press Mic to start:", FONT_SMALL, BLACK, WIDTH // 2, HEIGHT // 5)
        else:
            draw_text("Choose the correct word:", FONT_SMALL, BLACK, WIDTH // 2, HEIGHT // 5)
        draw_text(correct_word, FONT_LARGE, BLUE, WIDTH // 2, HEIGHT // 3)
        option_rects.clear()

        def draw_button_text(text, font, color, rect):
            lines = text.split('\n')
            total_height = sum(font.size(line)[1] for line in lines)
            y_offset = rect.centery - total_height // 2
            for line in lines:
                text_surface = font.render(line, True, color)
                text_rect = text_surface.get_rect(center=(rect.centerx, y_offset + font.get_height() // 2))
                screen.blit(text_surface, text_rect)
                y_offset += font.get_height()

        # Draw buttons with colors
        pygame.draw.rect(screen, (70, 130, 180), speak_button)
        draw_button_text("Speak\nWord", FONT_LARGE, WHITE, speak_button)

        pygame.draw.rect(screen, (60, 179, 113), mic_button)
        draw_button_text("Mic", FONT_LARGE, WHITE, mic_button)

        pygame.draw.rect(screen, (255, 165, 0), help_button)
        draw_button_text("Syllable", FONT_LARGE, BLACK, help_button)

        pygame.draw.rect(screen, (138, 43, 226), ai_button)
        draw_button_text("AI Assist", FONT_LARGE, WHITE, ai_button)

        # --- Show message (correct/wrong feedback) at bottom ---
        if message:
            lines = message.split('\n')
            for i, line in enumerate(lines):
                draw_text(line, FONT_SMALL, message_color, WIDTH // 2, HEIGHT - 140 + (i * FONT_SMALL.get_height()))

        button_width = 80  # Narrower
        button_height = 40  # Taller
        button_x = WIDTH - button_width - 10  # Keep them 10px from the right edge

        speak_button = pygame.Rect(button_x, 10, button_width, button_height)
        mic_button = pygame.Rect(button_x, 60, button_width, button_height)
        help_button = pygame.Rect(button_x, 110, button_width, button_height)
        ai_button = pygame.Rect(button_x, 160, button_width, button_height)

        # --- AI Assist feedback display, applies to all levels ---
        #if ai_user_said and (time.time() - ai_user_said_time < AI_FEEDBACK_DURATION):
        #    popup_width = WIDTH - 120
        #    popup_height = 40
        #    popup_x = 60
        #    popup_y = HEIGHT - popup_height - 185
        #    pygame.draw.rect(screen, (255, 255, 230), (popup_x, popup_y, popup_width, popup_height))
        #    draw_text(f'You said: "{ai_user_said}"', FONT_SMALL, (128, 0, 128), popup_x + 10, popup_y + popup_height // 2, center=False)
            # if ai_feedback and (time.time() - ai_feedback_time) < AI_FEEDBACK_DURATION:
            # popup_width = WIDTH - 120
            # popup_height = 80
            # popup_x = 60
            # popup_y = HEIGHT - popup_height - 130
            # pygame.draw.rect(screen, (240, 246, 255), (popup_x, popup_y, popup_width, popup_height))
            # draw_text("AI Feedback:", FONT_SMALL, (70, 70, 70), popup_x + 10, popup_y + 18, center=False)
            # draw_text(ai_feedback, FONT_HINT, get_feedback_color(ai_feedback), popup_x + 10, popup_y + popup_height // 2 + 5, center=False)
        if flash_index is not None:
            current_time = pygame.time.get_ticks()
            if current_time - flash_start_time > FLASH_DURATION:
                if flash_color == (0, 255, 0):
                    current_word_index += 1
                    progress[difficulty] = max(progress.get(difficulty, 0), current_word_index)
                    save_progress(progress)
                    if current_word_index >= len(words[difficulty]):
                        congrats_screen()
                        play_bgm()
                        return
                    else:
                        current_options, option_rects = load_word(current_word_index)
                flash_index = None
                flash_color = None

        pygame.display.flip()

        if show_congrats:
            pygame.time.delay(3000)
            play_bgm()
            running = False

def draw_gradient_background(screen, width, height, top_color, bottom_color):
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))

if __name__ == "__main__":
    menu()
