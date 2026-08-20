import streamlit as st
import pymupdf as fitz
import pytesseract
from PIL import Image
import re
from datetime import datetime

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
# STYLES
# ----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Overall page */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    /* Header */
    .app-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.25rem;
    }
    .app-title {
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(90deg, #6366F1, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .app-subtitle {
        color: #6B7280;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 1.75rem;
    }

    /* Uploader card */
    .stFileUploader {
        border-radius: 14px;
    }
    div[data-testid="stFileUploaderDropzone"] {
        border-radius: 14px;
        border: 2px dashed #C7C9F5;
        background: #FAFAFF;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #EEF0F6;
        border-radius: 14px;
        padding: 1rem 1rem 0.75rem 1rem;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.04);
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #6B7280;
    }

    /* Score badge */
    .score-wrap {
        display: flex;
        align-items: center;
        gap: 1.25rem;
        background: #FFFFFF;
        border: 1px solid #EEF0F6;
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.04);
    }
    .score-circle {
        width: 78px;
        height: 78px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: 800;
        color: white;
        flex-shrink: 0;
    }
    .score-text-title {
        font-weight: 700;
        font-size: 1.05rem;
        margin: 0;
    }
    .score-text-sub {
        color: #6B7280;
        margin: 0;
        font-size: 0.9rem;
    }

    /* Suggestion cards */
    .suggestion-card {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.6rem;
        border: 1px solid transparent;
        font-size: 0.95rem;
        line-height: 1.4;
    }
    .suggestion-icon {
        font-size: 1.1rem;
        margin-top: 0.05rem;
    }
    .suggestion-good {
        background: #F0FDF4;
        border-color: #DCFCE7;
        color: #166534;
    }
    .suggestion-warn {
        background: #FFFBEB;
        border-color: #FEF3C7;
        color: #92400E;
    }
    .suggestion-tip {
        background: #EFF6FF;
        border-color: #DBEAFE;
        color: #1E40AF;
    }

    /* Section headers */
    .section-header {
        font-weight: 700;
        font-size: 1.15rem;
        margin-top: 1.75rem;
        margin-bottom: 0.75rem;
    }

    /* Extracted text box tweak */
    textarea {
        border-radius: 12px !important;
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 3.5rem 1rem;
        color: #9CA3AF;
    }
    .empty-state-emoji {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
st.markdown("""
<div class="app-header">
    <span style="font-size:2rem;">📊</span>
    <p class="app-title">Social Media Content Analyzer</p>
</div>
<p class="app-subtitle">Upload a post (PDF or image) and get instant, rule-based engagement suggestions — no external API needed.</p>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ℹ️ How it works")
    st.markdown(
        "1. **Upload** a PDF or image of your post\n"
        "2. We **extract the text** (OCR for images)\n"
        "3. Get a **score** and actionable suggestions"
    )
    st.divider()
    st.markdown("### ✅ What we check")
    st.markdown(
        "- Post length\n"
        "- Hashtags\n"
        "- Mentions\n"
        "- Call-to-action\n"
        "- Questions / hooks\n"
        "- Emoji usage\n"
        "- Opening line length"
    )
    st.divider()
    st.caption("Everything runs locally — your content isn't sent to any third-party API.")

# ----------------------------------------------------------------------------
# ANALYSIS LOGIC
# ----------------------------------------------------------------------------

def analyze_content(text):
    """Rule-based engagement suggestions. Returns list of (type, message).
    type is one of: 'good', 'warn', 'tip'
    """
    suggestions = []
    word_count = len(text.split())

    # Length checks
    if word_count < 15:
        suggestions.append(("warn", "Your post is quite short — consider adding more context or a call-to-action to boost engagement."))
    elif word_count > 150:
        suggestions.append(("warn", "Your post is fairly long for social media. Consider trimming it — shorter posts often perform better on platforms like Twitter/X or Instagram."))
    else:
        suggestions.append(("good", "Post length looks good for most platforms."))

    # Hashtags
    hashtags = re.findall(r"#\w+", text)
    if not hashtags:
        suggestions.append(("tip", "No hashtags found. Adding 2-5 relevant hashtags can improve discoverability."))
    elif len(hashtags) > 10:
        suggestions.append(("warn", f"You have {len(hashtags)} hashtags — consider trimming to 5-10 for better readability."))
    else:
        suggestions.append(("good", f"Good use of hashtags ({len(hashtags)} found)."))

    # Mentions
    mentions = re.findall(r"@\w+", text)
    if mentions:
        suggestions.append(("good", f"You're tagging {len(mentions)} account(s) — tagging relevant people/brands can boost reach."))

    # Call-to-action check
    cta_keywords = ["comment", "share", "follow", "click", "link in bio", "sign up", "learn more", "check out", "subscribe"]
    has_cta = any(kw in text.lower() for kw in cta_keywords)
    if not has_cta:
        suggestions.append(("tip", "No clear call-to-action detected. Consider ending with a prompt like 'Comment below' or 'Share your thoughts'."))
    else:
        suggestions.append(("good", "Clear call-to-action detected."))

    # Question / engagement hook
    has_question = "?" in text
    if not has_question:
        suggestions.append(("tip", "Consider adding a question to encourage replies and boost engagement."))
    else:
        suggestions.append(("good", "Nice — a question in your post can drive replies."))

    # Emoji check (rough heuristic)
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F600-\U0001F64F]+"
    )
    has_emoji = bool(emoji_pattern.search(text))
    if not has_emoji:
        suggestions.append(("tip", "No emojis detected. A few relevant emojis can make posts feel more approachable (use sparingly)."))
    else:
        suggestions.append(("good", "Good use of emojis to add personality."))

    # First line / hook check
    first_line = text.strip().split("\n")[0] if text.strip() else ""
    if len(first_line.split()) > 20:
        suggestions.append(("warn", "Your opening line is long. A short, punchy hook in the first line grabs attention faster."))

    # Simple score: start at 100, deduct for warns, half-deduct for tips
    score = 100
    for kind, _ in suggestions:
        if kind == "warn":
            score -= 15
        elif kind == "tip":
            score -= 8
    score = max(0, min(100, score))

    return suggestions, word_count, len(hashtags), len(mentions), score


ICONS = {"good": "✅", "warn": "⚠️", "tip": "💡"}
CLASS = {"good": "suggestion-good", "warn": "suggestion-warn", "tip": "suggestion-tip"}


def score_color(score):
    if score >= 80:
        return "#22C55E"  # green
    elif score >= 55:
        return "#F59E0B"  # amber
    else:
        return "#EF4444"  # red


def score_label(score):
    if score >= 80:
        return "Great shape — minor tweaks only"
    elif score >= 55:
        return "Decent, but a few things to improve"
    else:
        return "Needs work before you post"


def display_results(extracted_text, source_label):
    suggestions, word_count, hashtag_count, mention_count, score = analyze_content(extracted_text)
    color = score_color(score)

    # Score summary
    st.markdown(f"""
    <div class="score-wrap">
        <div class="score-circle" style="background:{color};">{score}</div>
        <div>
            <p class="score-text-title">Engagement Score: {score_label(score)}</p>
            <p class="score-text-sub">Based on length, hashtags, mentions, CTA, hooks and emoji usage.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Word Count", word_count)
    col2.metric("Hashtags", hashtag_count)
    col3.metric("Mentions", mention_count)

    # Tabs for extracted text vs suggestions
    tab1, tab2 = st.tabs(["💡 Suggestions", "📄 Extracted Text"])

    with tab1:
        for kind, msg in suggestions:
            st.markdown(
                f'<div class="suggestion-card {CLASS[kind]}">'
                f'<span class="suggestion-icon">{ICONS[kind]}</span>'
                f'<span>{msg}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Downloadable report
        report_lines = [
            "Social Media Content Analyzer — Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Engagement Score: {score}/100 ({score_label(score)})",
            f"Word Count: {word_count} | Hashtags: {hashtag_count} | Mentions: {mention_count}",
            "",
            "Suggestions:",
        ]
        for kind, msg in suggestions:
            report_lines.append(f"- [{kind.upper()}] {msg}")
        report_text = "\n".join(report_lines)

        st.download_button(
            "⬇️ Download Report (.txt)",
            data=report_text,
            file_name="engagement_report.txt",
            mime="text/plain",
            use_container_width=False,
        )

    with tab2:
        if extracted_text.strip():
            st.text_area(
                f"Content found in your {source_label}:",
                extracted_text,
                height=280,
            )
        else:
            st.warning(f"No text could be extracted from this {source_label}.")


# ----------------------------------------------------------------------------
# MAIN FLOW
# ----------------------------------------------------------------------------
uploaded_file = st.file_uploader(
    "Drop a PDF or image here, or click to browse",
    type=["pdf", "png", "jpg", "jpeg"],
    help="Supported formats: PDF, PNG, JPG, JPEG",
)

if uploaded_file:
    st.toast(f"Uploaded {uploaded_file.name}", icon="✅")

    try:
        # PDF
        if uploaded_file.type == "application/pdf":
            try:
                pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            except Exception:
                st.error("This PDF could not be read. It may be corrupted or password-protected. Please try another file.")
                st.stop()

            extracted_text = ""
            with st.spinner("Reading PDF..."):
                for page in pdf:
                    extracted_text += page.get_text()

            if extracted_text.strip():
                display_results(extracted_text, "PDF")
            else:
                st.warning("No text was found. This may be a scanned PDF (image-based). Try uploading it as an image instead, or use a PDF with a text layer.")

        # Image
        else:
            try:
                image = Image.open(uploaded_file)
                image.verify()  # check file isn't corrupted
                uploaded_file.seek(0)
                image = Image.open(uploaded_file)  # reopen after verify
            except Exception:
                st.error("This image could not be read. It may be corrupted or in an unsupported format. Please try another file.")
                st.stop()

            with st.expander("🖼️ Uploaded Image", expanded=True):
                st.image(image, use_container_width=True)

            with st.spinner("Extracting text using OCR..."):
                try:
                    extracted_text = pytesseract.image_to_string(image)
                except pytesseract.TesseractNotFoundError:
                    st.error("Tesseract OCR engine is not installed on this system. Please install it to enable text extraction from images.")
                    st.stop()
                except Exception as e:
                    st.error(f"OCR failed unexpectedly: {e}")
                    st.stop()

            display_results(extracted_text, "image")

    except Exception as e:
        st.error(f"Something went wrong while processing your file: {e}")

else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-emoji">📤</div>
        <div><strong>No file uploaded yet</strong></div>
        <div>Upload a PDF or image of your post to get started.</div>
    </div>
    """, unsafe_allow_html=True)
