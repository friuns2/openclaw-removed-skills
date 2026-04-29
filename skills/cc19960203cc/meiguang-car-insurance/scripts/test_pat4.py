import pdfplumber, os, re
folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)
with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

# Find the insurance period line
for line in text.split('\n'):
    if '365' in line and '2026' in line and '2027' in line:
        print('LINE:', repr(line[:100]))
        
        # Find exact position of '从' and what comes before '零时'
        idx_cong = line.find('从')
        idx_ling = line.find('零时')
        idx_zhi = line.find('至')
        
        print()
        print('从 at:', idx_cong)
        print('零时 at:', idx_ling)
        print('至 at:', idx_zhi)
        
        # Print chars around 日 to 零
        # Find 日 before 零时
        idx_ri = line.rfind('日', 0, idx_ling)
        print()
        print('日 before 零时 at:', idx_ri)
        print('Chars from 日 to 零时:', repr(line[idx_ri:idx_ling+3]))
        print('Bytes from 日 to 零时:', line[idx_ri:idx_ling+3].encode('utf-8'))
        
        # Print the exact bytes
        segment = line[idx_ri:idx_ling+3]
        print()
        print('Chars and bytes:')
        for i, c in enumerate(segment):
            print(f'  [{idx_ri+i}] {c!r} U+{ord(c):04X} bytes={ord(c):#010x}')
        
        break
