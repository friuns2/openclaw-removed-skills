# -*- coding: utf-8 -*-
import pymupdf, pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\diag11.txt"

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
    if 'FZL317' in p and '商业' in p:
        text = get_text(p)
        idx = text.find('保险费合计')
        if idx >= 0:
            segment = text[idx:idx+200]
            lines = ["="*60, f"File: {p}", f"Text len: {len(text)}", f"Garbled check:"]
            # Try different garbled patterns
            for pat_name, pat in [
                ("4-digit", r'¥\s*([0-9](?:\s*[0-9]){3}\s*[.．]\s*[0-9]\s*[0-9])'),
                ("3-digit", r'¥\s*([0-9](?:\s*[0-9]){2}\s*[.．]\s*[0-9]\s*[0-9])'),
                ("2-digit", r'¥\s*([0-9](?:\s*[0-9]){1}\s*[.．]\s*[0-9]\s*[0-9])'),
            ]:
                m = re.search(pat, segment)
                if m:
                    digits = re.sub(r'[^\d]', '', m.group(1))
                    if len(digits) >= 5:
                        val = float(digits[:-2] + "." + digits[-2:])
                        lines.append("  %s: %r -> digits=%s -> %.2f" % (pat_name, m.group(1), digits, val))
                else:
                    lines.append(f"  {pat_name}: NOT MATCHED")
            # Show garbled region
            idx2 = segment.find('¥')
            if idx2 >= 0:
                lines.append(f"  ¥ context: {segment[idx2:idx2+50]!r}")
            lines.append(f"  Segment: {segment[:100]!r}")
            with open(out, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            for l in lines:
                print(l)
        else:
            print(f"No 保险费合计 found in {p}")
