import fitz
import os

def split_pdf(pdf_path, docs, output_dir, patient_db):
    os.makedirs(output_dir, exist_ok=True)
    src = fitz.open(pdf_path)

    for doc in docs:
        name = doc["name"] or "Unknown"
        first, *rest = name.split()
        last = rest[-1] if rest else first
        full = f"{last}_{first}" if first else name

        from core.db import get_clinic
        clinic = get_clinic(patient_db, name)

        out_dir = os.path.join(output_dir, clinic)
        os.makedirs(out_dir, exist_ok=True)

        out_file = os.path.join(out_dir, f"{full}.pdf")
        new_pdf = fitz.open()
        for p in doc["pages"]:
            new_pdf.insert_pdf(src, from_page=p, to_page=p)
        new_pdf.save(out_file)
        new_pdf.close()

        print(f"💾 Saved {out_file}")
