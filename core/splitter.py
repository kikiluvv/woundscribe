import fitz
import os
import re
from rapidfuzz import fuzz, process
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
    match = re.match(r'([A-Z][a-z]+),\s*(?:“.*?”\s*)?([A-Z][a-z]+)', raw_name)
    if match:
        last, first = match.groups()
        return f"{first} {last}"
    return re.sub(r'\b(Age|DOB|Room|#)\b.*', '', raw_name, flags=re.I).strip()

def extract_filename(raw_name: str) -> str:
    """Converts 'Last, First' → 'Last_First', removes illegal chars."""
    match = re.match(r'([A-Z][a-z]+),\s*(?:“.*?”\s*)?([A-Z][a-z]+)', raw_name)
    if match:
        last, first = match.groups()
        return sanitize_filename(f"{last}_{first}")
    clean_name = re.sub(r'\b(Age|DOB|Room|#)\b.*', '', raw_name, flags=re.I).strip()
    return sanitize_filename(clean_name)

def split_pdf(pdf_path, docs, output_dir, patient_db):
    from PyPDF2 import PdfReader, PdfWriter
    from datetime import date

    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(pdf_path)
    results = []
    fuzzy_hits = []  # 🧠 new: track fuzzy matches

    for doc in docs:
        name_raw = doc["name"]
        pages = doc["pages"]

        # normalize name
        clean_name = name_raw.replace(" Age", "").strip()
        parts = clean_name.split(", ")
        if len(parts) == 2:
            clean_name = f"{parts[1]} {parts[0]}"

        # lookup clinic
        clinic_info = patient_db.get(clean_name)
        if clinic_info:
            clinic = clinic_info.get("clinic", "UnknownClinic")
        else:
            if patient_db:
                matches = process.extract(clean_name, patient_db.keys(), scorer=fuzz.token_sort_ratio, limit=1)
                if matches and matches[0][1] > 85:
                    probable_match, score = matches[0][0], matches[0][1]
                    print(f"🤔 Fuzzy match: '{clean_name}' ≈ '{probable_match}' ({score}%)")
                    clinic = patient_db[probable_match]["clinic"]
                    fuzzy_hits.append((clean_name, probable_match, score))
                else:
                    clinic = "UnknownClinic"
            else:
                clinic = "UnknownClinic"

            patient_db[clean_name] = {
                "clinic": clinic,
                "last_updated": date.today().isoformat()
            }

        # ensure subfolder
        clinic_dir = os.path.join(output_dir, clinic)
        os.makedirs(clinic_dir, exist_ok=True)

        filename = f"{clean_name.replace(' ', '_')}.pdf"
        filepath = os.path.join(clinic_dir, filename)

        # write split PDF
        writer = PdfWriter()
        for page_idx in pages:
            writer.add_page(reader.pages[page_idx])
        with open(filepath, "wb") as f:
            writer.write(f)

        print(f"💾 Saved {filepath}")

        results.append({
            "name": clean_name,
            "clinic": clinic,
            "filename": filepath
        })

    return results, fuzzy_hits  # 🧠 return both
