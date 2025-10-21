import re

NAME_REGEX = re.compile(r"Resident\s*Name[:\-]?\s*([A-Za-z'’\- ]+)", re.I)

def detect_docs(page_texts):
    docs = []
    current = {"pages": [], "name": None}
    for i, text in enumerate(page_texts):
        match = NAME_REGEX.search(text)
        if match:
            # start new doc if a name is found
            if current["pages"]:
                docs.append(current)
                current = {"pages": [], "name": None}
            current["name"] = match.group(1).strip()
        current["pages"].append(i)
    if current["pages"]:
        docs.append(current)
    return docs
