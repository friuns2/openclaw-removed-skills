# -*- coding: utf-8 -*-
import pdfplumber, pymupdf, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\gq8l18_commercial_check.txt"

for p in os.listdir(pdf_dir):
    if 'GQ8L18' in p and '商业' in p:
        path = os.path.join(pdf_dir, p)
        
        # pymupdf
        pymupdf_text = ""
        with pymupdf.open(path) as doc:
            for page in doc:
                t = page.get_text()
                if t:
                    pymupdf_text += t + "\n"
        
        # plumber
        plumber_text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    plumber_text += t + "\n"
        
        lines = []
        lines.append(f"File: {p}")
        lines.append(f"pymupdf len: {len(pymupdf_text)}")
        lines.append(f"plumber len: {len(plumber_text)}")
        
        # Check which text has ¥
        has_ymark_pymupdf = "¥" in pymupdf_text
        has_ymark_plumber = "¥" in plumber_text
        lines.append(f"pymupdf has ¥: {has_ymark_pymupdf}")
        lines.append(f"plumber has ¥: {has_ymark_plumber}")
        
        text = plumber_text if (not has_ymark_pymupdf and plumber_text) else (pymupdf_text if pymupdf_text else plumber_text)
        lines.append(f"text used (len): {len(text)}")
        
        # Find premium area
        idx = text.find('保险费合计')
        if idx >= 0:
            segment = text[idx:idx+60]
            lines.append(f"\nPremium segment: {segment!r}")
        
        # Test the 3-digit regex
        pat = r"¥\s+([0-9]\s+[0-9]\s+[0-9]\s+\.\s+[0-9]\s+[0-9])\s+元"
        m = re.search(pat, text)
        if m:
            val = re.sub(r"\s", "", m.group(1))
            lines.append(f"\nRegex matched! val={val}")
        else:
            lines.append(f"\nRegex NO MATCH")
            # Try simpler
            pat2 = r"4\s+3\s+9"
            m2 = re.search(pat2, text)
            lines.append(f"  4 3 9 found: {bool(m2)}")
            # Show what's around ¥
            idx_y = text.find('¥')
            if idx_y >= 0:
                lines.append(f"  ¥ context: {text[idx_y:idx_y+30]!r}")
        
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        print(f"Written to {out}")
        print("\n".join(lines))
        break
