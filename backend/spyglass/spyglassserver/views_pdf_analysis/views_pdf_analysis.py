import os
from django.conf import settings
import re
from datetime import datetime
import fitz  # PyMuPDF

# I have Data/research_paper/kumar2016.pdf which is a research paper 

pdf_path = '../../Data/research_paper/kumar2016.pdf'

def parse_pdf_date(raw_date: str):
    if not raw_date:
        return None
    m = re.match(r"D:(\d{4})(\d{2})(\d{2})", raw_date)
    if m:
        year, month, day = m.groups()
        try:
            return datetime(int(year), int(month), int(day)).date()
        except ValueError:
            return raw_date
    return raw_date

def extract_metadata_and_doi(pdf_path: str):
    doc = fitz.open(pdf_path)

    md = doc.metadata
    title    = md.get("title") or "—"
    author   = md.get("author") or "—"
    subject  = md.get("subject") or "—"
    raw_date = md.get("creationDate")
    creation = parse_pdf_date(raw_date)

    doi_pattern = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
    doi = None
    for page in doc:
        text = page.get_text()
        if not text:
            continue
        m = doi_pattern.search(text)
        if m:
            doi = m.group(0)
            break

    return {
        "title": title,
        "author": author,
        "subject": subject,
        "creation_date": creation or "—",
        "doi": doi or "Not found"
    }
    
# print("base dir is ==========> ", settings.BASE_DIR)
# print("pyth dir is ==========> ", settings.PYTH_DIR)

info = extract_metadata_and_doi(pdf_path)
print(f"Title:          {info['title']}")
print(f"Author:         {info['author']}")
print(f"Subject:        {info['subject']}")
print(f"Creation Date:  {info['creation_date']}")
print(f"DOI:            {info['doi']}")