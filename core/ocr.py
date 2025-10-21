import fitz
import pytesseract
from PIL import Image
from io import BytesIO

def extract_texts(pdf_path):
    doc = fitz.open(pdf_path)
    texts = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)
        img = Image.open(BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img)
        texts.append(text)
    return texts
