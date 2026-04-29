# -*- coding: utf-8 -*-
import re, pdfplumber, io, os, sys
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts')

PDF_DIR = r'C:\Users\Administrator\Desktop\车险保单'
for f in os.listdir(PDF_DIR):
    if 'Y78X92' in f and '交强' in f:
        y78x92_pdf = os.path.join(PDF_DIR, f)
        break

with pdfplumber.open(y78x92_pdf) as pdf:
    text = ''
    for p in pdf.pages:
        text += (p.extract_text() or '') + '\n'

log = []
idx2 = text.find('当年应缴')
log.append(f'当年应缴 idx: {idx2}')

# Show the full 300 bytes from 当年应缴
seg = text[idx2:idx2+300]
log.append(f'seg (repr): {repr(seg)}')
log.append(f'seg (bytes): {seg.encode("utf-8", errors="replace")[:300]}')

# Try pymupdf_text for comparison
try:
    import pymupdf
    doc = pymupdf.open(y78x92_pdf)
    pym_text = ''
    for page in doc:
        pym_text += page.get_text() + '\n'
    idx_py = pym_text.find('当年应缴')
    if idx_py >= 0:
        seg_py = pym_text[idx_py:idx_py+200]
        log.append(f'pym_seg (bytes): {seg_py.encode("utf-8", errors="replace")[:200]}')
except:
    log.append('pymupdf not available')

# Also look at plumber raw text in the area AFTER the garbled section (around char 900+)
# The real 叁佰叁拾壹元整 should appear somewhere after char 860
search_area = text[idx2:idx2+500]
log.append(f'search_area beyond 200 bytes: {search_area[200:400].encode("utf-8", errors="replace")[:200]}')

# Try: find all numbers in the seg
nums = re.findall(r'[\d]+\.?[\d]*', seg)
log.append(f'all numbers in seg: {nums}')

# Try looking for "叁" or "三" characters
for ch in ['叁', '三', '陆', '陆', '佰', '拾']:
    idx_ch = seg.find(ch)
    if idx_ch >= 0:
        log.append(f'found {repr(ch)} at {idx_ch}: {repr(seg[max(0,idx_ch-5):idx_ch+10])}')

with io.open(r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\y78x92_full.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log))
print('done')
