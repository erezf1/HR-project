
from pdfminer.high_level import extract_text as pdf_extract_text
import docx

def extract_text(file_path: str):
    # This function extracts text from PDF or DOCX files based on their extension.
    text = ""
    if file_path.endswith('.pdf'):
        text = pdf_extract_text(file_path)
    elif file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text

def normalize_text(text: str):
    # This function is a placeholder for any text normalization you might need,
    # like removing special characters, standardizing date formats, etc.
    # For demonstration, it simply returns the text as is.
    return text
