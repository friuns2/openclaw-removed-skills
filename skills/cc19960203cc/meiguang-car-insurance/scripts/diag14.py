# -*- coding: utf-8 -*-
import pymupdf, pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\jiaoqiang_garbled.txt"

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
    if 'FZL317' in p and '交强险' in p:
        text = get_text(p)
        lines = []
        lines.append(f"File: {p}")
        lines.append(f"Text len: {len(text)}")
        
        # Show garbled area
        for search_str in ['保险费合计', '当年应缴']:
            idx = text.find(search_str)
            if idx >= 0:
                segment = text[idx:idx+200]
                lines.append(f"\n'{search_str}' at {idx}:")
                lines.append(repr(segment[:200]))
                
                # Try various patterns
                for n_digits in [4, 3, 2]:
                    pat = r'¥\s*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])'
                    m = re.search(pat, segment)
                    if m:
                        digits = re.sub(r'[^\d]', '', m.group(1))
                        lines.append(f"  n_digits={n_digits}: MATCHED {m.group(1)!r} -> {digits}")
                    else:
                        # Show what's actually around ¥
                        idx2 = segment.find('¥')
                        if idx2 >= 0:
                            ctx = segment[idx2:idx2+30]
                            lines.append(f"  n_digits={n_digits}: NO MATCH, ¥ context: {ctx!r}")
        
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("Written to", out)
        for l in lines:
            if '¥' not in l:
                print(l)
        break
