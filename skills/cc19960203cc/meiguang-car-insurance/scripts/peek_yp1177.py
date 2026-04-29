# -*- coding: utf-8 -*-
import io, os, sys, re
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts')

PDF_DIR = r'C:\Users\Administrator\Desktop\车险保单'
OUT = r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\yp1177_diag.txt'

# Find YP1177 团体意外险 PDF
fname = None
for f in os.listdir(PDF_DIR):
    if 'YP1177' in f and '团体意外险' in f:
        fname = f
        break

path = os.path.join(PDF_DIR, fname)
print('using:', repr(fname))

result = []
import pymupdf
doc = pymupdf.open(path)
pym_text = ''
for page in doc:
    pym_text += page.get_text() + '\n'

# Find 使用性质
for kw in ['使用性质', '使用性质', '企业', '非营业', '非营业车辆', '家庭']:
    idx = pym_text.find(kw)
    if idx >= 0:
        result.append(f'{repr(kw)} at {idx}: {repr(pym_text[max(0,idx-20):idx+60])}')

result.append(f'\n=== full text (first 1500 chars) ===')
result.append(pym_text[:1500])

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))
print('done')
