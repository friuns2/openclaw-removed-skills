# -*- coding: utf-8 -*-
"""Check raw PDF content / encoding for 刘福强/姜祖清 PDFs"""
import pdfplumber, pymupdf, re, os

pdfs = [
    r'C:\Users\Administrator\Desktop\车险保单\鲁FS2J97-刘福强-交强险-电子保单(1).pdf',
    r'C:\Users\Administrator\Desktop\车险保单\鲁FS2J97-刘福强-商业险-电子保单(1).pdf',
    r'C:\Users\Administrator\Desktop\车险保单\鲁Y72Z98-姜祖清-交强险-电子保单(1).pdf',
    r'C:\Users\Administrator\Desktop\车险保单\鲁Y72Z98-姜祖清-商业险-电子保单(1).pdf',
]

for pdf_path in pdfs:
    basename = os.path.basename(pdf_path)
    print(f"\n===== {basename} =====")

    # Try pymupdf - extract ALL text including tables
    try:
        with pymupdf.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                print(f"\n--- pymupdf Page {i+1} ---")
                blocks = page.get_text("blocks")
                for b in blocks:
                    x0, y0, x1, y1, text, bno, btype = b
                    if text.strip():
                        print(f"  [{btype}] {repr(text[:200])}")
    except Exception as e:
        print(f"pymupdf blocks error: {e}")

    # Check raw bytes for patterns
    try:
        with open(pdf_path, 'rb') as f:
            raw = f.read()
        # Search for readable dates in raw bytes
        print("\n--- Raw byte date search ---")
        for pat in [b'2026-03', b'2026-04', b'2026-05', b'2025-', b'2027-']:
            pos = raw.find(pat)
            if pos >= 0:
                snippet = raw[pos-20:pos+50]
                print(f"  Found {pat}: context = {repr(snippet)}")
    except Exception as e:
        print(f"raw byte error: {e}")

    # Try tables extraction
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                print(f"\n--- Tables Page {i+1} ---")
                tables = page.extract_tables()
                for j, tbl in enumerate(tables):
                    print(f"  Table {j}:")
                    for row in tbl[:5]:
                        print(f"    {row}")
    except Exception as e:
        print(f"tables error: {e}")