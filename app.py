import streamlit as st
import pymupdf as fitz
import pytesseract
from PIL import Image
import re

st.title("Social Media Content Analyzer")

st.write("Upload your social media content and get engagement suggestions.")

uploaded_file = st.file_uploader(
    "Upload a PDF or image",
    type=["pdf", "png", "jpg", "jpeg"]
)


def analyze_content(text):
    """Rule-based engagement suggestions. No external API needed."""
    suggestions = []
    word_count = len(text.split())
    char_count = len(text)

    # Length checks
    if word_count < 15:
        suggestions.append("Your post is quite short — consider adding more context or a call-to-action to boost engagement.")
    elif word_count > 150:
        suggestions.append("Your post is fairly long for social media. Consider trimming it — shorter posts often perform better on platforms like Twitter/X or Instagram.")
    else:
        suggestions.append("Post length looks good for most platforms.")

    # Hashtags
    hashtags = re.findall(r"#\w+", text)
    if not hashtags:
        suggestions.append("No hashtags found. Adding 2-5 relevant hashtags can improve discoverability.")
    elif len(hashtags) > 10:
        suggestions.append(f"You have {len(hashtags)} hashtags — consider trimming to 5-10 for better readability.")
    else:
        suggestions.append(f"Good use of hashtags ({len(hashtags)} found).")

    # Mentions
    mentions = re.findall(r"@\w+", text)
    if mentions:
        suggestions.append(f"You're tagging {len(mentions)} account(s) — tagging relevant people/brands can boost reach.")

    # Call-to-action check
    cta_keywords = ["comment", "share", "follow", "click", "link in bio", "sign up", "learn more", "check out", "subscribe"]
    if not any(kw in text.lower() for kw in cta_keywords):
        suggestions.append("No clear call-to-action detected. Consider ending with a prompt like 'Comment below' or 'Share your thoughts'.")

    # Question / engagement hook
    if "?" not in text:
        suggestions.append("Consider adding a question to encourage replies and boost engagement.")

    # Emoji check (rough heuristic)
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F600-\U0001F64F]+"
    )
    if not emoji_pattern.search(text):
        suggestions.append("No emojis detected. A few relevant emojis can make posts feel more approachable (use sparingly).")

    # First line / hook check
    first_line = text.strip().split("\n")[0] if text.strip() else ""
    if len(first_line.split()) > 20:
        suggestions.append("Your opening line is long. A short, punchy hook in the first line grabs attention faster.")

    return suggestions, word_count, len(hashtags), len(mentions)


def display_results(extracted_text, source_label):
    st.subheader("Extracted Text")

    if extracted_text.strip():
        st.text_area(
            f"Content found in your {source_label}:",
            extracted_text,
            height=300
        )

        st.subheader("Engagement Suggestions")
        suggestions, word_count, hashtag_count, mention_count = analyze_content(extracted_text)

        col1, col2, col3 = st.columns(3)
        col1.metric("Word Count", word_count)
        col2.metric("Hashtags", hashtag_count)
        col3.metric("Mentions", mention_count)

        for s in suggestions:
            st.info(s)
    else:
        st.warning(f"No text could be extracted from this {source_label}.")


if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")

    try:
        # PDF
        if uploaded_file.type == "application/pdf":
            try:
                pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            except Exception:
                st.error("This PDF could not be read. It may be corrupted or password-protected. Please try another file.")
                st.stop()

            extracted_text = ""
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

            st.image(
                image,
                caption="Uploaded Image",
                use_container_width=True
            )

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