# -*- coding: utf-8 -*-
import pymupdf, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\huai_bytes.txt"

def extract_raw(pdf_path):
    raw = b""
    try:
        with pymupdf.open(pdf_path) as doc:
            for page in doc:
                t = page.get_text()
                if t:
                    raw += t.encode("utf-8", errors="replace")
    except Exception as e:
        return b""
    return raw

def find_premium_bytes(raw):
    # Search for ¥ followed by spaced digits in raw UTF-8 bytes
    # Try different ¥ encodings
    for yen in [b'\xc2\xa5', b'\xef\xbf\xa5', b'\xa5']:
        idx = raw.find(yen)
        if idx >= 0:
            # Show context
            context = raw[idx:idx+40]
            print(f"  yen found at {idx}: {context}")
            # Try to extract digits after ¥
            after = raw[idx+len(yen):idx+len(yen)+30]
            # Find digit sequences
            digits = re.sub(rb"[^0-9.]", b"", after)
            print(f"  digits only: {digits}")
            try:
                val = digits.decode('ascii', errors='replace')
                # Remove dots and keep only first decimal number
                parts = val.split('.')
                if len(parts) >= 2:
                    int_part = parts[0].strip()
                    dec_part = parts[1].strip()[:2].ljust(2, '0')
                    result = f"{int_part}.{dec_part}"
                    print(f"  result: {result}")
                    return result
            except Exception as e:
                print(f"  error: {e}")
    return None

for p in os.listdir(pdf_dir):
    if 'GQ8L18' in p and '商业' in p:
        path = os.path.join(pdf_dir, p)
        raw = extract_raw(path)
        print(f"File: {p}")
        print(f"Raw bytes: {len(raw)}")
        result = find_premium_bytes(raw)
        
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"File: {p}\nRaw: {len(raw)}\nResult: {result}\n")
        break
