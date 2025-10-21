import re

NAME_REGEX = re.compile(r"Resident Name[:\-_ ]*\s*([A-Za-z’‘\".,\- ]+)", re.I)

def detect_docs(page_texts):
    docs = []
    current = {"pages": [], "name": None}

    for i, text in enumerate(page_texts):
        match = NAME_REGEX.search(text)
        if match:
            name = match.group(1).strip()
            if not name:
                name = "Unknown"
            print(f"[Parser] Found name on page {i+1}: '{name}'")
            if current["pages"]:
                docs.append(current)
                current = {"pages": [], "name": None}
            current["name"] = name
        else:
            print(f"[Parser] No name detected on page {i+1}")
        current["pages"].append(i)

    if current["pages"]:
        docs.append(current)

    print(f"[Parser] Total docs detected: {len(docs)}")
    return docs
