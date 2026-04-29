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
    if '华海' in p and '商业' in p:
        text = get_text(p)
        idx = text.find('保险费合计')
        if idx >= 0:
            segment = text[idx:idx+300]
            garbled = re.search(r'¥\s*([0-9](?:\s*[0-9]){2}\s*[.．]\s*[0-9]\s*[0-9])', segment)
            if garbled:
                digits = re.sub(r'[^\d]', '', garbled.group(1))
                if len(digits) >= 5:
                    val = float(f"{digits[:-2]}.{digits[-2:]}")
                    print(f"{p[:40]}: garbled={garbled.group(1)!r} -> digits={digits} -> {val:.2f}")
                else:
                    print(f"{p[:40]}: garbled but digits too short: {digits}")
            else:
                print(f"{p[:40]}: garbled NOT FOUND")
                # Show context
                idx2 = segment.find('¥')
                if idx2 >= 0:
                    print(f"  ¥ context: {segment[idx2:idx2+30]!r}")
