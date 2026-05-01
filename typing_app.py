#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import random
import re
import json
import os
import wikipediaapi

wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='TypingApp'
)

import unicodedata

def clean_text(text):
    # normalize accents (é → e, ā → a)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')

    # replace special symbols manually
    replacements = {
        'µ': 'micro',
        '°': ' degrees',
        '×': 'x',
        '–': '-',
        '—': '-',
        '’': "'",
        '“': '"',
        '”': '"'
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text
# Beeps
try:
    import winsound
except Exception:
    winsound = None

LEADERBOARD_FILE = "leaderboard.json"
TOPICS = [
    "Physics", "India", "Technology", "Mathematics", "Computer",
    "Space", "Biology", "History", "Astronomy", "Engineering",
    "Earth", "Animals", "Chemistry", "Economics", "Art"
]

USED_SENTENCES = set()
def safe_fetch_wiki_text():
    try:
        topics = [
            "Physics", "Mathematics", "Computer science", "Biology",
            "Space", "History", "Technology", "Artificial intelligence",
            "Earth", "Animals", "Chemistry", "Engineering",
            "Astronomy", "Economics", "Geography", "Medicine"
        ]

        topic = random.choice(topics)

        page = wiki.page(topic)

        if page.exists():
            text = clean_text(page.text)

# split into proper sentences
            sentences = re.split(r'(?<=[.!?]) +', text)

# filter clean short sentences
            good = [s.strip() for s in sentences if 6 <= len(s.split()) <= 14]

            if good:
                return random.choice(good)

    except Exception as e:
        print("Wiki error:", e)

    return ""


def split_into_sentences(text):
    # Split on punctuation
    sentences = re.split(r'[.!?]\s+', text)

    cleaned = []

    for s in sentences:
        s = s.strip()

        # 🔥 Keep it simple — don't over-filter
        if len(s) < 20:
            continue

        # remove [1], [2] citations
        s = re.sub(r'\[\d+\]', '', s)

        cleaned.append(s)

    return cleaned


def classify_sentence(sentence):
    words = [w for w in re.findall(r"[A-Za-z0-9']+", sentence)]
    if not words:
        return "hard"
    length = len(words)
    avg = sum(len(w) for w in words) / len(words)
    if length <= 12 and avg < 5:
        return "easy"
    elif length <= 18:
        return "medium"
    else:
        return "hard"


def build_buckets(sentences):
    buckets = {"easy": [], "medium": [], "hard": []}
    for s in sentences:
        buckets[classify_sentence(s)].append(s)
    return buckets


    raise ValueError(f"No Wikipedia sentence found for difficulty: {level}")
def get_sentence_by_level(level):
    global USED_SENTENCES

    collected = []

    for _ in range(10):  # increased attempts
        text = safe_fetch_wiki_text()
        print("TEXT LENGTH:", len(text))
        if not text:
            continue

        sents = split_into_sentences(text)
        buckets = build_buckets(sents)

        collected.extend(buckets.get(level, []))

# 🔥 fallback: if bucket empty, take ANY sentence
        if not buckets.get(level):
           collected.extend(sents[:10])
    print("Collected sentences:", len(collected))

    if not collected:
        return "Typing improves with consistent practice and patience."

    fresh = [s for s in collected if s not in USED_SENTENCES]

    if not fresh:
        USED_SENTENCES.clear()
        fresh = collected

    random.shuffle(fresh)
    chosen = fresh[0]

    USED_SENTENCES.add(chosen)
    return chosen




def get_easy_wiki_words(min_len=5, max_len=8, count=200, attempts=10):
    """
    Fetch easier, simpler random words (min_len..max_len letters) from Wikipedia.
    Filters out scientific / technical terms and non-alpha tokens.
    If fetching isn't possible, returns a fallback list of simple words.
    """
    banned_chunks = [
        "tion", "sion", "ology", "phy", "chem", "micro", "astro",
        "ism", "ment", "genic", "graph", "thermo", "neuro",
        "struct", "quant", "physics", "logical", "meter", "scope",
        "lysis", "flora", "phage", "cyte", "genic"
    ]

    easy_words = set()

    for _ in range(attempts):
        text = safe_fetch_wiki_text()
        if not text:
            continue

        raw = re.findall(r"[A-Za-z]+", text)  # alphabetic sequences only

        for w in raw:
            w = w.lower()
            if len(w) < min_len or len(w) > max_len:
                continue
            if any(chunk in w for chunk in banned_chunks):
                continue
            if not w.isalpha():
                continue
            easy_words.add(w)

        if len(easy_words) >= count:
            break

    if not easy_words:
        # fallback simple words
        fallback = [
            "forest", "castle", "silver", "happy", "little",
            "beauty", "bright", "wonder", "planet", "sunset",
            "golden", "smooth", "family", "memory", "driver",
            "yellow", "ocean", "garden", "mirror", "candle",
            "butter", "friend", "moment", "circle", "bridge",
            "summer", "winter", "simple", "pretty", "smiley"
        ]
        random.shuffle(fallback)
        return fallback[:count]

    lst = list(easy_words)
    random.shuffle(lst)
    return lst[:count]


def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_leaderboard(board):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(board, f, indent=2)


def add_score_to_leaderboard(name, wpm, accuracy):
    board = load_leaderboard()
    board.append({"name": name, "wpm": wpm, "accuracy": accuracy, "ts": time.time()})
    board = sorted(board, key=lambda x: x["wpm"], reverse=True)[:20]
    save_leaderboard(board)


# -----------------------
# Falling Words Mode (with timer) - EASY WIKI WORDS (5-8 letters)
# -----------------------

class FallingWordsWindow(tk.Toplevel):
    """
    Falling Words Mode — EASY Wikipedia words version (words 5-8 letters).
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Falling Words Mode")
        self.geometry("650x520")
        self.resizable(False, False)
        self.next_sentence = None

        # Fetch EASY WORDS HERE 🎉
        # This will try to source from Wikipedia; if not available uses fallback simple words.
        self.word_list = get_easy_wiki_words(min_len=5, max_len=8, count=200)

        # Game state
        self.running = False
        self.words = []
        self.spawn_interval = 1300  # ms
        self.move_interval = 40     # ms
        self.word_speed = 2         # pixels per tick

        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        self.score = 0
        self.missed = 0

        self.score_label = ttk.Label(top, text="Score: 0")
        self.score_label.pack(side=tk.LEFT, padx=(0, 10))

        self.missed_label = ttk.Label(top, text="Missed: 0")
        self.missed_label.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(top, text="Time (s):").pack(side=tk.LEFT)
        self.game_time_var = tk.IntVar(value=60)
        self.time_spin = ttk.Spinbox(top, from_=10, to=600, increment=10, textvariable=self.game_time_var, width=6)
        self.time_spin.pack(side=tk.LEFT, padx=(6, 8))

        self.timer_label = ttk.Label(top, text=f"Time left: {self.game_time_var.get()}s")
        self.timer_label.pack(side=tk.LEFT, padx=(6, 12))

        self.start_btn = ttk.Button(top, text="Start", command=self.start_game)
        self.start_btn.pack(side=tk.LEFT, padx=(4, 4))
        self.stop_btn = ttk.Button(top, text="Stop", command=self.end_game, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(4, 4))

        self.canvas = tk.Canvas(self, width=630, height=380, bg="#000000")
        self.canvas.pack(padx=10, pady=(8, 6))

        bottom = ttk.Frame(self, padding=8)
        bottom.pack(fill=tk.X)

        self.entry = ttk.Entry(bottom, width=40)
        self.entry.pack(side=tk.LEFT, padx=(0, 8))
        # bind Return to submit typed word
        self.entry.bind("<Return>", self.check_word)

        ttk.Button(bottom, text="Close", command=self.close).pack(side=tk.RIGHT)

        self.game_time = int(self.game_time_var.get())
        self.remaining_time = self.game_time
        self.countdown_id = None
        self.spawn_id = None
        self.move_id = None

        # keep focus behavior predictable
        self.protocol("WM_DELETE_WINDOW", self.close)

    def start_game(self):
        if self.running:
            return
        self.clear_all_words()
        self.score = 0
        self.missed = 0
        self.score_label.config(text="Score: 0")
        self.missed_label.config(text="Missed: 0")

        try:
            self.game_time = int(self.game_time_var.get())
        except Exception:
            self.game_time = 60
            self.game_time_var.set(60)
        self.remaining_time = self.game_time
        self.timer_label.config(text=f"Time left: {self.remaining_time}s")

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        # ensure entry has focus
        self.entry.focus_set()

        # shuffle word list to reduce repeats
        random.shuffle(self.word_list)

        self.spawn_word()
        self.move_words()
        self.countdown()

        if winsound is not None:
            try:
                winsound.Beep(1200, 120)
            except Exception:
                pass

    def spawn_word(self):
        if not self.running:
            return
        if not self.word_list:
            return
        word = random.choice(self.word_list)
        x = random.randint(40, 590)
        y = 10
        color = random.choice(["#ff4b5c", "#ffcd3c", "#4cd3c2", "#5c6bf5", "#ff6bf5", "#ffa36c", "#9ad3bc"])
        text_id = self.canvas.create_text(x, y, text=word, fill=color, font=("Helvetica", 16, "bold"))
        self.words.append({"id": text_id, "word": word, "x": x, "y": y})
        self.spawn_id = self.after(self.spawn_interval, self.spawn_word)

    def move_words(self):
        if not self.running:
            return
        to_remove = []
        for w in list(self.words):
            w["y"] += self.word_speed
            try:
                self.canvas.move(w["id"], 0, self.word_speed)
            except Exception:
                to_remove.append(w)
                continue
            if w["y"] > 360:
                to_remove.append(w)
        for w in to_remove:
            try:
                self.canvas.delete(w["id"])
            except Exception:
                pass
            if w in self.words:
                self.words.remove(w)
            self.missed += 1
            self.missed_label.config(text=f"Missed: {self.missed}")
        self.move_id = self.after(self.move_interval, self.move_words)

    def check_word(self, event=None):
        """
        Submit the typed entry. Keep focus on entry so canvas doesn't steal it.
        Return "break" to prevent further propagation of the Return key.
        """
        typed = self.entry.get().strip()

        # keep focus in the entry (fixes occasional canvas focus jump)
        try:
            self.entry.focus_set()
        except Exception:
            pass

        if not typed or not self.running:
            self.entry.delete(0, tk.END)
            # consume the event so nothing else reacts
            return "break"

        matched = None
        # prefer the top-most (lowest y) matching word
        for w in sorted(self.words, key=lambda a: a["y"]):
            if w["word"] == typed:
                matched = w
                break

        if matched:
            try:
                self.canvas.delete(matched["id"])
            except Exception:
                pass
            if matched in self.words:
                self.words.remove(matched)
            self.score += 1
            self.score_label.config(text=f"Score: {self.score}")
            if winsound is not None:
                try:
                    winsound.Beep(1500, 60)
                except Exception:
                    pass

        # clear input and keep focus
        try:
            self.entry.delete(0, tk.END)
            self.entry.focus_set()
        except Exception:
            pass

        # prevent default handling
        return "break"

    def countdown(self):
        if not self.running:
            return
        self.remaining_time -= 1
        self.timer_label.config(text=f"Time left: {self.remaining_time}s")
        if self.remaining_time <= 0:
            self.end_game()
            return
        self.countdown_id = self.after(1000, self.countdown)

    def clear_all_words(self):
        for w in list(self.words):
            try:
                self.canvas.delete(w["id"])
            except Exception:
                pass
        self.words.clear()

    def end_game(self):
        if not self.running:
            return
        self.running = False
        if self.spawn_id is not None:
            try:
                self.after_cancel(self.spawn_id)
            except Exception:
                pass
            self.spawn_id = None
        if self.move_id is not None:
            try:
                self.after_cancel(self.move_id)
            except Exception:
                pass
            self.move_id = None
        if self.countdown_id is not None:
            try:
                self.after_cancel(self.countdown_id)
            except Exception:
                pass
            self.countdown_id = None

        if winsound is not None:
            try:
                winsound.Beep(700, 220)
            except Exception:
                pass

        messagebox.showinfo("Time Up!", f"⏳ Time Over!\n\nScore: {self.score}\nMissed: {self.missed}")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.clear_all_words()
        self.timer_label.config(text=f"Time left: {self.game_time}s")

    def close(self):
        self.running = False
        if self.spawn_id is not None:
            try:
                self.after_cancel(self.spawn_id)
            except Exception:
                pass
            self.spawn_id = None
        if self.move_id is not None:
            try:
                self.after_cancel(self.move_id)
            except Exception:
                pass
            self.move_id = None
        if self.countdown_id is not None:
            try:
                self.after_cancel(self.countdown_id)
            except Exception:
                pass
            self.countdown_id = None
        self.destroy()


# -----------------------
# Main Typing App
# -----------------------

class TypingApp(tk.Tk):
    def style_buttons(self, widget, style_name):
        for child in widget.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(style=style_name)
            self.style_buttons(child, style_name)
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._apply_theme()
    def __init__(self):
        super().__init__()
        self.title("Smart Typing Test — Wikipedia Edition")
        self.geometry("980x720")
        self.resizable(False, False)

        self.current_passage = ""
        self.level = tk.StringVar(value="easy")
        self.duration = tk.IntVar(value=30)
        self.started = False
        self.start_time = None
        self.end_time = None
        self.elapsed = 0.0
        self.after_id = None

        self.dark_mode = False
        self.fetching_more = False

        # New controls: mode, word count, time presets/custom
        self.mode = tk.StringVar(value="Sentence")
        self.word_limit = tk.IntVar(value=25)
        self.word_custom = tk.IntVar(value=25)
        self.time_preset = tk.StringVar(value="30")
        self.time_custom = tk.IntVar(value=30)

        self._build_ui()
        self._apply_theme()

        # BIND F5 as the single universal reset shortcut (safe)
        self.bind_all("<F5>", lambda e: self.reset_and_new_sentence())

    def _build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(side=tk.TOP, fill=tk.X)

        # Mode selector: Sentence / Paragraph / Words
        ttk.Label(top, text="Mode:").pack(side=tk.LEFT, padx=(0, 6))
        mode_cb = ttk.Combobox(top, textvariable=self.mode, values=["Sentence", "Paragraph", "Words"], width=10, state="readonly")
        mode_cb.pack(side=tk.LEFT)

        ttk.Label(top, text="Difficulty:").pack(side=tk.LEFT, padx=(12, 6))
        ttk.Combobox(top, textvariable=self.level,
                     values=["easy", "medium", "hard"], width=8, state="readonly").pack(side=tk.LEFT)

        # Word limit dropdown (relevant when Mode == Words)
        ttk.Label(top, text="Words:").pack(side=tk.LEFT, padx=(12, 6))
        self.words_cb = ttk.Combobox(top, values=["10", "25", "50", "100", "Custom"], width=8, state="readonly")
        self.words_cb.set(str(self.word_limit.get()))
        self.words_cb.pack(side=tk.LEFT)
        self.words_cb.bind("<<ComboboxSelected>>", self.on_words_choice)
        # custom word spinbox (hidden unless Custom selected)
        self.word_spin = ttk.Spinbox(top, from_=5, to=1000, increment=5, textvariable=self.word_custom, width=6)
        # don't pack yet

        # Time presets dropdown (and custom spinbox)
        ttk.Label(top, text="Time (s):").pack(side=tk.LEFT, padx=(12, 6))
        self.time_cb = ttk.Combobox(top, values=["15", "30", "45", "60", "Custom"], width=8, state="readonly")
        self.time_cb.set(str(self.duration.get()))
        self.time_cb.pack(side=tk.LEFT)
        self.time_cb.bind("<<ComboboxSelected>>", self.on_time_choice)
        self.time_spin = ttk.Spinbox(top, from_=5, to=3600, increment=5, textvariable=self.time_custom, width=6)
        # hidden unless Custom selected

        # New sentence / fetch
        self.new_passage_btn = ttk.Button(top, text="New Passage", command=self.on_fetch_clicked)
        self.new_passage_btn.pack(side=tk.LEFT, padx=(12, 6))

        self.progress = ttk.Progressbar(self, mode="indeterminate", length=260)
        self.progress.pack(pady=4)
        self.progress.pack_forget()

        # Restart same passage
        self.restart_btn = ttk.Button(top, text="Restart Same", command=self.restart_same_passage, state=tk.DISABLED)
        self.restart_btn.pack(side=tk.LEFT, padx=(6, 6))

        # Falling words mode button
        self.falling_btn = ttk.Button(top, text="Falling Words Mode 🌧️", command=self.open_falling_words)
        self.falling_btn.pack(side=tk.LEFT, padx=(6, 6))

        # Right side controls (clean order)
        self.theme_btn = ttk.Button(top, text="☀", width=3, command=self.toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=(6, 4))

        self.instructions_btn = ttk.Button(
            top,
            text="Instructions",
            command=self.show_instructions
        )
  
        self.instructions_btn.pack(side=tk.RIGHT, padx=6)
        ttk.Button(top, text="Leaderboard", command=self.show_leaderboard).pack(side=tk.RIGHT, padx=(6, 0))

        passage_frame = ttk.LabelFrame(self, text="Passage", padding=(8, 8))
        passage_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(8, 4))
        self.passage_frame = passage_frame

        # ✅ fixed line (no stray backslash)
        self.passage_text = tk.Text(
            passage_frame,
            height=8,
            wrap="word",
            padx=8,
            pady=6,
            font=("Helvetica", 12),
            state=tk.DISABLED
        )
        self.passage_text.pack(fill=tk.BOTH, expand=True)

        self.passage_text.tag_configure("correct", foreground="black")
        self.passage_text.tag_configure("incorrect", foreground="red")
        self.passage_text.tag_configure("missing", foreground="gray")

        typing_frame = ttk.LabelFrame(self, text="Type here", padding=(8, 8))
        typing_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 8))
        self.typing_frame = typing_frame

        self.input_entry = tk.Text(typing_frame, height=8, wrap="word", font=("Helvetica", 13))
        self.input_entry.pack(fill=tk.BOTH, expand=True)
        self.input_entry.bind("<KeyRelease>", self.on_key_release)

        bottom = ttk.Frame(self, padding=10)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(bottom, text="Ready — click 'New Passage' to begin.", anchor="w")
        self.status_label.pack(side=tk.LEFT)

        self.wpm_label = ttk.Label(bottom, text="WPM: 0.00")
        self.wpm_label.pack(side=tk.RIGHT, padx=(8, 4))

        self.acc_label = ttk.Label(bottom, text="Accuracy: 0.00%")
        self.acc_label.pack(side=tk.RIGHT, padx=(8, 4))

        

        # NOTE: we intentionally do not bind Enter/Space globally; F5 is the only global reset
        # Enter works normally; space works normally.

    # -----------------------
    # Theming
    # -----------------------

    def _apply_theme(self):
        style = ttk.Style(self)
        style.theme_use('clam')

    # 🔥 SET COLORS FIRST
        if self.dark_mode:
            bg = "#1e1e1e"
            fg = "#f5f5f5"
            entry_bg = "#121212"
            sel_bg = "#444444"
        else:
            bg = "#f0f0f0"
            fg = "#000000"
            entry_bg = "#ffffff"
            sel_bg = "#bcd4ff"

    # 🔥 NOW APPLY STYLE (after bg exists)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TFrame", background=bg)
        style.configure("TLabelframe", background=bg, foreground=fg)
        style.configure("TLabelframe.Label", background=bg, foreground=fg)

    # 🔥 BUTTON STYLE
        if self.dark_mode:
            style.configure(
                "Dark.TButton",
                background="#2b2b2b",
                foreground="#ffffff",
                padding=6
            )

            style.map(
                "Dark.TButton",
                background=[("active", "#3c3c3c"), ("!active", "#2b2b2b")]
            )
            for child in self.winfo_children():
                if isinstance(child, ttk.Button):
                    if child != self.instructions_btn:
                        child.configure(style="Dark.TButton")
            self.instructions_btn.configure(style="TButton")
            

            
            style.configure(
                "TCombobox",
                fieldbackground="#ffffff",
                foreground="#000000"
            )

            style.map(
                "TCombobox",
                fieldbackground=[("readonly", "#ffffff")],
                foreground=[("readonly", "#000000")]
            )
            # 🔥 Spinbox fix (use style, NOT bg/fg)
            style.configure(
                "TSpinbox",
                fieldbackground="#ffffff",
                foreground="#000000"
            )

            style.map(
                "TSpinbox",
                fieldbackground=[("readonly", "#ffffff")],
                foreground=[("readonly", "#000000")]
            )
        else:
            self.style_buttons(self, "TButton")

    # 🔥 APPLY ROOT + TEXT COLORS
        self.configure(background=bg)

        self.passage_text.configure(
            background=entry_bg,
            foreground=fg,
            insertbackground=fg,
            selectbackground=sel_bg
        )

        self.input_entry.configure(
            background=entry_bg,
            foreground=fg,
            insertbackground=fg,
            selectbackground=sel_bg
        )

    # 🔥 ICON SWITCH
        self.theme_btn.config(text="🌙" if self.dark_mode else "☀")

    # -----------------------
    # Falling Words launcher
    # -----------------------

    def open_falling_words(self):
        # Pass the app as master; the falling window will fetch its words internally
        FallingWordsWindow(self)

    # -----------------------
    # Sounds
    # -----------------------

    def _play_start_sound(self):
        if winsound is not None:
            try:
                winsound.Beep(1200, 150)
            except Exception:
                pass

    def _play_end_sound(self):
        if winsound is not None:
            try:
                winsound.Beep(600, 300)
            except Exception:
                pass

    # -----------------------
    # Instructions & helpers
    # -----------------------

    def show_instructions(self):
        instr = (
            "Main Typing Test:\n"
            "- Choose Mode: Sentence / Paragraph / Words.\n"
            "- Words mode: choose how many words (10/25/50/100) or Custom.\n"
            "- Paragraph mode: multiple sentences will be fetched and used as the passage.\n"
            "- Click 'New Passage' to fetch content from Wikipedia (or fallback).\n"
            "- Timer starts when you type the first character (not on fetch).\n"
            "- 'Restart Same' restarts the test with the SAME text (timer starts when typing).\n"
            "- Press F5 to immediately reset and fetch a new passage.\n"
            "- Accuracy is now computed only over characters you typed (errors you made), not unanswered/missing characters.\n\n"
            "Falling Words Mode:\n"
            "- Words are sourced from Wikipedia but filtered to be simple 5-8 letter words\n"
            "- Set a time, press Start\n"
            "- Type a falling word and press Enter to clear it\n"
            "- Score increases when you clear a word; missed words are counted."
        )
        messagebox.showinfo("Instructions", instr)

    # -----------------------
    # New UI callbacks for presets/custom
    # -----------------------

    def on_words_choice(self, event=None):
        choice = self.words_cb.get()
        if choice == "Custom":
            # show spinbox
            self.word_spin.pack(side=tk.LEFT, padx=(4, 4))
            self.word_spin.focus_set()
        else:
            try:
                val = int(choice)
                self.word_limit.set(val)
            except Exception:
                pass
            try:
                self.word_spin.pack_forget()
            except Exception:
                pass

    def on_time_choice(self, event=None):
        choice = self.time_cb.get()
        if choice == "Custom":
            self.time_spin.pack(side=tk.LEFT, padx=(4, 4))
            self.time_spin.focus_set()
        else:
            try:
                val = int(choice)
                self.duration.set(val)
            except Exception:
                pass
            try:
                self.time_spin.pack_forget()
            except Exception:
                pass

    # -----------------------
    # Passage fetching
    # -----------------------

    def on_fetch_clicked(self):
        # fetch a passage according to selected mode (does NOT auto-start timer)
        self.new_passage_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.DISABLED)

        self.status_label.config(text="Fetching passage from Wikipedia...")
        self.progress.pack()
        self.progress.start(10)

        t = threading.Thread(target=self._bg_fetch_passage, daemon=True)
        t.start()

    def _prefetch_sentence(self):
        try:
            s = get_sentence_by_level(self.level.get())
            self.next_sentence = s
        except:
            self.next_sentence = "Typing improves with consistent practice."

    def _bg_fetch_passage(self):
        try:
            mode = self.mode.get()
            level = self.level.get()
            if mode == "Sentence":
                passage = get_sentence_by_level(level)
            elif mode == "Paragraph":
                # join a few sentences to make a paragraph
              parts = []
              for _ in range(3):
                  s = get_sentence_by_level(level)
                  if s not in parts:   # 🔥 avoid duplicate fallback
                    parts.append(s)

              if not parts:
                    parts = ["Typing improves with consistent practice and patience."]

              passage = " ".join(parts)
            else:  # Words mode
                # decide how many words
                choice = self.words_cb.get()
                if choice == "Custom":
                    count = max(5, int(self.word_custom.get()))
                else:
                    try:
                        count = int(choice)
                    except Exception:
                        count = self.word_limit.get() or 25
                # build a words passage
                words = get_easy_wiki_words(min_len=3, max_len=10, count=max(200, count))
                if len(words) < count:
                    # fallback short repeated list
                    words = (words * ((count // max(1, len(words))) + 2))[:count]
                selected = words[:count]
                passage = " ".join(selected)
                # nice punctuation
                passage = passage.capitalize() + "."

            if not passage.strip():
                passage = "Typing improves with consistent practice and patience."

            self.after(20, lambda: self._set_passage(passage))
        except Exception as e:
            print("ERROR:", e)
            # show the actual exception message
            self.after(20, lambda err=e: messagebox.showerror("Error", str(err)))
            self.after(20, self._fetch_cleanup)
        finally:
            # always stop progress bar
            self.after(20, self._hide_progress)

    def _hide_progress(self):
        try:
            self.progress.stop()
            self.progress.pack_forget()
        except Exception:
            pass

    def _fetch_cleanup(self):
        self.new_passage_btn.config(state=tk.NORMAL)
        self.restart_btn.config(state=tk.NORMAL)

    def _set_passage(self, text):
        # Set passage but do NOT start timer here. Timer starts on first key press.
        self.current_passage = text.strip()

        self.passage_text.configure(state=tk.NORMAL)
        self.passage_text.delete(1.0, tk.END)
        self.passage_text.insert(tk.END, self.current_passage)
        self.passage_text.tag_remove("correct", "1.0", tk.END)
        self.passage_text.tag_remove("incorrect", "1.0", tk.END)
        self.passage_text.tag_remove("missing", "1.0", tk.END)
        self.passage_text.configure(state=tk.DISABLED)

        self.input_entry.delete("1.0", tk.END)
        self.input_entry.focus_set()

        # If user selected a time custom preset, apply it now
        if self.time_cb.get() == "Custom":
            try:
                self.duration.set(int(self.time_custom.get()))
            except Exception:
                pass
        else:
            try:
                self.duration.set(int(self.time_cb.get()))
            except Exception:
                pass

        self.restart_btn.config(state=tk.NORMAL)
        self.new_passage_btn.config(state=tk.NORMAL)

        self.fetching_more = False

        # Reset started state so typing will begin timer
        self.started = False
        self.start_time = None
        self.end_time = None
        self.elapsed = 0.0
        self.wpm_label.config(text="WPM: 0.00")
        self.acc_label.config(text="Accuracy: 0.00%")
        self.status_label.config(text="Ready — start typing to begin the timer.")
        threading.Thread(target=self._prefetch_sentence, daemon=True).start()

    # -----------------------
    # Reset & shortcuts
    # -----------------------

    def reset_and_new_sentence(self, event=None):
        """
        Stop test, clear fields, and fetch a new passage.
        """
        # Stop any running test
        self.started = False
        if getattr(self, "after_id", None):
            try:
                self.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

        # Clear input and reset metrics
        try:
            self.input_entry.delete("1.0", tk.END)
        except Exception:
            pass
        self.wpm_label.config(text="WPM: 0.00")
        self.acc_label.config(text="Accuracy: 0.00%")
        self.status_label.config(text="Fetching new passage...")

        # Reset flags and fetch new passage
        self.fetching_more = False
        # fetch new passage shortly to allow UI to update
        self.after(10, self.on_fetch_clicked)

    # -----------------------
    # Test control and metrics
    # -----------------------

    def auto_start_test(self):
        """
        Kept for backward compatibility — not automatically invoked on set_passage anymore.
        Starts the timer immediately (used if you want explicit auto-start).
        """
        if not self.current_passage:
            return
        self.input_entry.delete("1.0", tk.END)
        self.input_entry.focus_set()
        self.duration_val = int(self.duration.get())
        self.started = True
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration_val
        self._play_start_sound()
        self.status_label.config(text=f"Typing... {self.duration_val} sec left")
        self._tick()

    def restart_same_passage(self):
        """
        Restart the same passage: clear typed text and reset timers.
        Timer will start when user types.
        """
        if not self.current_passage:
            return
        # Stop any running test
        self.started = False
        if getattr(self, "after_id", None):
            try:
                self.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

        self.input_entry.delete("1.0", tk.END)
        self.wpm_label.config(text="WPM: 0.00")
        self.acc_label.config(text="Accuracy: 0.00%")
        self.status_label.config(text="Restarted — start typing to begin the timer.")

        self.fetching_more = False
        self.start_time = None
        self.end_time = None
        self.elapsed = 0.0

    def _tick(self):
        if not self.started:
            return

        now = time.time()
        self.elapsed = now - self.start_time
        remaining = max(0, int(self.end_time - now))
        self.status_label.config(text=f"Typing... {remaining} sec left")

        self._update_metrics()

        if now >= self.end_time:
            self.started = False
            self._finish_test()
            self.new_passage_btn.config(state=tk.NORMAL)
        else:
            self.after_id = self.after(200, self._tick)

    def on_key_release(self, event=None):
        """
        Start timer on first keypress (if not already started).
        Update metrics while typing.
        """
        typed = self.input_entry.get("1.0", tk.END).rstrip("\n")

        # Start the timer when the user types the first non-empty content
        if not self.started and typed:
            self.started = True
            self.start_time = time.time()
            try:
                self.duration_val = int(self.duration.get())
            except Exception:
                self.duration_val = 30
            self.end_time = self.start_time + self.duration_val
            self._play_start_sound()
            # begin tick loop
            self._tick()

        # Update metrics (even if not started yet, to show accuracy)
        self._update_metrics()

    def _maybe_extend_passage(self, typed: str):
        if self.fetching_more or not self.current_passage:
            return

        if self.mode.get() == "Words":
            return

        passage_words = self.current_passage.split()
        if len(passage_words) < 3:
            return

        total = len(passage_words)

    # 🔥 count words properly INCLUDING spaces
        words_typed = len(re.findall(r"\S+", typed))

    # 🔥 detect if user is at second-last word EARLY
        if words_typed >= total - 2 and not self.fetching_more:
            self.fetching_more = True

    # 🔥 APPEND IMMEDIATELY (NO WAIT)
            sentence = self.next_sentence or get_sentence_by_level(self.level.get())
            self._append_sentence(sentence)

    # 🔥 fetch next in background
            threading.Thread(
                target=self._prefetch_sentence,
                daemon=True
            ).start()

    # 🔥 allow next append
            self.fetching_more = False

    
    def _append_sentence(self, sentence):
        sentence = clean_text(sentence.strip())

        if sentence in self.current_passage:
            return

    # ensure punctuation
        if not sentence.endswith(('.', '!', '?')):
            sentence += '.'

    # ensure space before adding
        if not self.current_passage.endswith(" "):
            self.current_passage += " "

        self.current_passage += sentence

        # Update passage widget
        self.passage_text.configure(state=tk.NORMAL)
        self.passage_text.delete("1.0", tk.END)
        self.passage_text.insert(tk.END, self.current_passage)
        self.passage_text.configure(state=tk.DISABLED)

        # Re-highlight with current typed text
        typed = self.input_entry.get("1.0", tk.END).rstrip("\n")
        self._highlight_passage(typed)

    def _update_metrics(self):
        typed = self.input_entry.get("1.0", tk.END).rstrip("\n")

        # Possibly extend passage
        self._maybe_extend_passage(typed)

        num_words = len(typed.split())
        elapsed = max(1e-6, self.elapsed)
        wpm = (num_words / elapsed) * 60 if elapsed > 0 else 0.0

        # compute correct characters only up to typed length
        correct = sum(
            typed[i] == self.current_passage[i]
            for i in range(min(len(typed), len(self.current_passage)))
        )
        # NEW ACCURACY: consider only characters the user typed (do not penalize missing text)
        accuracy = (correct / max(1, len(typed))) * 100 if typed else 0.0

        self.wpm_label.config(text=f"WPM: {wpm:.2f}")
        self.acc_label.config(text=f"Accuracy: {accuracy:.2f}%")

        self._highlight_passage(typed)

    def _highlight_passage(self, typed):
        self.passage_text.configure(state=tk.NORMAL)
        self.passage_text.tag_remove("correct", "1.0", tk.END)
        self.passage_text.tag_remove("incorrect", "1.0", tk.END)
        self.passage_text.tag_remove("missing", "1.0", tk.END)

        for i, ch in enumerate(self.current_passage):
            idx = f"1.0 + {i} chars"
            if i < len(typed):
                if typed[i] == ch:
                    self.passage_text.tag_add("correct", idx, f"{idx}+1c")
                else:
                    self.passage_text.tag_add("incorrect", idx, f"{idx}+1c")
            else:
                self.passage_text.tag_add("missing", idx, f"{idx}+1c")

        self.passage_text.configure(state=tk.DISABLED)

    # -----------------------
    # Mistake summary & finishing
    # -----------------------

    def _compute_mistake_stats(self, typed):
        passage = self.current_passage
        total_chars = len(passage)
        min_len = min(len(typed), len(passage))
        correct_chars = sum(typed[i] == passage[i] for i in range(min_len))
        incorrect_chars = sum(typed[i] != passage[i] for i in range(min_len))
        missing_chars = max(0, len(passage) - len(typed))
        extra_chars = max(0, len(typed) - len(passage))

        passage_words = re.findall(r"\S+", passage)
        typed_words = re.findall(r"\S+", typed)
        minw = min(len(passage_words), len(typed_words))
        wrong_words = []
        for i in range(minw):
            if passage_words[i] != typed_words[i]:
                wrong_words.append((passage_words[i], typed_words[i]))
        missing_words = passage_words[minw:]
        extra_words = typed_words[minw:]

        return {
            "total_chars": total_chars,
            "correct_chars": correct_chars,
            "incorrect_chars": incorrect_chars,
            "missing_chars": missing_chars,
            "extra_chars": extra_chars,
            "wrong_words": wrong_words,
            "missing_words": missing_words,
            "extra_words": extra_words,
        }

    def _show_mistake_summary(self, typed, wpm, accuracy):
        stats = self._compute_mistake_stats(typed)

        win = tk.Toplevel(self)
        win.title("Mistake Summary")
        win.geometry("520x420")
        win.resizable(False, False)

        frm = ttk.Frame(win, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(
            frm,
            text=f"Summary — WPM: {wpm:.2f}, Accuracy: {accuracy:.2f}%",
            font=("Helvetica", 11, "bold")
        )
        header.pack(pady=(0, 6))

        info = (
            f"Total characters in passage: {stats['total_chars']}\n"
            f"Correct characters: {stats['correct_chars']}\n"
            f"Incorrect characters: {stats['incorrect_chars']}\n"
            f"Missing characters: {stats['missing_chars']}\n"
            f"Extra characters typed: {stats['extra_chars']}\n"
            f"\nWrong words: {len(stats['wrong_words'])}\n"
            f"Missing words: {len(stats['missing_words'])}\n"
            f"Extra words: {len(stats['extra_words'])}\n"
        )
        ttk.Label(frm, text=info, justify="left").pack(anchor="w")

        text_frame = ttk.LabelFrame(frm, text="Details of wrong words", padding=6)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        txt = tk.Text(text_frame, height=10, wrap="word", font=("Helvetica", 10))
        txt.pack(fill=tk.BOTH, expand=True)

        if stats["wrong_words"]:
            txt.insert(tk.END, "Expected  ->  Typed\n\n")
            for expected, typed_word in stats["wrong_words"]:
                txt.insert(tk.END, f"{expected}  ->  {typed_word}\n")
        else:
            txt.insert(tk.END, "Nice! No word-level mismatches were detected.\n")

        txt.configure(state=tk.DISABLED)

        ttk.Button(frm, text="Close", command=win.destroy).pack(pady=(6, 0))

    def _finish_test(self):
        typed = self.input_entry.get("1.0", tk.END).rstrip("\n")
        elapsed = max(1e-6, self.elapsed)
        num_words = len(typed.split())
        wpm = (num_words / elapsed) * 60 if elapsed > 0 else 0.0

        correct = sum(
            typed[i] == self.current_passage[i]
            for i in range(min(len(typed), len(self.current_passage)))
        )
        # NEW ACCURACY: only consider typed characters
        accuracy = (correct / max(1, len(typed))) * 100 if typed else 0.0

        self._play_end_sound()

        msg = f"WPM: {wpm:.2f}\nAccuracy: {accuracy:.2f}%"
        if messagebox.askyesno("Result", msg + "\n\nSave to leaderboard?"):
            name = simpledialog.askstring("Name", "Enter your name:", parent=self)
            if name:
                add_score_to_leaderboard(name, round(wpm, 2), round(accuracy, 2))
                messagebox.showinfo("Saved", "Score saved.")

        # Always show mistake summary after test
        self._show_mistake_summary(typed, wpm, accuracy)

    # -----------------------
    # Leaderboard window
    # -----------------------

    def show_leaderboard(self):
        board = load_leaderboard()
        win = tk.Toplevel(self)
        win.title("Leaderboard")
        win.geometry("480x420")
        win.resizable(False, False)

        frm = ttk.Frame(win, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Top WPM Leaderboard", font=("Helvetica", 12, "bold")).pack(pady=(0, 6))

        columns = ("pos", "name", "wpm", "acc")
        tree = ttk.Treeview(frm, columns=columns, show="headings", height=14)
        tree.heading("pos", text="#")
        tree.heading("name", text="Name")
        tree.heading("wpm", text="WPM")
        tree.heading("acc", text="Accuracy")
        tree.column("pos", width=40, anchor="center")
        tree.column("name", width=220)
        tree.column("wpm", width=80, anchor="center")
        tree.column("acc", width=80, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True)

        for i, e in enumerate(board, start=1):
            tree.insert("", "end", values=(i, e["name"], e["wpm"], f"{e['accuracy']}%"))

        ttk.Button(frm, text="Close", command=win.destroy).pack(pady=(8, 0))


# -----------------------
def main():
    app = TypingApp()
    app.mainloop()


if __name__ == "__main__":
    main()
