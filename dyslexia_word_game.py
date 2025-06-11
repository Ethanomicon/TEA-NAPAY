import pygame
import pyttsx3
import random
import speech_recognition as sr
import json
import os
import re
import sys
import time
import difflib

pygame.init()

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

# Example "training data" (expand this as desired)
# Each entry: (attempt, correct_word, label)
ml_training_data = [
    ("apple", "apple", "correct"),
    ("aple", "apple", "almost"),
    ("appl", "apple", "almost"),
    ("applle", "apple", "almost"),
    ("appple", "apple", "almost"),
    ("aplee", "apple", "incorrect"),
    ("banana", "banana", "correct"),
    ("bananna", "banana", "almost"),
    ("banan", "banana", "almost"),
    ("benana", "banana", "almost"),
    ("bannana", "banana", "almost"),
    ("bannanna", "banana", "incorrect"),
    ("hello", "hello", "correct"),
    ("helo", "hello", "almost"),
    ("helllo", "hello", "almost"),
    ("heloo", "hello", "almost"),
    ("hallo", "hello", "almost"),
    ("heallo", "hello", "incorrect"),
    # Add more as needed for other words
]

def knn_feedback(user_attempt, correct_word, k=3):
    # Compute distances only for entries with the same correct_word
    distances = []
    for attempt, word, label in ml_training_data:
        if word == correct_word:
            dist = levenshtein(user_attempt, attempt)
            distances.append((dist, label))
    if not distances:
        # Fallback: compare user_attempt to correct_word only
        dist = levenshtein(user_attempt, correct_word)
        if dist == 0:
            return "correct"
        elif dist == 1:
            return "almost"
        else:
            return "incorrect"
    # Sort and pick k nearest
    distances.sort()
    k_nearest = [label for _, label in distances[:k]]
    # Majority vote
    return max(set(k_nearest), key=k_nearest.count)

def get_ml_feedback(user_attempt, correct_word):
    label = knn_feedback(user_attempt, correct_word)
    if label == "correct":
        return "Awesome! You said it perfectly!"
    elif label == "almost":
        return "Great job! That was very close. Try again!"
    else:
        return "Not quite. Listen to the word and try again!"

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
    with open(ACH_POPPED_FILE, "w") as f:
        json.dump(achievement_popped, f)

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
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
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

# Text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)

