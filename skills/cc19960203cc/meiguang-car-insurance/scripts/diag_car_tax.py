# -*- coding: utf-8 -*-
import re, pdfplumber, codecs

PDF_FOLDER = r'C:\Users\Administrator\Desktop\车险保单'
CAR_TAX_PAT = re.compile(r'当年应缴.*?([1-9]\d*(?:\.\d+)?)', re.DOTALL)

files = [
    '徐世林_鲁GQ8L18_华海财险_交强险_1103707000703000120260006613(2).pdf',
    '徐世林_鲁FZL317_华海财险_交强险_1103707000703000120260006354(2).pdf',
    '徐世林_鲁Y78X92_华海财险_交强险_1103707000703000120260006246(2).pdf',
]

results = []
for fname in files:
    path = f'{PDF_FOLDER}/{fname}'
    results.append(f'\n=== {fname} ===')
    with pdfplumber.open(path) as pdf:
        text = ''
        for page in pdf.pages:
            text += (page.extract_text() or '') + '\n'
    
    idx = text.find('当年应缴')
    if idx == -1:
        results.append('当年应缴 NOT FOUND')
        continue
    
    seg = text[idx:idx+300]
    results.append(f'当年应缴 section (repr): {repr(seg[:200])}')
    
    m = CAR_TAX_PAT.search(seg)
    if m:
        val = float(m.group(1))
        results.append(f'CAR_TAX_PAT match: {m.group(1)} -> {val}')
    else:
        results.append('CAR_TAX_PAT no match')

with codecs.open(r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\car_tax_diag.txt', 'w', 'utf-8') as f:
    f.write('\n'.join(results))
print('Done, written to car_tax_diag.txt')
