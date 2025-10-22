import fitz
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

def process_page(page, page_number):
    # Convert PDF page to image
    pix = page.get_pixmap(dpi=300)  # Increase DPI for better OCR accuracy
    img = Image.open(BytesIO(pix.tobytes("png")))

    # Preprocess the image
    img = img.convert("L")  # Convert to grayscale
    img = img.filter(ImageFilter.SHARPEN)  # Sharpen the image
    img = ImageEnhance.Contrast(img).enhance(2.0)  # Increase contrast

    # Perform OCR
    text = pytesseract.image_to_string(img)
    print(f"[OCR] Page {page_number+1} text length: {len(text)} chars")
    return text

def extract_texts(pdf_path):
    doc = fitz.open(pdf_path)
    texts = []

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_page, page, i) for i, page in enumerate(doc)]
        for future in futures:
            texts.append(future.result())

    return texts