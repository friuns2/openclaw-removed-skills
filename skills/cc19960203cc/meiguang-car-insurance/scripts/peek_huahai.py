# -*- coding: utf-8 -*-
import pdfplumber, os

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out_path = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\huahai_texts.txt"

pdfs = [p for p in os.listdir(pdf_dir) if p.endswith('.pdf')]
lines = []
for p in pdfs:
    if '华海' in p:
        lines.append(f'=== {p} ===')
        try:
            with pdfplumber.open(os.path.join(pdf_dir, p)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        lines.append(t)
        except Exception as e:
            lines.append(f'Error: {e}')
        lines.append('')

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f'Written to {out_path}')
