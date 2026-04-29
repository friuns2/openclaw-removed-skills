# -*- coding: utf-8 -*-
import io, re, pdfplumber, os, sys
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts')

PDF_DIR = r'C:\Users\Administrator\Desktop\车险保单'
OUT = r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\dadi_fee_diag.txt'

# Find FD19N9 安享B款 PDF
fname = None
for f in os.listdir(PDF_DIR):
    if 'FD19N9' in f and '安享B款' in f:
        fname = f
        break

path = os.path.join(PDF_DIR, fname)
print('using:', fname)

# pymupdf text (as used in parse_dadi_anyi)
try:
    import pymupdf
    doc = pymupdf.open(path)
    pym_text = ''
    for page in doc:
        pym_text += page.get_text() + '\n'
    # Find premium section
    idx_prem = pym_text.find('保费合计')
    if idx_prem >= 0:
        seg_prem = pym_text[idx_prem:idx_prem+200]
    else:
        seg_prem = 'NOT FOUND'
    # Find all amounts in pym_text
    amounts = re.findall(r'[￥¥]?\s*([0-9,]+\.?\d*)', pym_text)
    valid_amts = []
    for a in amounts:
        try:
            num = float(a.replace(',', ''))
            if 100 <= num < 50000 and not (2013 <= num <= 2030):
                valid_amts.append((num, a))
        except:
            pass
    pym_result = {
        'premium_section': seg_prem[:200].encode('utf-8', errors='replace')[:200],
        'all_amounts': amounts[:20],
        'valid_amounts': valid_amts
    }
except Exception as e:
    pym_result = {'error': str(e)}

# plumber text
with pdfplumber.open(path) as pdf:
    text = ''
    for p in pdf.pages:
        text += (p.extract_text() or '') + '\n'
idx_prem = text.find('保费合计')
if idx_prem >= 0:
    seg_prem = text[idx_prem:idx_prem+200]
else:
    seg_prem = 'NOT FOUND'
amounts = re.findall(r'[￥¥]?\s*([0-9,]+\.?\d*)', text)
valid_amts = []
for a in amounts:
    try:
        num = float(a.replace(',', ''))
        if 100 <= num < 50000 and not (2013 <= num <= 2030):
            valid_amts.append((num, a))
    except:
        pass

result = [
    f'PDF: {fname}',
    '=== pymupdf ===',
    f'premium section: {pym_result.get("premium_section", "")}',
    f'valid amounts: {pym_result.get("valid_amounts", [])}',
    '=== plumber ===',
    f'premium section: {seg_prem.encode("utf-8", errors="replace")[:200]}',
    f'all amounts: {amounts[:20]}',
    f'valid amounts: {valid_amts}',
]

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(str(x) for x in result))
print('done')
for r in result:
    print(r)
