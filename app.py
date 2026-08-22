import streamlit as st
import pymupdf as fitz
import pytesseract
from PIL import Image
import re
import io
from datetime import datetime
from collections import Counter

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Social Media Content Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# THEME — "The Copy Desk": a newsroom-at-night read on the editor who checks
# a draft before it runs. Suggestions are margin notes in three inks (red
# pen for fixes, sage stamp for approvals, brass pencil for ideas); the
# score is a hand-stamped verdict, not a dashboard gauge.
# ----------------------------------------------------------------------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    :root {
        --bg: #1B1815;
        --panel: #24201A;
        --panel-alt: #18140F;
        --border: #3A342A;
        --text: #F1EAD9;
        --text-muted: #A69C87;

        --brand: #4C7A8C;          /* fountain-pen blue — primary accent */
        --brand-bg: #16262B;
        --brand-border: #294A54;

        --good: #7FAE84;           /* sage approval stamp */
        --good-bg: #1B2A1F;
        --good-border: #30452F;
        --good-text: #A9CBA3;

        --warn: #C1584A;           /* editor's red pen */
        --warn-bg: #2E1A15;
        --warn-border: #4A2A20;
        --warn-text: #E29A8C;

        --tip: #D3A24C;            /* brass highlighter */
        --tip-bg: #2E2412;
        --tip-border: #4A3A1C;
        --tip-text: #E8C583;

        --neg-bg: #2E1A15;
        --neg-text: #E29A8C;

        --font-display: 'Fraunces', Georgia, serif;
        --font-body: 'Inter', -apple-system, sans-serif;
        --font-mono: 'IBM Plex Mono', ui-monospace, monospace;
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation-duration: 0.001ms !important; transition-duration: 0.001ms !important; }
    }

    .stApp { background: var(--bg); font-family: var(--font-body); }
    .main .block-container { padding-top: 2.25rem; max-width: 1150px; }
    body, p, span, div, label { color: var(--text); }

    /* ---------- Top toolbar (Streamlit chrome) ---------- */
    header[data-testid="stHeader"] {
        background: var(--bg) !important; border-bottom: 1px solid var(--border);
    }
    header[data-testid="stHeader"] * { color: var(--text-muted) !important; }
    div[data-testid="stToolbar"] { background: var(--bg) !important; }
    div[data-testid="stDecoration"] { background: var(--brand) !important; }

    /* ---------- Header / masthead ---------- */
    .masthead { margin-bottom: 1.75rem; border-bottom: 1px solid var(--border); padding-bottom: 1.25rem; }
    .eyebrow {
        font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.18em;
        text-transform: uppercase; color: var(--brand); margin: 0 0 0.4rem 0; font-weight: 600;
    }
    .app-title {
        font-family: var(--font-display); font-size: 2.35rem; font-weight: 600;
        margin: 0; color: var(--text); letter-spacing: -0.01em;
    }
    .app-subtitle {
        font-family: var(--font-body); color: var(--text-muted); font-size: 1rem;
        margin-top: 0.5rem; margin-bottom: 0; max-width: 640px; line-height: 1.5;
    }

    /* ---------- Uploader ---------- */
    div[data-testid="stFileUploaderDropzone"] {
        border-radius: 4px; border: 1.5px dashed var(--border); background: var(--panel-alt);
        transition: border-color 0.15s ease, background 0.15s ease;
    }
    div[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--brand); background: var(--brand-bg); }
    div[data-testid="stFileUploaderDropzone"] * { color: var(--text-muted) !important; font-family: var(--font-body) !important; }
    section[data-testid="stFileUploader"] small { color: var(--text-muted) !important; }
    div[data-testid="stFileUploaderDropzone"] button {
        border: 1px solid var(--border) !important; border-radius: 4px !important;
        background: var(--panel) !important; color: var(--text) !important;
    }

    /* ---------- Metrics (word/char/hashtag/mention strip) ---------- */
    div[data-testid="stMetric"] {
        background: var(--panel); border: 1px solid var(--border); border-radius: 4px;
        padding: 0.9rem 1rem 0.75rem 1rem; border-left: 2px solid var(--brand);
    }
    div[data-testid="stMetricLabel"] {
        font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.06em;
        text-transform: uppercase; font-weight: 500; color: var(--text-muted);
    }
    div[data-testid="stMetricValue"] { font-family: var(--font-display); color: var(--text); font-size: 1.6rem; }

    /* ---------- Score stamp (signature element) ---------- */
    .score-wrap {
        display: flex; align-items: center; gap: 1.5rem; background: var(--panel);
        border: 1px solid var(--border); border-radius: 4px; padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem; position: relative; overflow: hidden;
    }
    .score-stamp {
        width: 84px; height: 84px; border-radius: 50%; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
        border: 2.5px dashed currentColor; transform: rotate(-6deg);
        font-family: var(--font-mono); font-weight: 600; font-size: 1.7rem;
        animation: stamp-in 0.35s ease-out;
    }
    @keyframes stamp-in {
        0% { transform: rotate(-6deg) scale(1.4); opacity: 0; }
        100% { transform: rotate(-6deg) scale(1); opacity: 1; }
    }
    .score-text-eyebrow {
        font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 0.12em;
        text-transform: uppercase; color: var(--text-muted); margin: 0 0 0.15rem 0;
    }
    .score-text-title { font-family: var(--font-display); font-weight: 600; font-size: 1.25rem; margin: 0; color: var(--text); }
    .score-text-sub { color: var(--text-muted); margin: 0.25rem 0 0 0; font-size: 0.88rem; font-family: var(--font-body); }

    /* ---------- Suggestion cards (margin notes) ---------- */
    .suggestion-tally {
        font-family: var(--font-mono); font-size: 0.82rem; color: var(--text-muted);
        margin-bottom: 1rem; letter-spacing: 0.02em;
    }
    .suggestion-tally b { color: var(--text); }
    .suggestion-card {
        display: flex; align-items: flex-start; gap: 0.85rem; border-radius: 4px;
        padding: 0.85rem 1rem; margin-bottom: 0.55rem; border-left: 3px solid transparent;
        background: var(--panel-alt); font-size: 0.95rem; line-height: 1.45;
        font-family: var(--font-body);
    }
    .suggestion-tag {
        font-family: var(--font-mono); font-size: 0.65rem; letter-spacing: 0.08em;
        font-weight: 600; padding: 0.15rem 0.45rem; border-radius: 3px;
        flex-shrink: 0; margin-top: 0.1rem; white-space: nowrap;
    }
    .suggestion-good { border-left-color: var(--good); color: var(--good-text); }
    .suggestion-good .suggestion-tag { background: var(--good-bg); color: var(--good-text); border: 1px solid var(--good-border); }
    .suggestion-warn { border-left-color: var(--warn); color: var(--warn-text); }
    .suggestion-warn .suggestion-tag { background: var(--warn-bg); color: var(--warn-text); border: 1px solid var(--warn-border); }
    .suggestion-tip { border-left-color: var(--tip); color: var(--tip-text); }
    .suggestion-tip .suggestion-tag { background: var(--tip-bg); color: var(--tip-text); border: 1px solid var(--tip-border); }

    /* ---------- Insight badges ---------- */
    .insight-badge {
        display: inline-block; padding: 0.35rem 0.8rem; border-radius: 3px;
        font-family: var(--font-mono); font-weight: 500; font-size: 0.78rem;
        letter-spacing: 0.02em; margin-right: 0.45rem; margin-bottom: 0.5rem;
        border: 1px solid var(--border);
    }
    .badge-pos { background: var(--good-bg); color: var(--good-text); border-color: var(--good-border); }
    .badge-neg { background: var(--neg-bg); color: var(--neg-text); border-color: var(--warn-border); }
    .badge-neu { background: var(--panel-alt); color: var(--text-muted); }
    .badge-info { background: var(--brand-bg); color: #9FC3D1; border-color: var(--brand-border); }

    /* ---------- Sidebar / revision log ---------- */
    section[data-testid="stSidebar"] { background: var(--panel-alt); border-right: 1px solid var(--border); }
    section[data-testid="stSidebar"] h3 {
        font-family: var(--font-mono) !important; font-size: 0.78rem !important;
        letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted) !important;
    }
    .history-item {
        border-left: 2px solid var(--brand); background: var(--panel); border-radius: 3px;
        padding: 0.55rem 0.75rem; margin-bottom: 0.5rem; font-size: 0.8rem;
        font-family: var(--font-mono); color: var(--text);
    }
    .history-item b { color: var(--text); }

    /* ---------- Empty state ---------- */
    .empty-state {
        text-align: center; padding: 4rem 1.5rem; color: var(--text-muted);
        border: 1.5px dashed var(--border); border-radius: 4px; font-family: var(--font-body);
    }
    .empty-state-mark { font-family: var(--font-display); font-style: italic; font-size: 1.4rem; color: var(--text); margin-bottom: 0.4rem; }
    .empty-state-sub { font-size: 0.9rem; }

    /* ---------- Text areas ---------- */
    textarea {
        border-radius: 4px !important; background: var(--panel-alt) !important;
        color: var(--text) !important; border: 1px solid var(--border) !important;
        font-family: var(--font-body) !important;
    }
    textarea:focus { border-color: var(--brand) !important; box-shadow: 0 0 0 1px var(--brand) !important; }

    /* ---------- Tabs ---------- */
    button[data-baseweb="tab"] {
        color: var(--text-muted); font-family: var(--font-mono); font-size: 0.85rem;
        letter-spacing: 0.02em; text-transform: uppercase;
    }
    button[data-baseweb="tab"][aria-selected="true"] { color: var(--text); }
    div[data-baseweb="tab-highlight"] { background-color: var(--brand) !important; }

    /* ---------- Selectbox / inputs ---------- */
    div[data-baseweb="select"] > div {
        background: var(--panel-alt) !important; border-color: var(--border) !important;
        border-radius: 4px !important; color: var(--text) !important;
    }
    div[data-baseweb="select"] div[role="button"] { color: var(--text) !important; }
    div[data-baseweb="select"] svg { fill: var(--text-muted) !important; }
    ul[data-baseweb="menu"] {
        background: var(--panel) !important; border: 1px solid var(--border) !important;
    }
    ul[data-baseweb="menu"] li { color: var(--text) !important; font-family: var(--font-body) !important; }
    ul[data-baseweb="menu"] li:hover { background: var(--panel-alt) !important; }
    div[data-baseweb="popover"] { background: var(--panel) !important; }

    /* ---------- Buttons ---------- */
    .stButton button, .stDownloadButton button {
        border-radius: 4px !important; border: 1px solid var(--border) !important;
        font-family: var(--font-body) !important; font-weight: 500 !important;
        transition: border-color 0.15s ease, transform 0.1s ease;
    }
    .stButton button:hover, .stDownloadButton button:hover { border-color: var(--brand) !important; }
    button[kind="primary"] { background: var(--brand) !important; border-color: var(--brand) !important; }

    /* Keyboard focus visibility */
    button:focus-visible, [tabindex]:focus-visible, input:focus-visible {
        outline: 2px solid var(--brand) !important; outline-offset: 2px;
    }

    /* ---------- Expanders / tooltips / misc chrome ---------- */
    div[data-testid="stExpander"] {
        background: var(--panel); border: 1px solid var(--border) !important; border-radius: 4px;
    }
    div[data-testid="stExpander"] summary { color: var(--text) !important; }
    [data-testid="stTooltipIcon"] svg { fill: var(--text-muted) !important; }
    div[data-baseweb="tooltip"] { background: var(--panel) !important; color: var(--text) !important; }

    /* ---------- Caption text ---------- */
    .stCaption, [data-testid="stCaptionContainer"] { color: var(--text-muted) !important; font-family: var(--font-body) !important; }

    /* ---------- Section subheads inside results (Version A / B etc.) ---------- */
    h4 { font-family: var(--font-display) !important; font-weight: 600 !important; color: var(--text) !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
st.markdown("""
<div class="masthead">
    <p class="eyebrow">Before it runs &middot; a quick read from the desk</p>
    <p class="app-title">Social Media Content Analyzer</p>
    <p class="app-subtitle">Upload or paste a post, pick a platform, and get a full engagement breakdown — sentiment, readability, tone, keywords, and more. Runs entirely locally, no external API.</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ----------------------------------------------------------------------------
# PLATFORM PROFILES
# ----------------------------------------------------------------------------
PLATFORMS = {
    "Twitter / X": {"char_limit": 280, "hashtag_range": (1, 2), "ideal_words": (10, 40), "tone": "punchy, casual"},
    "Instagram": {"char_limit": 2200, "hashtag_range": (5, 15), "ideal_words": (20, 150), "tone": "visual, casual"},
    "LinkedIn": {"char_limit": 3000, "hashtag_range": (3, 5), "ideal_words": (50, 200), "tone": "professional"},
    "Facebook": {"char_limit": 63206, "hashtag_range": (0, 2), "ideal_words": (10, 80), "tone": "conversational"},
}

# ----------------------------------------------------------------------------
# LEXICONS (lightweight, no external NLP downloads needed)
# ----------------------------------------------------------------------------
POSITIVE_WORDS = set("""great amazing awesome excellent fantastic love loved loving best happy excited
thrilled wonderful brilliant incredible perfect win winning success proud grateful thankful delighted
inspire inspiring innovative growth achieve achieved milestone celebrate celebrating good nice cool
beautiful fun exciting glad joy""".split())

NEGATIVE_WORDS = set("""bad worst hate hated terrible awful horrible fail failed failure sad angry annoyed
disappointed frustrating frustrated problem issue broken worse worst sorry unfortunately concern concerned
struggle struggling difficult hard painful worried worry crisis loss lost""".split())

FORMAL_WORDS = set("""therefore however furthermore moreover consequently regarding pursuant accordingly
whom shall hereby thus additionally significant substantial demonstrate implement leverage utilize
organization stakeholders strategic initiative""".split())

CASUAL_MARKERS = ["'m", "'re", "'s", "'ve", "'ll", "n't", "lol", "omg", "gonna", "wanna", "tbh", "btw", "hey", "yeah"]

STOPWORDS = set("""the a an and or but if of to in on for with is are was were be been being this that
these those it its i you he she we they my your our their as at by from up down out about into over
after before between not no yes so than then there here can will would could should just also more most
""".split())

# ----------------------------------------------------------------------------
# OCR / EXTRACTION HELPERS
# ----------------------------------------------------------------------------

# Legacy pre-Unicode Indic fonts (glyphs remapped onto ASCII code points, no
# ToUnicode CMap). Any PDF using one of these will extract as gibberish no
# matter what library is used — the fix is OCR, not better text extraction.
LEGACY_INDIC_FONT_MARKERS = ["krutidev", "devlys", "chanakya", "shusha", "walkman", "agra"]


def page_uses_legacy_indic_font(page):
    """True if the page embeds a known non-Unicode legacy Hindi/Devanagari font."""
    try:
        font_names = " ".join(f[3].lower() for f in page.get_fonts())
    except Exception:
        return False
    return any(marker in font_names for marker in LEGACY_INDIC_FONT_MARKERS)


def get_available_ocr_langs():
    """Return the set of installed Tesseract language packs, or None if the
    Tesseract engine itself isn't installed at all (distinct from just
    missing a specific language pack)."""
    try:
        return set(pytesseract.get_languages(config=""))
    except pytesseract.TesseractNotFoundError:
        return None
    except Exception:
        return {"eng"}


def preprocess_for_ocr(image):
    """Grayscale, upscale small images, and threshold for better OCR contrast.

    Raw screenshots (busy backgrounds, low resolution, gradients behind text)
    are the main reason Tesseract returns garbled or partial results, so this
    normalizes the image before OCR runs.
    """
    img = image.convert("L")  # grayscale

    # Upscale small images — Tesseract wants roughly 300dpi-equivalent detail
    w, h = img.size
    longest_side = max(w, h)
    if longest_side < 1500:
        scale = 1500 / longest_side
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Simple binarization to boost contrast against busy/gradient backgrounds
    img = img.point(lambda x: 0 if x < 150 else 255, "1")
    return img


def run_ocr(image, lang="eng"):
    """OCR a single image with layout hint tuned for social captions.

    --psm 6 ("assume a single uniform block of text") performs much better
    on captions than the default psm 3, which tries to auto-detect complex
    multi-region layouts and often mis-segments a simple caption + UI chrome.
    """
    processed = preprocess_for_ocr(image)
    return pytesseract.image_to_string(processed, lang=lang, config="--psm 6")


def extract_pdf_text(pdf):
    """Extract text from a PDF, sorted into natural reading order."""
    text = ""
    for page in pdf:
        text += page.get_text("text", sort=True)
    return text


def pdf_text_needs_ocr(text, num_pages, pdf=None):
    """Decide whether extracted PDF text is usable or needs an OCR fallback.

    Two independent triggers:
    1. Density: empty or near-empty extraction (scanned/image-only PDF).
    2. Legacy fonts: pages using a non-Unicode Indic font (e.g. KrutiDev)
       extract as gibberish even though plenty of "text" comes out — the
       character codes just don't mean what they claim to. No density
       check can catch this, so we check font names directly.
    """
    stripped = text.strip()
    if not stripped:
        return True
    avg_chars_per_page = len(stripped) / max(1, num_pages)
    if avg_chars_per_page < 20:
        return True
    if pdf is not None and any(page_uses_legacy_indic_font(p) for p in pdf):
        return True
    return False

# ----------------------------------------------------------------------------
# ANALYSIS HELPERS
# ----------------------------------------------------------------------------

def count_syllables(word):
    word = word.lower().strip(".,!?;:\"'()")
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def flesch_reading_ease(text):
    sentences = re.split(r"[.!?]+", text)
    sentences = [s for s in sentences if s.strip()]
    words = re.findall(r"[A-Za-z']+", text)
    if not sentences or not words:
        return None
    syllable_count = sum(count_syllables(w) for w in words)
    asl = len(words) / len(sentences)
    asw = syllable_count / len(words)
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    return round(max(0, min(100, score)), 1)


def readability_label(score):
    if score is None:
        return "N/A", "Not enough text to measure."
    if score >= 70:
        return "Easy to read", "Great for a broad, casual audience."
    elif score >= 50:
        return "Moderate", "Fairly accessible, some effort to read."
    else:
        return "Complex", "May be harder for a general audience to skim quickly."


def analyze_sentiment(text):
    words = re.findall(r"[A-Za-z']+", text.lower())
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    if pos == 0 and neg == 0:
        return "Neutral", pos, neg
    if pos > neg:
        return "Positive", pos, neg
    elif neg > pos:
        return "Negative", pos, neg
    return "Mixed", pos, neg


def detect_tone(text):
    lower = text.lower()
    formal_hits = sum(1 for w in FORMAL_WORDS if w in lower)
    casual_hits = sum(1 for marker in CASUAL_MARKERS if marker in lower)
    if formal_hits > casual_hits:
        return "Formal / Professional"
    elif casual_hits > formal_hits:
        return "Casual / Conversational"
    return "Neutral"


def get_top_keywords(text, n=8):
    words = re.findall(r"[A-Za-z']{3,}", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    counts = Counter(filtered)
    return counts.most_common(n)


def analyze_content(text, platform):
    """Rule-based, platform-aware engagement suggestions."""
    profile = PLATFORMS[platform]
    suggestions = []
    word_count = len(text.split())
    char_count = len(text)
    min_w, max_w = profile["ideal_words"]

    if word_count < min_w:
        suggestions.append(("warn", f"Post is short for {platform} — ideal range is {min_w}-{max_w} words. Consider adding more context or a hook."))
    elif word_count > max_w:
        suggestions.append(("warn", f"Post is longer than typical for {platform} (ideal: {min_w}-{max_w} words). Consider trimming."))
    else:
        suggestions.append(("good", f"Word count fits {platform}'s sweet spot ({min_w}-{max_w} words)."))

    if char_count > profile["char_limit"]:
        suggestions.append(("warn", f"Exceeds {platform}'s character limit ({profile['char_limit']}). Currently {char_count} characters."))
    else:
        suggestions.append(("good", f"Within {platform}'s character limit ({char_count}/{profile['char_limit']})."))

    hashtags = re.findall(r"#\w+", text)
    h_min, h_max = profile["hashtag_range"]
    if len(hashtags) < h_min:
        suggestions.append(("tip", f"{platform} posts typically use {h_min}-{h_max} hashtags. You have {len(hashtags)}."))
    elif len(hashtags) > h_max:
        suggestions.append(("warn", f"You have {len(hashtags)} hashtags — {platform} performs better with {h_min}-{h_max}."))
    else:
        suggestions.append(("good", f"Hashtag count ({len(hashtags)}) fits {platform} norms."))

    mentions = re.findall(r"@\w+", text)
    if mentions:
        suggestions.append(("good", f"Tagging {len(mentions)} account(s) — can help boost reach."))

    cta_keywords = ["comment", "share", "follow", "click", "link in bio", "sign up", "learn more", "check out", "subscribe"]
    if not any(kw in text.lower() for kw in cta_keywords):
        suggestions.append(("tip", "No clear call-to-action detected. Try ending with 'Comment below' or 'Share your thoughts'."))
    else:
        suggestions.append(("good", "Clear call-to-action detected."))

    if "?" not in text:
        suggestions.append(("tip", "Consider adding a question to encourage replies."))
    else:
        suggestions.append(("good", "A question in your post can help drive replies."))

    emoji_pattern = re.compile("[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F600-\U0001F64F]+")
    if not emoji_pattern.search(text):
        suggestions.append(("tip", "No emojis detected — a few relevant ones can add personality (use sparingly)."))
    else:
        suggestions.append(("good", "Good use of emojis."))

    first_line = text.strip().split("\n")[0] if text.strip() else ""
    if len(first_line.split()) > 20:
        suggestions.append(("warn", "Opening line is long — a short, punchy hook grabs attention faster."))

    score = 100
    for kind, _ in suggestions:
        if kind == "warn":
            score -= 15
        elif kind == "tip":
            score -= 8
    score = max(0, min(100, score))

    return suggestions, word_count, len(hashtags), len(mentions), char_count, score


TAGS = {"good": "APPROVED", "warn": "FIX THIS", "tip": "TRY THIS"}
CLASS = {"good": "suggestion-good", "warn": "suggestion-warn", "tip": "suggestion-tip"}


def score_color(score):
    if score >= 80:
        return "var(--good)"
    elif score >= 55:
        return "var(--tip)"
    return "var(--warn)"


def score_verdict(score):
    if score >= 80:
        return "READY"
    elif score >= 55:
        return "REVISE"
    return "REWORK"


def score_label(score):
    if score >= 80:
        return "Great shape — minor tweaks only"
    elif score >= 55:
        return "Decent, but a few things to improve"
    return "Needs work before you post"


def render_score_block(score):
    color = score_color(score)
    st.markdown(f"""
    <div class="score-wrap">
        <div class="score-stamp" style="color:{color};">{score}</div>
        <div>
            <p class="score-text-eyebrow">Desk verdict &middot; {score_verdict(score)}</p>
            <p class="score-text-title">{score_label(score)}</p>
            <p class="score-text-sub">Based on platform-fit length, hashtags, mentions, CTA, hooks and emoji usage.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_insights(text):
    sentiment, pos, neg = analyze_sentiment(text)
    tone = detect_tone(text)
    flesch = flesch_reading_ease(text)
    read_label, read_desc = readability_label(flesch)
    reading_time = max(1, round(len(text.split()) / 200 * 60))

    sentiment_class = {"Positive": "badge-pos", "Negative": "badge-neg", "Mixed": "badge-info", "Neutral": "badge-neu"}[sentiment]

    st.markdown(
        f'<span class="insight-badge {sentiment_class}">🎭 Sentiment: {sentiment}</span>'
        f'<span class="insight-badge badge-info">🗣️ Tone: {tone}</span>'
        f'<span class="insight-badge badge-neu">📖 Readability: {read_label}{"" if flesch is None else f" ({flesch})"}</span>'
        f'<span class="insight-badge badge-neu">⏱️ ~{reading_time}s read</span>',
        unsafe_allow_html=True
    )
    st.caption(read_desc)

    keywords = get_top_keywords(text)
    if keywords:
        st.markdown("**Top keywords**")
        kw_dict = {word: count for word, count in keywords}
        st.bar_chart(kw_dict, color="#818CF8")
    else:
        st.caption("Not enough distinct words to chart keywords.")


def display_results(extracted_text, source_label, platform, save_to_history=True):
    suggestions, word_count, hashtag_count, mention_count, char_count, score = analyze_content(extracted_text, platform)
    render_score_block(score)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Word Count", word_count)
    col2.metric("Characters", char_count)
    col3.metric("Hashtags", hashtag_count)
    col4.metric("Mentions", mention_count)

    tab1, tab2, tab3 = st.tabs(["💡 Suggestions", "🔍 Insights", "📄 Extracted Text"])

    with tab1:
        n_good = sum(1 for k, _ in suggestions if k == "good")
        n_warn = sum(1 for k, _ in suggestions if k == "warn")
        n_tip = sum(1 for k, _ in suggestions if k == "tip")
        st.markdown(
            f'<div class="suggestion-tally"><b>{n_warn}</b> to fix &middot; '
            f'<b>{n_good}</b> approved &middot; <b>{n_tip}</b> worth trying</div>',
            unsafe_allow_html=True,
        )
        for kind, msg in suggestions:
            st.markdown(
                f'<div class="suggestion-card {CLASS[kind]}">'
                f'<span class="suggestion-tag">{TAGS[kind]}</span><span>{msg}</span></div>',
                unsafe_allow_html=True,
            )
        report_lines = [
            "Social Media Content Analyzer — Report",
            f"Platform: {platform}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Engagement Score: {score}/100 ({score_label(score)})",
            f"Word Count: {word_count} | Characters: {char_count} | Hashtags: {hashtag_count} | Mentions: {mention_count}",
            "", "Suggestions:",
        ]
        for kind, msg in suggestions:
            report_lines.append(f"- [{TAGS[kind]}] {msg}")
        st.download_button("Download desk notes (.txt)", data="\n".join(report_lines),
                            file_name="engagement_report.txt", mime="text/plain")

    with tab2:
        render_insights(extracted_text)

    with tab3:
        if extracted_text.strip():
            st.text_area(f"Content found in your {source_label}:", extracted_text, height=250, key=f"text_{source_label}_{len(st.session_state.history)}")
        else:
            st.warning(f"No text could be extracted from this {source_label}.")

    if save_to_history:
        st.session_state.history.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "source": source_label,
            "platform": platform,
            "score": score,
            "words": word_count,
        })

    return score


# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### How it works")
    st.markdown(
        "1. Pick a **platform**\n"
        "2. **Upload** a PDF/image or **paste** text\n"
        "3. Get a **score**, sentiment, tone, readability & suggestions"
    )
    st.divider()
    st.markdown("### What the desk checks")
    st.markdown(
        "- Platform-fit length & character limit\n- Hashtags & mentions\n"
        "- Call-to-action & hooks\n- Sentiment & tone\n- Readability (Flesch score)\n- Top keywords"
    )
    st.divider()
    st.markdown("### Revision log")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-8:]):
            st.markdown(
                f'<div class="history-item">{item["time"]} &middot; <b>{item["source"]}</b> &middot; {item["platform"]}<br>'
                f'{item["score"]}/100 &middot; {item["words"]} words</div>',
                unsafe_allow_html=True
            )
        if st.button("Clear log", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("Nothing reviewed yet this session.")
    st.divider()
    st.caption("Everything runs locally — your content isn't sent to any third-party API.")

# ----------------------------------------------------------------------------
# MAIN TABS: Analyze vs Compare
# ----------------------------------------------------------------------------
mode_tab1, mode_tab2 = st.tabs(["Upload & Analyze", "Compare Two Versions"])

with mode_tab1:
    platform = st.selectbox("Choose platform", list(PLATFORMS.keys()), key="platform_upload")

    uploaded_file = st.file_uploader(
        "Drop a PDF or image here, or click to browse",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Supported formats: PDF, PNG, JPG, JPEG",
    )

    if uploaded_file:
        st.toast(f"Uploaded {uploaded_file.name}", icon="✅")
        try:
            if uploaded_file.type == "application/pdf":
                try:
                    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                except Exception:
                    st.error("This PDF could not be read. It may be corrupted or password-protected.")
                    st.stop()

                with st.spinner("Reading PDF..."):
                    extracted_text = extract_pdf_text(pdf)
                    has_legacy_font = any(page_uses_legacy_indic_font(p) for p in pdf)

                if not pdf_text_needs_ocr(extracted_text, len(pdf), pdf=pdf):
                    display_results(extracted_text, "PDF", platform)
                else:
                    available_langs = get_available_ocr_langs()

                    if available_langs is None:
                        # Tesseract engine itself isn't installed — say so plainly,
                        # don't imply it's just a missing language pack.
                        st.error("Tesseract OCR engine is not installed on this system, so this PDF's text can't be recovered. Install it (e.g. `apt-get install tesseract-ocr`), or upload this page as an image instead.")
                    else:
                        if has_legacy_font:
                            st.info("This PDF uses a legacy Hindi font (e.g. KrutiDev) whose text can't be extracted directly — its characters don't map to real Unicode. Running OCR instead, which reads the rendered glyphs visually.")
                        else:
                            st.info("Little or no usable text layer found — this looks like a scanned PDF. Running OCR on each page instead...")

                        ocr_lang = "eng+hin" if (has_legacy_font and "hin" in available_langs) else "eng"
                        if has_legacy_font and "hin" not in available_langs:
                            st.warning("The Hindi OCR language pack (tesseract-ocr-hin) isn't installed, so Hindi text will still come out incorrectly. English portions will still extract correctly. Install it with `apt-get install tesseract-ocr-hin` to fix this.")

                        try:
                            with st.spinner(f"Running OCR on {len(pdf)} page(s)..."):
                                ocr_text = ""
                                for page_num, page in enumerate(pdf):
                                    # Render at 2x zoom for sharper OCR results
                                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                                    img_bytes = pix.tobytes("png")
                                    page_image = Image.open(io.BytesIO(img_bytes))
                                    ocr_text += run_ocr(page_image, lang=ocr_lang) + "\n"

                            if ocr_text.strip():
                                st.success(f"Recovered text via OCR from {len(pdf)} page(s).")
                                display_results(ocr_text, "scanned PDF (OCR)", platform)
                            else:
                                st.warning("OCR ran but found no readable text. Try a higher-quality scan or upload as an image instead.")
                        except pytesseract.TesseractNotFoundError:
                            st.error("Tesseract OCR engine is not installed on this system, so scanned PDFs can't be read. Please install it, or upload this page as an image instead.")
                        except Exception as e:
                            st.error(f"OCR on the PDF failed: {e}")

            else:
                try:
                    image = Image.open(uploaded_file)
                    image.verify()
                    uploaded_file.seek(0)
                    image = Image.open(uploaded_file)
                except Exception:
                    st.error("This image could not be read. It may be corrupted or unsupported.")
                    st.stop()

                with st.expander("🖼️ Uploaded Image", expanded=True):
                    st.image(image, use_container_width=True)

                with st.spinner("Extracting text using OCR..."):
                    try:
                        extracted_text = run_ocr(image)
                    except pytesseract.TesseractNotFoundError:
                        st.error("Tesseract OCR engine is not installed on this system.")
                        st.stop()
                    except Exception as e:
                        st.error(f"OCR failed unexpectedly: {e}")
                        st.stop()

                display_results(extracted_text, "image", platform)

        except Exception as e:
            st.error(f"Something went wrong while processing your file: {e}")

    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-mark">The desk is clear.</div>
            <div class="empty-state-sub">Upload a PDF or image of your post above to get it reviewed.</div>
        </div>
        """, unsafe_allow_html=True)

with mode_tab2:
    st.markdown("Paste two versions of the same post and see which one is likely to perform better.")
    platform_c = st.selectbox("Choose platform", list(PLATFORMS.keys()), key="platform_compare")

    colA, colB = st.columns(2)
    with colA:
        text_a = st.text_area("Version A", height=180, placeholder="Paste your first draft here...")
    with colB:
        text_b = st.text_area("Version B", height=180, placeholder="Paste your alternate draft here...")

    if st.button("Compare", type="primary", use_container_width=True):
        if not text_a.strip() or not text_b.strip():
            st.warning("Please paste text into both boxes to compare.")
        else:
            resA, resB = st.columns(2)
            with resA:
                st.markdown("#### Version A")
                score_a = display_results(text_a, "Version A", platform_c, save_to_history=False)
            with resB:
                st.markdown("#### Version B")
                score_b = display_results(text_b, "Version B", platform_c, save_to_history=False)

            if score_a != score_b:
                winner = "A" if score_a > score_b else "B"
                st.success(f"Version {winner} is the stronger draft ({max(score_a, score_b)} vs {min(score_a, score_b)}).")
            else:
                st.info("Dead heat — both versions score the same.")