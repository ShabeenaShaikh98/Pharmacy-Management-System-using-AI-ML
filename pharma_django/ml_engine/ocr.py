import pytesseract
from PIL import Image

def extract_prescription_text(image_path):
    try:
        # image open
        img = Image.open(image_path)

        # OCR extract
        text = pytesseract.image_to_string(img)

        return text

    except Exception as e:
        return f"OCR Error: {str(e)}"