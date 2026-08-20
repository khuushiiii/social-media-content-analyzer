# Social Media Content Analyzer

A Streamlit web app that extracts text from uploaded PDFs or images and provides
rule-based suggestions to improve social media engagement.

## Features

- Upload a PDF or image (PNG/JPG/JPEG) via drag-and-drop or file picker
- **PDF text extraction** using PyMuPDF (`fitz`), preserving text content page by page
- **OCR text extraction** from images using Tesseract (via `pytesseract`)
- **Engagement analysis**: word count, hashtag count, mention count, and rule-based
  suggestions (length, hashtags, call-to-action, hooks, emojis, questions)
- Error handling for corrupted files, scanned/image-only PDFs, and missing OCR engine
- Loading spinner during OCR processing

## Setup

1. Clone this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install the Tesseract OCR engine (required separately from the Python package):
   - **Windows**: [UB-Mannheim Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - **Mac**: `brew install tesseract`
   - **Linux**: `sudo apt install tesseract-ocr`
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Approach (200 words)

The app is built with Streamlit for rapid UI development, avoiding the overhead of a
separate frontend/backend split within the time constraint. File upload is handled via
Streamlit's built-in `file_uploader`. For PDFs, text is extracted using PyMuPDF, which
reads the embedded text layer page by page; if no text is found, the app warns the user
the PDF may be scanned/image-based. For images, Tesseract OCR (via `pytesseract`) extracts
text after a validity check using PIL's `verify()` method to catch corrupted files early.

For the "engagement suggestions" component, I chose a rule-based analyzer instead of an
external LLM API, prioritizing reliability and zero setup cost over sophistication given
the 8-hour time budget. The analyzer checks word count (too short/long), hashtag and
mention usage, presence of a call-to-action, a question/hook, and emojis — common,
well-documented drivers of social engagement. Each check returns a specific, actionable
tip rather than a generic score.

Error handling wraps each extraction path separately (PDF parsing, image validation, OCR
execution) so failures produce clear user-facing messages instead of crashes.

## Known Limitations

- Some PDFs with stylized/letter-spaced headers (e.g., resumes made in design tools) may
  extract with extra spaces between letters — this is a font-encoding quirk, not a bug.
- OCR accuracy depends on image quality; blurry or low-resolution images may extract poorly.
- Engagement suggestions are heuristic-based, not AI-generated.