# -*- coding: utf-8 -*-
import pymupdf, pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\huai_bytes.txt"

def extract_raw(pdf_path):
    """Extract raw bytes from PDF"""
    raw = b""
    try:
        with pymupdf.open(pdf_path) as doc:
            for page in doc:
                t = page.get_text()
                if t:
                    raw += t.encode("utf-8", errors="replace")
    except Exception as e:
        pass
    return raw

def find_premium_in_bytes(raw):
    """Find ¥ followed by 3 digits, decimal, 2 digits in raw bytes"""
    # ¥ in UTF-8 is \xc2\xa5
    # Look for \xc2\xa5 followed by digits with optional spaces
    m = re.search(rb"\xc2\xa5[\s]*([0-9][\s]*[0-9][\s]*[0-9][\s]*[.][\s]*[0-9][\s]*[0-9])", raw)
    if m:
        raw_match = m.group(1)
        # Extract digits and dots
        digits = re.sub(rb"[^\d.]", b"", raw_match)
        return digits.decode("ascii", errors="replace")
    return None

for p in os.listdir(pdf_dir):
    if 'GQ8L18' in p and '商业' in p:
        path = os.path.join(pdf_dir, p)
        raw = extract_raw(path)
        result = find_premium_in_bytes(raw)
        print(f"File: {p}")
        print(f"Raw bytes length: {len(raw)}")
        print(f"Premium found: {result}")
        
        # Also show bytes around ¥
        idx = raw.find(b'\xc2\xa5')
        if idx >= 0:
            print(f"¥ at byte {idx}: {raw[idx:idx+30]}")
        
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"File: {p}\n")
            f.write(f"Raw length: {len(raw)}\n")
            f.write(f"Premium: {result}\n")
            if idx >= 0:
                f.write(f"¥ context: {raw[idx:idx+50]}\n")
        break
