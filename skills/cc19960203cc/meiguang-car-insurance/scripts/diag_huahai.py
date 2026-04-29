# -*- coding: utf-8 -*-
import pdfplumber, os, sys
sys.path.insert(0, r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts")
from run_extract import route_type, parse_pdf, parse_shangye, parse_changxing, parse_jiaoqiang

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
pdfs = [p for p in os.listdir(pdf_dir) if p.endswith('.pdf')]

for p in pdfs:
    if '华海' in p and '商业' in p:
        print(f'=== {p} ===')
        path = os.path.join(pdf_dir, p)

        import pymupdf
        pymupdf_text = ""
        try:
            with pymupdf.open(path) as doc:
                for page in doc:
                    t = page.get_text()
                    if t:
                        pymupdf_text += t + "\n"
        except Exception as e:
            print(f"pymupdf error: {e}")

        plumber_text = ""
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        plumber_text += t + "\n"
        except Exception as e:
            print(f"plumber error: {e}")

        print(f"pymupdf has '华海': {'华海' in pymupdf_text}")
        print(f"plumber has '华海': {'华海' in plumber_text}")
        print(f"pymupdf length: {len(pymupdf_text)}")
        print(f"plumber length: {len(plumber_text)}")

        text = pymupdf_text if pymupdf_text else plumber_text
        rt = route_type(text)
        print(f"route_type: {rt}")
        print(f"header[:300]: {repr(text[:300])}")

        # Test parse_shangye directly
        import re
        def safe_extract(text, patterns):
            for pat in patterns:
                flags = 0
                if isinstance(pat, tuple):
                    pat, flags = pat
                try:
                    m = re.search(pat, text, flags)
                    if m:
                        val = m.group(1).strip() if m.lastindex is not None and m.lastindex >= 1 else m.group(0).strip()
                        if val:
                            return val
                except:
                    pass
            return ""

        # Test the exact pattern
        result = safe_extract(text, [
            r"¥[\s：:]*([0-9][\s,]*[0-9]\.[0-9]{2})[\s元）)]*",
        ])
        print(f"Direct pattern match: {result}")

        m = re.search(r"¥[\s：:]*([0-9][\s,]*[0-9]\.[0-9]{2})[\s元）)]*", text)
        if m:
            print(f"Regex match raw: {repr(m.group(0))}, group1: {repr(m.group(1))}")
            val = re.sub(r"\s", "", m.group(1))
            print(f"After strip spaces: {val}")

        # Show the premium area
        idx = text.find('保险费合计')
        if idx >= 0:
            print(f"Premium area: {repr(text[idx:idx+80])}")

        print()
