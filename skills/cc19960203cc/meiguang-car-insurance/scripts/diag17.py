# -*- coding: utf-8 -*-
import pymupdf, pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\y78x92_debug.txt"

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

lines = []
for p in sorted(os.listdir(pdf_dir)):
    if 'Y78X92' in p and '交强险' in p:
        text = get_text(p)
        lines.append(f"File: {p}")
        lines.append(f"Text len: {len(text)}")
        
        # 1. 保险费合计 garbled
        idx = text.find('保险费合计')
        if idx >= 0:
            segment = text[idx:idx+300]
            for n_digits in [4, 3, 2]:
                garbled = re.search(
                    r'¥[：:\s]*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])\s*元[）]?',
                    segment
                )
                if garbled:
                    digits = re.sub(r'[^\d]', '', garbled.group(1))
                    if len(digits) >= 5:
                        val = float(digits[:-2] + "." + digits[-2:])
                        lines.append(f"保险费合计 garbled(n={n_digits}): {garbled.group(1)!r} -> {digits} -> {val}")
        
        # 2. 当年应缴 garbled
        idx2 = text.find('当年应缴')
        if idx2 >= 0:
            seg2 = text[idx2:idx2+400]
            yen_positions = [(m.start(), m.start()+30) for m in re.finditer('¥', seg2)]
            lines.append(f"\n当年应缴 seg2 len={len(seg2)}, ¥ positions: {[(p, seg2[p:p+20]) for p, _ in yen_positions]}")
            
            for n_digits in [4, 3, 2]:
                garbled2 = re.search(
                    r'¥[：:\s]*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])\s*元[）]?',
                    seg2
                )
                if garbled2:
                    digits2 = re.sub(r'[^\d]', '', garbled2.group(1))
                    if len(digits2) >= 5:
                        val2 = float(digits2[:-2] + "." + digits2[-2:])
                        lines.append(f"当年应缴 garbled(n={n_digits}): group={garbled2.group(1)!r} -> {digits2} -> {val2}")
                    else:
                        lines.append(f"当年应缴 garbled(n={n_digits}): MATCH but digits too short: {digits2}")
                else:
                    lines.append(f"当年应缴 garbled(n={n_digits}): NO MATCH")
        
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        for l in lines:
            print(l.encode('ascii', errors='replace').decode('ascii'))
        break
