# -*- coding: utf-8 -*-
import pymupdf, os, re

pdf_dir = r'C:\Users\Administrator\Desktop\车险保单'
files = [
    '³FZL317-烟台-业务车险(1).pdf',
    '³FZL317-烟台-业务车险.pdf',
    '³Y78X92-Ʋ-ǿձ.pdf',
    '³FZL317-Ʋ-ǿձ(1).pdf',
]

for fn in files:
    path = os.path.join(pdf_dir, fn)
    if not os.path.exists(path):
        print(f'NOT FOUND: {fn}')
        continue
    with pymupdf.open(path) as doc:
        text = ''.join(page.get_text() or '' for page in doc)
    
    print(f'\n=== {fn} ===')
    print(f'  太平洋: {bool(re.search(r"太平洋", text))}')
    print(f'  华海: {bool(re.search(r"华海", text))}')
    print(f'  交强险: {bool(re.search(r"交强险", text))}')
    print(f'  商业险: {bool(re.search(r"商业险", text))}')
    print(f'  非车险: {bool(re.search(r"非车险", text))}')
    
    # Show all sign date related lines
    for line in text.split('\n'):
        if any(kw in line for kw in ['签单日期', '签单时间', '出单时间', '保单确认', '保单生成']):
            print(f'  SIGN: {repr(line)}')