voices = tts_engine.getProperty('voices')
for voice in voices:
    if 'female' in voice.name.lower() or 'en_us' in voice.id.lower():
        tts_engine.setProperty('voice', voice.id)
        break

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
    CUSTOM_FONT_SIZE = 48
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
    large_size = max(30, height // 10)
    small_size = max(25, height // 20)
    hint_size = max(15, height // 30)
    return (
        pygame.font.Font(None, large_size),
        pygame.font.Font(None, small_size),
        pygame.font.Font(None, hint_size)
    )

def draw_text(text, font, color, x, y, center=True):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(x, y) if center else (x, y))
    screen.blit(rendered, rect)

words = {
    "easy": [
        {"word": "hello"},
        {"word": "apple"},
        {"word": "rocket"},
        {"word": "mouse"},
        {"word": "joy"}
    ],
    "medium": [
        {"word": "basket", "options": ["basset", "bass", "basskit", "basket"], "hint": "A container for carrying things."},
        {"word": "banana", "options": ["bandana", "band", "banana", "ba"], "hint": "A type of fruit."},
        {"word": "potato", "options": ["pot", "potato", "puti", "pothole"], "hint": "A color brown vegetable. You can eat it."},
        {"word": "animal", "options": ["anime", "amen", "animal", "aim"], "hint": "A living thing like cat or dog."},
        {"word": "garden", "options": ["guard", "gear", "garden", "golden"], "hint": "It shows love."}
    ],
    "hard": [
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
        return {"easy": {}, "medium": {}, "hard": {}}

def save_attempts(attempts):
    with open(ATTEMPTS_FILE, "w") as f:
        json.dump(attempts, f, indent=2)

def reset_attempts():
    if os.path.exists(ATTEMPTS_FILE):
        os.remove(ATTEMPTS_FILE)

def load_progress():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    else:
        return {"easy": 0, "medium": 0, "hard": 0}

def save_progress(progress):
    with open(SAVE_FILE, "w") as f:
        json.dump(progress, f)

def reset_progress():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)

def speak_word(word):
    tts_engine.say(word)
    tts_engine.runAndWait()

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
    back_button = pygame.Rect(20, 20, 100, 40)
    reset_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
    mute_button = pygame.Rect(WIDTH - 140, 20, 120, 40)
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
    top_margin = 120
    bottom_margin = 110
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
        medium_done = progress.get("medium", 0) >= len(words["medium"])
        achievements.append({
            "name": "Inter-Medium",
            "desc": "Complete all words in Medium level.",
            "unlocked": medium_done
        })
        hard_done = progress.get("hard", 0) >= len(words["hard"])
        achievements.append({
            "name": "Hardworker",
            "desc": "Complete all words in Hard level.",
            "unlocked": hard_done
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
        for diff in ["easy", "medium", "hard"]:
            all_1 = all(attempts_db.get(diff, {}).get(word_data["word"], 0) == 1 for word_data in words[diff])
            achievements.append({
                "name": f"Excellent User ({diff.title()})",
                "desc": f"Finish all words in the {diff.title()} level with only 1 attempt per word.",
                "unlocked": all_1
            })
        # Progress summary rows
        progress_rows = []
        for i, diff in enumerate(["easy", "medium", "hard"]):
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
        draw_text("Achievements / Progress", FONT_LARGE, BLUE, WIDTH // 2, 70)

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
    back_button = pygame.Rect(20, 20, 100, 40)
    reset_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
    mute_button = pygame.Rect(WIDTH - 140, 20, 120, 40)
    FONT_LARGE, FONT_SMALL, _ = get_fonts(HEIGHT)
    while running:
        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))
        draw_text("Attempts Database", FONT_LARGE, PURPLE, WIDTH // 2, HEIGHT // 8)
        pygame.draw.rect(screen, GRAY, back_button)
        draw_text("Back", FONT_SMALL, BLACK, back_button.centerx, back_button.centery)
        pygame.draw.rect(screen, RED, reset_button)
        draw_text("Reset Attempts", FONT_SMALL, WHITE, reset_button.centerx, reset_button.centery)
        pygame.draw.rect(screen, BLUE if not bgm_muted else GRAY, mute_button)
        draw_text("Mute" if not bgm_muted else "Unmute", FONT_SMALL, WHITE, mute_button.centerx, mute_button.centery)
        col_width = WIDTH // 3
        start_y = HEIGHT // 5
        header_y = start_y
        row_height = 40
        headers = ["Easy", "Medium", "Hard"]
        attempts_db = load_attempts()
        easy_words = [w["word"] for w in words["easy"]]
        medium_words = [w["word"] for w in words["medium"]]
        hard_words = [w["word"] for w in words["hard"]]
        max_rows = max(len(easy_words), len(medium_words), len(hard_words))
        for idx, header in enumerate(headers):
            draw_text(header, FONT_SMALL, BLUE, col_width * idx + col_width // 2, header_y + 15)
        pygame.draw.line(screen, BLACK, (col_width * 0.05, header_y + 30), (WIDTH - col_width * 0.05, header_y + 30), 2)
        for row in range(max_rows):
            y = header_y + 60 + row * row_height
            if row < len(easy_words):
                word = easy_words[row]
                attempts = attempts_db.get("easy", {}).get(word, 0)
                draw_text(f"{word}: {attempts}", FONT_SMALL, BLACK, col_width // 2, y)
            if row < len(medium_words):
                word = medium_words[row]
                attempts = attempts_db.get("medium", {}).get(word, 0)
                draw_text(f"{word}: {attempts}", FONT_SMALL, BLACK, col_width + col_width // 2, y)
            if row < len(hard_words):
                word = hard_words[row]
                attempts = attempts_db.get("hard", {}).get(word, 0)
                draw_text(f"{word}: {attempts}", FONT_SMALL, BLACK, col_width * 2 + col_width // 2, y)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                reset_button.x = WIDTH // 2 - 100
                reset_button.y = HEIGHT - 100
                mute_button.x = WIDTH - 140
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    running = False
                elif reset_button.collidepoint(event.pos):
                    reset_attempts()
                elif mute_button.collidepoint(event.pos):
                    set_bgm_mute(not bgm_muted)

def menu():
    global screen, WIDTH, HEIGHT
    play_bgm()
    running = True
    mute_button = pygame.Rect(WIDTH - 140, 20, 120, 40)
    while running:
        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))
        FONT_LARGE, FONT_SMALL, _ = get_fonts(HEIGHT)
        draw_text("LexisPlay: Word Learning Game", FONT_LARGE, BLUE, WIDTH // 2, HEIGHT // 4)
        start_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 70, 200, 50)
        achievements_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + -10, 200, 50)
        database_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50)
        quit_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 110, 200, 50)
        pygame.draw.rect(screen, GREEN, start_btn)
        pygame.draw.rect(screen, BLUE, achievements_btn)
        pygame.draw.rect(screen, PURPLE, database_btn)
        pygame.draw.rect(screen, RED, quit_btn)
        pygame.draw.rect(screen, BLUE if not bgm_muted else GRAY, mute_button)
        draw_text("Mute" if not bgm_muted else "Unmute", FONT_SMALL, WHITE, mute_button.centerx, mute_button.centery)
        draw_text("Start", FONT_SMALL, WHITE, start_btn.centerx, start_btn.centery)
        draw_text("Achievements", FONT_SMALL, WHITE, achievements_btn.centerx, achievements_btn.centery)
        draw_text("Database", FONT_SMALL, WHITE, database_btn.centerx, database_btn.centery)
        draw_text("Quit", FONT_SMALL, WHITE, quit_btn.centerx, quit_btn.centery)
        draw_text(
            "Created by Nabus et al. - Alpha Version - 2025",
            FONT_SMALL, BLACK, WIDTH // 2, HEIGHT - 35
        )
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
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                mute_button.x = WIDTH - 140

def difficulty_menu():
    global screen, WIDTH, HEIGHT
    play_bgm()
    running = True
    back_button = pygame.Rect(20, 20, 100, 40)
    mute_button = pygame.Rect(WIDTH - 140, 20, 120, 40)
    while running:
        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))
        FONT_LARGE, FONT_SMALL, _ = get_fonts(HEIGHT)
        draw_text("Choose Difficulty", FONT_LARGE, BLUE, WIDTH // 2, HEIGHT // 4)
        easy_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50)
        med_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 10, 200, 50)
        hard_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 50)
        pygame.draw.rect(screen, GREEN, easy_btn)
        pygame.draw.rect(screen, BLUE, med_btn)
        pygame.draw.rect(screen, RED, hard_btn)
        pygame.draw.rect(screen, GRAY, back_button)
        pygame.draw.rect(screen, BLUE if not bgm_muted else GRAY, mute_button)
        draw_text("Easy", FONT_SMALL, WHITE, easy_btn.centerx, easy_btn.centery)
        draw_text("Medium", FONT_SMALL, WHITE, med_btn.centerx, med_btn.centery)
        draw_text("Hard", FONT_SMALL, WHITE, hard_btn.centerx, hard_btn.centery)
        draw_text("Back", FONT_SMALL, BLACK, back_button.centerx, back_button.centery)
        draw_text("Mute" if not bgm_muted else "Unmute", FONT_SMALL, WHITE, mute_button.centerx, mute_button.centery)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if easy_btn.collidepoint(event.pos):
                    stop_bgm()
                    main("easy")
                elif med_btn.collidepoint(event.pos):
                    stop_bgm()
                    main("medium")
                elif hard_btn.collidepoint(event.pos):
                    stop_bgm()
                    main("hard")
                elif back_button.collidepoint(event.pos):
                    return
                elif mute_button.collidepoint(event.pos):
                    set_bgm_mute(not bgm_muted)
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                mute_button.x = WIDTH - 140

