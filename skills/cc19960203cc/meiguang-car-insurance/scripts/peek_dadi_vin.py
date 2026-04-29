# -*- coding: utf-8 -*-
import io, os, sys, re
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts')

PDF_DIR = r'C:\Users\Administrator\Desktop\车险保单'
OUT = r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\dadi_vin_diag.txt'

# Find FD19N9 安享B款
fname = None
for f in os.listdir(PDF_DIR):
    if 'FD19N9' in f and '安享B款' in f:
        fname = f
        break

path = os.path.join(PDF_DIR, fname)
print('using:', repr(fname))

result = []

# Check pymupdf text (as used in parse_dadi_anyang)
try:
    import pymupdf
    doc = pymupdf.open(path)
    pym_text = ''
    for page in doc:
        pym_text += page.get_text() + '\n'
    
    # Find all 17-char alphanumeric strings
    all_17 = re.findall(r'\b([A-HJ-NPR-Z0-9]{17})\b', pym_text)
    result.append(f'=== pymupdf 17-char strings ===')
    result.append(f'all 17-char: {all_17}')
    
    # Find vehicle info section
    for keyword in ['车架', 'VIN', '架号', '车辆信息', '车牌号']:
        idx = pym_text.find(keyword)
        if idx >= 0:
            seg = pym_text[idx:idx+200]
            result.append(f'keyword "{keyword}" at {idx}: {seg[:200].encode("utf-8", errors="replace")[:200]}')
            break
    
    # Show first 1000 chars of pym_text
    result.append(f'=== pymupdf first 1000 ===')
    result.append(pym_text[:1000])
    
except Exception as e:
    result.append(f'pymupdf error: {e}')

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))
print('done')
