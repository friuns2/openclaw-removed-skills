# -*- coding: utf-8 -*-
import pymupdf, pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"

def get_text(p):
    path = os.path.join(pdf_dir, p)
    pymupdf_text = ""
    try:
        with pymupdf.open(path) as doc:
            for page in doc:
                t = page.get_text()
                if t:
                    pymupdf_text += t + "\n"
    except: pass
    plumber_text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    plumber_text += t + "\n"
    except: pass
    has_amt = bool(re.search(r"¥\s+[0-9]", pymupdf_text)) if pymupdf_text else False
    return plumber_text if (not has_amt and plumber_text) else (pymupdf_text if pymupdf_text else plumber_text)

for p in sorted(os.listdir(pdf_dir)):
    if 'GQ8L18' in p and '交强险' in p:
        text = get_text(p)
        print(f"File: {p}")
        print(f"Text len: {len(text)}")
        
        # Find garbled amount
        idx = text.find('保险费合计')
        if idx >= 0:
            segment = text[idx:idx+200]
            for n_digits in [4, 3, 2]:
                garbled = re.search(
                    r'¥\s*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])',
                    segment
                )
                if garbled:
                    digits = re.sub(r'[^\d]', '', garbled.group(1))
                    if len(digits) >= 5:
                        val = float(digits[:-2] + "." + digits[-2:])
                        print(f"Garbled: n_digits={n_digits}, {garbled.group(1)!r} -> {val:.2f}")
                        break
        
        # Find tax amount
        idx2 = text.find('当年应缴')
        if idx2 >= 0:
            segment2 = text[idx2:idx2+100]
            for n_digits in [4, 3, 2]:
                garbled2 = re.search(
                    r'¥\s*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])',
                    segment2
                )
                if garbled2:
                    digits2 = re.sub(r'[^\d]', '', garbled2.group(1))
                    if len(digits2) >= 5:
                        val2 = float(digits2[:-2] + "." + digits2[-2:])
                        print(f"Tax garbled: n_digits={n_digits}, {garbled2.group(1)!r} -> {val2:.2f}")
                        break
        
        # Check what \b(\d{3,4}\.\d{2})\b finds
        all_nums = re.findall(r"\b(\d{3,4}\.\d{2})\b", text)
        print(f"\nAll 3-4digit amounts: {all_nums}")
        valid = [float(n) for n in all_nums if 100 <= float(n) <= 2000]
        print(f"Valid (100-2000): {valid}")
        if len(valid) >= 2:
            print(f"Sum: {sum(valid[:2]):.2f}")