def split_syllables(word):
    if word.lower() == "mouse":
        return ["mouse"]
    if word.lower() == "scissor":
        return ["sci", "ssor"]
    if word.lower() == "chocolate":
        return ["choc", "o", "late"]
    if word.lower() == "butterfly":
        return ["but", "ter", "fly"]
    syllables = re.findall(r'[^aeiou]*[aeiou]+(?:[^aeiou]*$|[^aeiou](?=[^aeiou]))?', word, re.I)
    return syllables if syllables else [word]

phonetic_map = {
    "bas": "bus",
    "ket": "ket",
    "ba": "bah",
    "na": "nah",
    "po": "poh",
    "ta": "tay",
    "to": "tow",
    "a": "aah",
    "ni": "knee",
    "mal": "mal",
    "gar": "gar",
    "den": "den",
    "mouse": "mous",
    "ap": "app",
    "ple": "poll",
    "sci": "sea",
    "ssor": "soar",
    "choc": "chok",
    "o": "oh",
    "late": "late",
    "but": "but",
    "ter": "ter",
    "fly": "fly",
    "is": "eye"
}

def speak_syllables(word):
    syllables = split_syllables(word)
    for syl in syllables:
        to_speak = phonetic_map.get(syl.lower(), syl)
        tts_engine.say(to_speak)
        tts_engine.runAndWait()
        time.sleep(0.3)

