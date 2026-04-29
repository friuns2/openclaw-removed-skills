# -*- coding: utf-8 -*-
import pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out_path = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\huai_commercial_text.txt"

for p in os.listdir(pdf_dir):
    if '华海' in p and '商业' in p:
        path = os.path.join(pdf_dir, p)
        print(f'=== {p} ===')

        import pymupdf
        pymupdf_text = ""
        try:
            with pymupdf.open(path) as doc:
                for page in doc:
                    t = page.get_text()
                    if t:
                        pymupdf_text += t + "\n"
        except Exception as e:
            print(f"pymupdf error: {e}")

        plumber_text = ""
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        plumber_text += t + "\n"
        except Exception as e:
            print(f"plumber error: {e}")

        text = pymupdf_text if pymupdf_text else plumber_text
        print(f"Total text length: {len(text)}")

        # Show where 保险费合计 appears
        idx = text.find('保险费合计')
        if idx >= 0:
            print(f"保险费合计 found at idx {idx}")
            print(f"Context: {repr(text[idx:idx+100])}")
        else:
            print("保险费合计 NOT FOUND in text")

        # Also check for the yuan sign
        idx2 = text.find('¥')
        if idx2 >= 0:
            print(f"¥ found at idx {idx2}")
            print(f"Context: {repr(text[idx2-20:idx2+50])}")
        else:
            print("¥ NOT FOUND")

        # Show last 500 chars
        print(f"\nLast 500 chars of text:")
        print(repr(text[-500:]))

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"=== {p} ===\n")
            f.write(f"pymupdf len={len(pymupdf_text)}, plumber len={len(plumber_text)}\n")
            f.write(text)
        print(f"\nWritten to {out_path}")
