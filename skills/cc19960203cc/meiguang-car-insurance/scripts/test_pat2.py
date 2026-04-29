import pdfplumber, os, re
folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)
with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

# Find the insurance period line
for line in text.split('\n'):
    if '365' in line and '2026' in line:
        print('LINE:', repr(line[:100]))
        
        # Print each character with its Unicode code point
        for i, c in enumerate(line[:60]):
            if ord(c) > 127 or c.isdigit():
                print(f'  [{i:2d}] {c!r} U+{ord(c):04X}')
        
        # Try to match the 365+ date part
        # The text should be: 保险期间：365天起，2026年04月22日零时起至2027年04月21日二十四时止。
        # But the chars between date digits might have \xa0
        
        # Try a simple search first
        simple_pat = r'保险期间：365天起，(\d{4}年\d{2}月\d{2}日)'
        m = re.search(simple_pat, line)
        print('Simple pattern match:', m)
        
        # What about using bytes?
        line_bytes = line.encode('utf-8')
        print()
        print('First 80 bytes:', line_bytes[:80])
        
        # Check for nbsp bytes (C2 A0 in UTF-8)
        if b'\xc2\xa0' in line_bytes:
            print('Found C2 A0 (UTF-8 encoding of U+00A0)!')
            idx = line_bytes.index(b'\xc2\xa0')
            print('At byte index:', idx)
            print('Around it:', line_bytes[idx-5:idx+10])
        
        break
