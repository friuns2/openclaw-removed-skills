# -*- coding: utf-8 -*-
import pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
for p in os.listdir(pdf_dir):
    if '华海' in p and '商业' in p:
        path = os.path.join(pdf_dir, p)
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        
        # Test the exact regex
        pat = r"¥\s+([0-9]\s+[0-9]\s+[0-9]\s*\.\s*[0-9]\s+[0-9])\s+元"
        m = re.search(pat, text)
        print(f"Test1: {'matched' if m else 'NO MATCH'}")
        if m:
            val = re.sub(r"\s", "", m.group(1))
            print(f"  val = {val}")
        
        # Try simpler
        pat2 = r"¥\s*([0-9]+(?:\s+[0-9]+){2}\s*\.\s*(?:[0-9]+\s+[0-9]+))"
        m2 = re.search(pat2, text)
        print(f"Test2: {'matched' if m2 else 'NO MATCH'}")
        
        # Direct search for 439
        m3 = re.search(r'4\s+3\s+9', text)
        print(f"Test3 (direct 4 3 9): {'found' if m3 else 'NOT FOUND'}")
        if m3:
            print(f"  context: {repr(text[m3.start():m3.start()+50])}")
        
        break
