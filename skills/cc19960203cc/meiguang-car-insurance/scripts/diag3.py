# -*- coding: utf-8 -*-
import pymupdf, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
for p in os.listdir(pdf_dir):
    if '华海' in p and '商业' in p:
        path = os.path.join(pdf_dir, p)
        text = ""
        with pymupdf.open(path) as doc:
            for page in doc:
                t = page.get_text()
                if t:
                    text += t + "\n"
        
        idx = text.find('保险费合计')
        if idx >= 0:
            segment = text[idx:idx+80]
            # Write to file
            with open(r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\premium_segment.txt", "w", encoding="utf-8") as f:
                f.write(f"File: {p}\n")
                f.write(f"Idx: {idx}\n")
                f.write(f"Segment:\n{segment}\n")
            
            # Test patterns
            patterns = [
                r"¥[\s：:]*([0-9][\s,]*[0-9]\.[0-9]{2})[\s元）)]*",
                r"保险费合计.*?¥[：:\s]*([0-9,]+\.[0-9]{2})",
            ]
            for pat in patterns:
                m = re.search(pat, segment)
                if m:
                    print(f"Pattern matched: {pat}")
                    print(f"Match: {m.group(0)}")
                    print(f"Group: {m.group(1) if m.lastindex else 'no group'}")
                else:
                    print(f"No match: {pat}")
        break
