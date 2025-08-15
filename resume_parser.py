import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import tempfile
import os

def extract_text_from_pdf(file):
    text = ''
    
    # Save the uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        # Try pdfplumber first
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
    except Exception as e:
        print(f'PDF parsing failed: {str(e)}')
    
    # If no text extracted, try OCR
    if not text.strip():
        try:
            images = convert_from_bytes(open(tmp_path, 'rb').read())
            for img in images:
                page_text = pytesseract.image_to_string(img)
                text += page_text + '\n'
        except Exception as e:
            print(f'OCR failed: {str(e)}')
    
    # Clean up the temporary file
    try:
        os.unlink(tmp_path)
    except:
        pass
    
    return text.strip()