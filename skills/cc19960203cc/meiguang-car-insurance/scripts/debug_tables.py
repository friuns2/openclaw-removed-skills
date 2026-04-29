# -*- coding: utf-8 -*-
"""Debug: dump all tables cell-by-cell for 浙商 PDFs"""
import pdfplumber, os

pdfs = [
    r'C:\Users\Administrator\Desktop\车险保单\鲁FS2J97-刘福强-交强险-电子保单(1).pdf',
    r'C:\Users\Administrator\Desktop\车险保单\鲁FS2J97-刘福强-商业险-电子保单(1).pdf',
    r'C:\Users\Administrator\Desktop\车险保单\鲁Y72Z98-姜祖清-交强险-电子保单(1).pdf',
    r'C:\Users\Administrator\Desktop\车险保单\鲁Y72Z98-姜祖清-商业险-电子保单(1).pdf',
]

for pdf_path in pdfs:
    basename = os.path.basename(pdf_path)
    print(f"\n{'='*60}")
    print(f"FILE: {basename}")
    print('='*60)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            for pidx, page in enumerate(pdf.pages):
                print(f"\n--- Page {pidx+1} ---")
                tables = page.extract_tables()
                for tidx, tbl in enumerate(tables):
                    print(f"  Table {tidx} ({len(tbl)} rows x {len(tbl[0]) if tbl else 0} cols):")
                    for ridx, row in enumerate(tbl):
                        # Clean cells: replace None, strip, truncate
                        clean = []
                        for cell in row:
                            s = str(cell).strip() if cell else ""
                            if len(s) > 60:
                                s = s[:60] + "..."
                            clean.append(s)
                        print(f"    Row {ridx}: {clean}")
    except Exception as e:
        print(f"Error: {e}")