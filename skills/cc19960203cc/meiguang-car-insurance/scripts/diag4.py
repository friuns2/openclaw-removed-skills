# -*- coding: utf-8 -*-
import pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\huai_commercial_plumber.txt"

for p in os.listdir(pdf_dir):
    if '华海' in p and '商业' in p:
        path = os.path.join(pdf_dir, p)
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"File: {p}\n")
            f.write(f"Length: {len(text)}\n")
            # Find premium section
            idx = text.find('保险费合计')
            if idx >= 0:
                f.write(f"\n保险费合计 at {idx}:\n")
                f.write(text[idx:idx+150])
                f.write("\n")
            idx2 = text.find('¥')
            if idx2 >= 0:
                f.write(f"\n¥ at {idx2}:\n")
                f.write(repr(text[max(0,idx2-20):idx2+50]))
                f.write("\n")
                # Try regex
                m = re.search(r"¥[\s：:]*([0-9][\s,]*[0-9]\.[0-9]{2})[\s元）)]*", text)
                if m:
                    val = re.sub(r"\s", "", m.group(1))
                    f.write(f"Regex matched: {m.group(0)!r} -> val={val}\n")
                else:
                    f.write("Regex NO MATCH\n")
            else:
                f.write("¥ NOT FOUND in plumber_text\n")
            
            f.write("\n--- Full text ---\n")
            f.write(text)
        
        print(f"Written to {out}")
        break