def split_syllables_medium(word):
    medium_exceptions = {
        "basket": ["bas", "ket"],
        "banana": ["ba", "na", "na"],
        "potato": ["po", "ta", "to"],
        "animal": ["a", "ni", "mal"],
        "garden": ["gar", "den"]
    }
    if word.lower() in medium_exceptions:
        return medium_exceptions[word.lower()]
    return re.findall(r'[^aeiou]*[aeiou]+(?:[^aeiou]*$|[^aeiou](?=[^aeiou]))?', word, re.I)

def speak_syllables_medium(word):
    syllables = split_syllables_medium(word)
    for syl in syllables:
        to_speak = phonetic_map.get(syl.lower(), syl)
        tts_engine.say(to_speak)
        tts_engine.runAndWait()
        time.sleep(0.3)

def get_phonetic_feedback(target, attempt):
    if not attempt or attempt.strip() == "":
        return "I didn't hear anything. Let's try again together!"
    elif attempt.lower() == target.lower():
        return "Awesome! You said it perfectly!"
    ratio = difflib.SequenceMatcher(None, target.lower(), attempt.lower()).ratio()
    if ratio > 0.8:
        return "Great job! That was very close. Try saying each part slowly."
    elif ratio > 0.5:
        return "Good try! That was close. Let's listen and try again."
    else:
        # Changed: Do NOT say "I didn't hear anything" if the user actually said something.
        return "Let's try again together!"

