# -*- coding: utf-8 -*-
import pymupdf, pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"

def get_texts(pdf_path):
    pymupdf_text = ""
    try:
        with pymupdf.open(pdf_path) as doc:
            for page in doc:
                t = page.get_text()
                if t:
                    pymupdf_text += t + "\n"
    except: pass
    plumber_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    plumber_text += t + "\n"
    except: pass
    return pymupdf_text, plumber_text

def huahai_premium(text):
    """For 华海 commercial insurance: extract total from fee table.
    Returns (total_str or None, debug_info)"""
    # Find "保险费合计" - garbled amount appears within ~200 chars after it
    idx = text.find('保险费合计')
    if idx >= 0:
        segment = text[idx:idx+300]
        # Clean garbled region: ¥ followed by spaced digits (¥ 4 3 9 . 0 0)
        garbled = re.search(r'¥\s*([0-9](?:\s*[0-9]){2}\s*[.．]\s*[0-9]\s*[0-9])', segment)
        if garbled:
            digits = re.sub(r'[^\d]', '', garbled.group(1))
            if len(digits) >= 5:
                # Format as XX.XX (last 2 digits = decimal)
                val = float(f"{digits[:-2]}.{digits[-2:]}")
                if 300 <= val <= 3000:
                    return f"{val:.2f}", f"garbled cleaned: {garbled.group(1)} -> {val}"
        # Otherwise scan segment for regular amounts
        all_nums = re.findall(r"\d+\.\d{2}", segment)
        valid = [float(n) for n in all_nums if 300 <= float(n) <= 3000]
        if valid:
            return f"{max(valid):.2f}", f"regular max={max(valid)}"
    # Fallback: sum the fee table items
    all_nums = re.findall(r"\b(\d{3,}\.\d{2})\b", text)
    valid = [float(n) for n in all_nums if 10 <= float(n) <= 5000]
    if len(valid) >= 3:
        # Sum the 3 largest items (commercial insurance total = sum of items)
        top3 = sorted(valid, reverse=True)[:3]
        total = sum(top3)
        return f"{total:.2f}", f"sum top3={top3} -> {total}"
    return None, "no valid numbers found"

for p in sorted(os.listdir(pdf_dir)):
    if 'GQ8L18' in p and '商业' in p:
        path = os.path.join(pdf_dir, p)
        pymupdf_t, plumber_t = get_texts(path)
        # Use plumber if pymupdf is short
        has_amt = bool(re.search(r"¥\s+[0-9]", pymupdf_t)) if pymupdf_t else False
        text = plumber_t if not has_amt and plumber_t else pymupdf_t
        result, info = huahai_premium(text)
        print(f"File: {p}")
        print(f"Using text len: {len(text)}")
        print(f"Result: {result}")
        print(f"Info: {info}")
        
        # Show lines around 本保单投保人
        tlines = text.split('\n')
        for i, line in enumerate(tlines):
            if '本保单投保人' in line:
                print(f"\n本保单投保人 at line {i}:")
                for j in range(max(0,i-3), i+1):
                    print(f"  {j}: {tlines[j]}")
                break
        break
