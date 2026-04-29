import pdfplumber, os, re
folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)
with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

# Find the insurance period line
for line in text.split('\n'):
    if '365' in line and '2026' in line and '2027' in line:
        print('LINE:', repr(line[:90]))
        
        # Test simple patterns
        tests = [
            ('365', '365 in line'),
            ('天起', '天起 in line'),
            ('从2026', '从2026 in line'),
            ('2026年', '2026年 in line'),
            (r'365天起', 'literal 365天起'),
            (r'天起，', 'literal 天起，'),
            (r'天起，从', 'literal 天起， from'),
            (r'从', 'literal 从'),
            (r'365天起，', 'literal 365天起，'),
            (r'保险期间', 'literal 保险期间'),
            (r'365天起，\d{4}', '365天起， + digit'),
        ]
        
        for pat, desc in tests:
            m = re.search(pat, line)
            print(f'{desc}: {bool(m)}')
            if m:
                print(f'  matched: {repr(m.group(0))}')
        
        break
