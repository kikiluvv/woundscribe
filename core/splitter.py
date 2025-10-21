import fitz
import os
import re
from core.db import get_clinic

def sanitize_filename(name: str) -> str:
    """Remove illegal chars and spaces → underscores for filesystem."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name.strip('_')

def clean_ocr_name(raw_name: str) -> str:
    """
    Trim trailing OCR junk (like 'Age', room numbers, etc.)
    Capture 'Last, First' pattern only.
    Returns normalized 'First Last' for DB lookup.
    """
    # match only letters for last and first
    match = re.match(r'([A-Z][a-z]+),\s*(?:“.*?”\s*)?([A-Z][a-z]+)', raw_name)
    if match:
        last, first = match.groups()
        return f"{first} {last}"  # normalized DB key
    # fallback: just remove common junk words
    return re.sub(r'\b(Age|DOB|Room|#)\b.*', '', raw_name, flags=re.I).strip()

def extract_filename(raw_name: str) -> str:
    """
    Converts 'Last, First' → 'Last_First', removes illegal chars.
    """
    match = re.match(r'([A-Z][a-z]+),\s*(?:“.*?”\s*)?([A-Z][a-z]+)', raw_name)
    if match:
        last, first = match.groups()
        return sanitize_filename(f"{last}_{first}")
    # fallback: strip junk for filename too
    clean_name = re.sub(r'\b(Age|DOB|Room|#)\b.*', '', raw_name, flags=re.I).strip()
    return sanitize_filename(clean_name)

def split_pdf(pdf_path, docs, output_dir, patient_db):
    src = fitz.open(pdf_path)
    os.makedirs(output_dir, exist_ok=True)

    for doc in docs:
        raw_name = doc.get("name") or "Unknown"
        print(f"[Splitter] Creating PDF for raw OCR name: '{raw_name}' with pages {doc['pages']}")

        # normalize name for DB lookup
        db_key = clean_ocr_name(raw_name)
        clinic = get_clinic(patient_db, db_key) or "UnknownClinic"

        # create filename for PDF
        full_filename = extract_filename(raw_name)

        out_dir = os.path.join(output_dir, clinic)
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, f"{full_filename}.pdf")

        # create PDF with only the specified pages
        new_pdf = fitz.open()
        for p in doc["pages"]:
            new_pdf.insert_pdf(src, from_page=p, to_page=p)
        new_pdf.save(out_file)
        new_pdf.close()

        print(f"💾 Saved {out_file}")
