# -*- coding: utf-8 -*-
"""
独立签单时间提取器 v10 - 修复中文日期格式 + 统一分隔符
"""
import os, re, glob

def get_pymupdf_bytes(fp):
    try:
        import pymupdf
        with pymupdf.open(fp) as doc:
            return '\n'.join(page.get_text() for page in doc).encode('utf-8', errors='replace')
    except:
        return b''

def get_plumber_bytes(fp):
    import pdfplumber
    with pdfplumber.open(fp) as pdf:
        return '\n'.join(p.extract_text() or '' for p in pdf.pages).encode('utf-8', errors='replace')

# UTF-8 labels
LABELS = [
    b'\xe7\xa1\xae\xe8\xae\xa4\xe6\x97\xb6\xe9\x97\xb4',  # 确认时间
    b'\xe6\x8a\x95\xe4\xbf\x9d\xe7\xa1\xae\xe8\xae\xa4\xe6\x97\xb6\xe9\x97\xb4',  # 投保确认时间
    b'\xe5\x87\xba\xe5\x8d\x95\xe7\xa1\xae\xe8\xae\xa4\xe6\x97\xb6\xe9\x97\xb4',  # 出单确认时间
    b'\xe5\x87\xba\xe5\x8d\x95\xe6\x97\xb6\xe9\x97\xb4',  # 出单时间
    b'\xe4\xbf\x9d\xe5\x8d\x95\xe7\xa1\xae\xe8\xae\xa4\xe6\x97\xb6\xe9\x97\xb4',  # 保单确认时间
    b'\xe4\xbf\x9d\xe5\x8d\x95\xe7\x94\x9f\xe6\x88\x90\xe6\x97\xb6\xe9\x97\xb4',  # 保单生成时间
    b'\xe7\x94\xb5\xe5\xad\x90\xe4\xbf\x9d\xe5\x8d\x95\xe7\x94\x9f\xe6\x88\x90\xe6\x97\xb6\xe9\x97\xb4',  # 电子保单生成时间
    b'\xe7\xad\xbe\xe5\x8d\x95\xe6\x97\xa5\xe6\x9c\x9f',  # 签单日期
    b'\xe7\xad\xbe\xe5\x8d\x95\xe6\x97\xb6\xe9\x97\xb4',  # 签单时间
]

# All valid date patterns (UTF-8 bytes):
# 1. YYYY-MM-DD / YYYY-M-D
# 2. YYYY.MM.DD [HH:MM:SS]
# 3. YYYY/MM/DD
# 4. YYYY年MM月DD日 (Chinese)
DATE_PAT = rb'(\d{4})([-./](\d{1,2}))\2(\d{1,2})'  # backref: \2 is same separator
# Actually simpler: just match all variations
DATE_PATTERNS = [
    rb'(\d{4})-(\d{1,2})-(\d{1,2})',   # YYYY-MM-DD
    rb'(\d{4})\.(\d{2})\.(\d{2})\s+(\d{2}:\d{2}:\d{2})',  # YYYY.MM.DD HH:MM:SS
    rb'(\d{4})\.(\d{2})\.(\d{2})',  # YYYY.MM.DD
    rb'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
    rb'(\d{4})\xe5\xb9\xb4(\d{1,2})\xe6\x9c\x88(\d{1,2})\xe6\x97\xa5',  # YYYY年MM月DD日
]

def parse_date_from_match(m):
    if len(m.groups()) == 4:  # YYYY.MM.DD HH:MM:SS
        return f"{m.group(1).decode()}-{m.group(2).decode()}-{m.group(3).decode()} {m.group(4).decode()}"
    elif len(m.groups()) == 3:
        return f"{m.group(1).decode()}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""

def find_label_in_range(src, start, end):
    for lb in LABELS:
        if lb in src[start:end]:
            return src.find(lb, start, end)
    return -1

def extract_from_src(src):
    """Date anchor + label traceback"""
    for pat in DATE_PATTERNS:
        for m in re.finditer(pat, src):
            date_str = parse_date_from_match(m)
            ds = m.start()
            ss = max(0, ds - 80)
            if find_label_in_range(src, ss, ds) >= 0:
                return date_str
    return ""

def extract_from_date_field(src):
    m = re.search(rb'Date[:\s]+(\d{4})\.(\d{2})\.(\d{2})(?:\s+(\d{2}:\d{2}:\d{2}))?', src)
    if m:
        if m.group(4):
            return f"{m.group(1).decode()}-{m.group(2).decode()}-{m.group(3).decode()} {m.group(4).decode()}"
        return f"{m.group(1).decode()}-{m.group(2).decode()}-{m.group(3).decode()}"
    return ""

def extract_sign_date(fp):
    fname = os.path.basename(fp).lower()
    pl = get_plumber_bytes(fp)
    pm = get_pymupdf_bytes(fp)

    if 'pebs' in fname:
        sd = extract_from_date_field(pm)
        if sd:
            return sd

    sd = extract_from_src(pl)
    if sd:
        return sd

    if pm:
        sd = extract_from_src(pm)
        if sd:
            return sd
        sd = extract_from_date_field(pm)
        if sd:
            return sd

    return ""

def test_all():
    pdfs = sorted(glob.glob(r"C:\Users\Administrator\Desktop\车险保单\*.pdf"))
    print('Total PDFs:', len(pdfs))
    for i, fp in enumerate(pdfs):
        sd = extract_sign_date(fp)
        fname = os.path.basename(fp)
        print('Row%d fn=%s sign=%r' % (i+1, fname[:30], sd))

if __name__ == "__main__":
    test_all()