def syllable_feedback(word):
    sylls = split_syllables(word)
    for syl in sylls:
        to_speak = phonetic_map.get(syl.lower(), syl)
        tts_engine.say(to_speak)
        tts_engine.runAndWait()
        time.sleep(0.4)
    tts_engine.say(word)
    tts_engine.runAndWait()

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
    """
    Speak back to the user what was heard.
    """
    if user_speech and user_speech.strip() != "":
        tts_engine.say(f"You said {user_speech}")
        tts_engine.runAndWait()
    else:
        tts_engine.say("I didn't hear anything.")
        tts_engine.runAndWait()

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

    back_button = pygame.Rect(20, 20, 100, 40)
    speak_button = pygame.Rect(WIDTH - 140, 20, 120, 40)
    help_button = pygame.Rect(WIDTH - 140, 140, 120, 40)
    ai_button = pygame.Rect(WIDTH - 140, 200, 120, 40)

    use_mic = (difficulty == "easy" or difficulty == "hard")
    if use_mic:
        mic_button = pygame.Rect(WIDTH - 140, 80, 120, 40)

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
        if difficulty == "easy" or difficulty == "hard":
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
                        message = f"Try again. You said: {user_speech.capitalize()}"
                        message_color = RED
                if help_button.collidepoint(x, y):
                    speak_syllables(correct_word)
                    message = "Listen carefully to syllables!"
                    message_color = BLACK
                    hint_shown = True
                if ai_button.collidepoint(x, y):
                    user_speech = recognize_speech()
                    ai_feedback = get_phonetic_feedback(correct_word, user_speech)
                    ai_feedback_time = time.time()
                    ai_user_said = user_speech
                    ai_user_said_time = time.time()
                    # Speak back what the user said
                    ai_assist_say_back(user_speech)
                    tts_engine.say(ai_feedback)
                    tts_engine.runAndWait()
                    syllable_feedback(correct_word)
                    message = ai_feedback
                    message_color = get_feedback_color(ai_feedback)
                    ai_hint_display = True
                if difficulty == "medium":
                    for idx, rect in enumerate(option_rects):
                        if rect.collidepoint(x, y):
                            attempts += 1
                            if difficulty not in attempts_db:
                                attempts_db[difficulty] = {}
                            attempts_db[difficulty][correct_word] = attempts
                            save_attempts(attempts_db)
                            selected = current_options[idx]
                            if selected == correct_word:
                                play_sound(correct_sound)
                                flash_index = idx
                                flash_color = (0, 255, 0)
                                flash_start_time = pygame.time.get_ticks()
                                message = "Correct!"
                                message_color = GREEN
                            else:
                                play_sound(wrong_sound)
                                flash_index = idx
                                flash_color = (255, 0, 0)
                                flash_start_time = pygame.time.get_ticks()
                                message = "Try again."
                                message_color = RED
                                hint_shown = True

        draw_gradient_background(screen, WIDTH, HEIGHT, (255, 255, 255), (216, 191, 216))
        FONT_LARGE, FONT_SMALL, FONT_HINT = get_fonts(HEIGHT)
        draw_text(f"Difficulty: {difficulty.capitalize()}", FONT_SMALL, BLACK, WIDTH // 2, 40)
        pygame.draw.rect(screen, GRAY, back_button)
        draw_text("Back", FONT_SMALL, BLACK, back_button.centerx, back_button.centery)
        if difficulty == "easy" or difficulty == "hard":
            draw_text("Say it correctly. Press Mic to start:", FONT_SMALL, BLACK, WIDTH // 2, HEIGHT // 5)
        else:
            draw_text("Choose the correct word:", FONT_SMALL, BLACK, WIDTH // 2, HEIGHT // 5)
        draw_text(correct_word, FONT_LARGE, BLUE, WIDTH // 2, HEIGHT // 3)
        option_rects.clear()
        if difficulty == "medium":
            spacing = HEIGHT // 10
            start_y = HEIGHT // 2 - len(current_options) * spacing // 2
            for i, option in enumerate(current_options):
                x_opt = WIDTH // 2
                y_opt = start_y + i * spacing
                rect = pygame.Rect(x_opt - 100, y_opt - -70, 200, 60)
                option_rects.append(rect)
                if flash_index == i and flash_color:
                    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                    s.fill((*flash_color, 100))
                    screen.blit(s, rect.topleft)
                    pygame.draw.rect(screen, flash_color, rect, 3)
                else:
                    pygame.draw.rect(screen, BLUE, rect, 2)
                draw_text(option, FONT_SMALL, BLACK, rect.centerx, rect.centery)
        pygame.draw.rect(screen, BLUE, speak_button)
        draw_text("Speak Word", FONT_SMALL, WHITE, speak_button.centerx, speak_button.centery)
        if use_mic:
            pygame.draw.rect(screen, GREEN, mic_button)
            draw_text("Mic", FONT_SMALL, WHITE, mic_button.centerx, mic_button.centery)
        pygame.draw.rect(screen, PURPLE, help_button)
        draw_text("AI Help", FONT_SMALL, WHITE, help_button.centerx, help_button.centery)
        pygame.draw.rect(screen, YELLOW, ai_button)
        draw_text("AI Assist", FONT_SMALL, BLACK, ai_button.centerx, ai_button.centery)
        if show_congrats:
            draw_text("Congratulations! You finished this level. Excellent job!", FONT_LARGE, GREEN, WIDTH // 2, HEIGHT // 2 - 40)
            draw_text("Always remember that practice makes perfect.", FONT_LARGE, GREEN, WIDTH // 2, HEIGHT // 2 + 40)
        else:
            draw_text(message, FONT_SMALL, message_color, WIDTH // 2, HEIGHT - 80)
        draw_text(f"Attempts: {attempts}", FONT_SMALL, BLACK, 80, HEIGHT - 120, center=False)
        if hint_shown or ai_hint_display:
            syllable_text = " - ".join(syllable_hint)
            draw_text(f"Syllable/s: {syllable_text}", FONT_HINT, BLACK, WIDTH // 2, HEIGHT - 50)
            if hint:
                draw_text(f"Hint: {hint}", FONT_HINT, BLACK, WIDTH // 2, HEIGHT - 30)
        # --- AI Assist feedback display, applies to all levels ---
        if ai_user_said and (time.time() - ai_user_said_time < AI_FEEDBACK_DURATION):
            popup_width = WIDTH - 120
            popup_height = 40
            popup_x = 60
            popup_y = HEIGHT - popup_height - 185
            pygame.draw.rect(screen, (255, 255, 230), (popup_x, popup_y, popup_width, popup_height))
            draw_text(f'You said: "{ai_user_said}"', FONT_SMALL, (128, 0, 128), popup_x + 10, popup_y + popup_height // 2, center=False)
        if ai_feedback and (time.time() - ai_feedback_time) < AI_FEEDBACK_DURATION:
            popup_width = WIDTH - 120
            popup_height = 80
            popup_x = 60
            popup_y = HEIGHT - popup_height - 130
            pygame.draw.rect(screen, (240, 246, 255), (popup_x, popup_y, popup_width, popup_height))
            draw_text("AI Feedback:", FONT_SMALL, (70, 70, 70), popup_x + 10, popup_y + 18, center=False)
            draw_text(ai_feedback, FONT_HINT, get_feedback_color(ai_feedback), popup_x + 10, popup_y + popup_height // 2 + 5, center=False)
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
