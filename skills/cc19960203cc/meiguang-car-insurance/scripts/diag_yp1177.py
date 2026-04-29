# -*- coding: utf-8 -*-
import io, os, sys, re
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts')

PDF_DIR = r'C:\Users\Administrator\Desktop\车险保单'
OUT = r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\pdaa_pdza_diag.txt'

result = []
for kw, label in [('PDAA202637060000103754', 'PDAA'), ('PDZA202637060000127810', 'PDZA')]:
    fname = None
    for f in os.listdir(PDF_DIR):
        if kw in f:
            fname = f
            break
    
    if not fname:
        result.append(f'{label}: NOT FOUND in folder')
        continue
    
    path = os.path.join(PDF_DIR, fname)
    result.append(f'\n=== {label}: {fname} ===')
    result.append(f'file size: {os.path.getsize(path)}')
    
    import pymupdf
    doc = pymupdf.open(path)
    pym_text = ''
    for page in doc:
        pym_text += page.get_text() + '\n'
    
    result.append(f'text length: {len(pym_text)}')
    result.append(f'first 500: {pym_text[:500]}')
    
    # Check route_type and route_company
    from run_extract import route_type, route_company
    rt = route_type(pym_text)
    co = route_company(pym_text)
    result.append(f'route_type: {rt}, route_company: {co}')

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))
print('done')
for r in result:
    print(r)
