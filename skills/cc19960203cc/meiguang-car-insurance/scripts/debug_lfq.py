# -*- coding: utf-8 -*-
"""Debug script for 刘福强/姜祖清 PDFs"""
import pdfplumber, pymupdf, os, sys

pdfs = [
    r'C:\Users\Administrator\Desktop\车险保单\鲁FS2J97-刘福强-交强险-电子保单(1).pdf',
    r'C:\Users\Administrator\Desktop\车险保单\鲁FS2J97-刘福强-商业险-电子保单(1).pdf',
    r'C:\Users\Administrator\Desktop\车险保单\鲁Y72Z98-姜祖清-交强险-电子保单(1).pdf',
    r'C:\Users\Administrator\Desktop\车险保单\鲁Y72Z98-姜祖清-商业险-电子保单(1).pdf',
]

for pdf_path in pdfs:
    basename = os.path.basename(pdf_path)
    print(f"\n===== {basename} =====")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Pages: {len(pdf.pages)}")
            for i, page in enumerate(pdf.pages[:2]):
                t = page.extract_text()
                if t:
                    print(f"--- Page {i+1} (plumber, first 400 chars) ---")
                    print(t[:400])
    except Exception as e:
        print(f"plumber error: {e}")

    try:
        with pymupdf.open(pdf_path) as doc:
            for i, page in enumerate(doc[:2]):
                t = page.get_text()
                if t:
                    print(f"--- Page {i+1} (pymupdf, first 400 chars) ---")
                    print(t[:400])
    except Exception as e:
        print(f"pymupdf error: {e}")