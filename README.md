# WoundScribe

This is a very case-specific program and i doubt anyone other than me would find any use for it. I built this to streamline one of my least favorite tasks at work, scanning, splitting, and organizing PDFs from one master PDF file.

WoundScribe is a Python CLI tool for automatically processing monolithic wound note PDFs. It extracts patient names via OCR, splits the PDF into per-patient documents, and assigns them to clinics using a persistent JSON database.

---

### Features

1. **OCR extraction:** Converts PDF pages to text using Tesseract OCR.

2. **Automatic document detection:** Detects patient sections based on OCR text patterns.

3. **PDF splitting:** Generates per-patient PDF files with clean filenames.

4. **Clinic assignment:** Looks up or assigns each patient to a clinic via a JSON database.

5. **Database management:** CLI commands for listing, assigning, renaming, and removing patients.

---

### Installation

**1. Clone the repo**
```bash
git clone <repo_url>
cd woundscribe
```

**2. Create a virtual environment and activate it:**
```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```
Dependencies include:
- PyMuPDF (fitz) – PDF reading and writing
- pytesseract – OCR engine
- Pillow – Image handling
- Typer – CLI framework
- Rich – Fancy console output

**4. Make sure Tesseract OCR is installed on your system:**
- macOS (via Homebrew):
```bash
brew install tesseract
```

- Windows: download from Tesseract at UB Mannheim

---

### Usage

**Activate your environment first:**
```bash
source venv/bin/activate  # macOS / Linux
```

**Process a PDF**
```bash
python woundscribe.py process <PDF_PATH> -o <OUTPUT_DIR>
```

**Example:**
```bash
python woundscribe.py process wound.pdf -o ProcessedWounds
```

**Workflow:**
1. OCR Extraction: Converts each PDF page to text.
2. Document Parsing: Detects patient sections using regex patterns like Resident Name: <Name>.
3. Database Lookup: Normalizes names (First Last) and checks the JSON database for clinic assignments.
4. PDF Splitting: Creates individual PDFs for each patient in a folder named after the clinic.
5. Database Update: Adds any new patients to data/patient_map.json with clinic "UnknownClinic" by default.

---

### Database Commands

All commands read/write the persistent JSON database at data/patient_map.json.

**1. Assign a clinic**
```bash
python woundscribe.py assign "John Doe" -c "Valley View"
```
Assigns or updates a patient’s clinic.

**2. List all patients**
```bash
python woundscribe.py list
```
Displays a table of known patients, their assigned clinics, and the last update date.

**3. Remove a patient**
```bash
python woundscribe.py remove "John Doe"
```
Deletes a patient from the database.

**4. Rename a patient**
```bash
python woundscribe.py rename "Old Name" "New Name"
```
Renames a patient in the database and updates the last-updated timestamp.

---

### File Structure
```
woundscribe/
├─ core/
│  ├─ ocr.py          # OCR extraction functions
│  ├─ parser.py       # Detects patient boundaries from OCR text
│  ├─ splitter.py     # Splits PDF and assigns filenames & clinics
│  └─ db.py           # JSON-based clinic/patient database
├─ woundscribe.py     # CLI entrypoint
├─ data/
│  └─ patient_map.json  # Persistent patient/clinic mapping
└─ requirements.txt
```

---

### Notes & Tips
- Names are normalized from OCR strings (Last, First) to First Last for DB lookups.
- Filenames are sanitized (Last_First.pdf) to remove illegal filesystem characters.
- OCR may produce extra text (Age, Room #), so the parser trims non-name parts automatically.
- Any patient not found in the database will default to UnknownClinic.

---

### Troubleshooting
- OCR not reading text correctly: Increase DPI in ocr.extract_texts or improve PDF quality.
- Duplicate patients in DB: Ensure OCR strings are properly trimmed; clean_ocr_name handles this automatically.
- Tesseract errors: Verify the Tesseract binary is installed and in your PATH.