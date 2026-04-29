# -*- coding: utf-8 -*-
import pymupdf, pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\y78x92_jiaoqiang.txt"

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
        lines.append("File: " + p)
        lines.append("Text len: " + str(len(text)))
        
        for search_str in ['保险费合计', '当年应缴']:
            idx = text.find(search_str)
            if idx >= 0:
                segment = text[idx:idx+300]
                yen_idx = segment.find('\xa5')  # ¥ in latin-1
                if yen_idx >= 0:
                    ctx = segment[yen_idx:yen_idx+40]
                    # repr encode to ascii
                    ctx_repr = ctx.encode('ascii', errors='replace').decode('ascii')
                    lines.append("")
                    lines.append(search_str + " segment, yen at " + str(yen_idx) + ":")
                    lines.append("  context: " + ctx_repr)
                
                # Try matching
                for n_digits in [4, 3, 2]:
                    pat = r'¥[：:\s]*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])\s*元[）]?'
                    m = re.search(pat, segment)
                    if m:
                        digits = re.sub(r'[^\d]', '', m.group(1))
                        if len(digits) >= 5:
                            val = float(digits[:-2] + "." + digits[-2:])
                            lines.append("  n_digits=" + str(n_digits) + ": MATCHED " + m.group(1).encode('ascii', errors='replace').decode('ascii') + " -> val=" + str(val))
                    else:
                        lines.append("  n_digits=" + str(n_digits) + ": NO MATCH")
        
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("Written to " + out)
        for l in lines:
            print(l)
        break
