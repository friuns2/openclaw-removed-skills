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
        
        # Where does "2026" start?
        idx_2026 = line.find('2026')
        print('2026 starts at:', idx_2026)
        print('Chars 0-15:', [f'{c} U+{ord(c):04X}' for c in line[:15]])
        print()
        
        # Show bytes around the first date
        start = idx_2026 - 5
        segment = line[start:start+30]
        print('Segment:', repr(segment))
        print('Bytes:', segment.encode('utf-8'))
        
        # Check for nbsp
        if '\xa0' in segment:
            print('Found NBSP!')
            for i, c in enumerate(segment):
                if c == '\xa0' or ord(c) > 127:
                    print(f'  [{start+i}] {c!r} = {ord(c):#06x}')
        
        # Try the regex in parts
        # Part 1: match 保险期间：365天起，
        pat1 = r'保险期间：365天起，'
        m1 = re.search(pat1, line)
        print()
        print('Part1 (保险期间：365天起，) match:', m1)
        
        # Part 2: then digits and 年
        # The actual text is: 2026年04月22日零时起至
        # But the 年 might be preceded by \xa0
        # Let me check what comes after 2026
        idx = line.find('2026')
        after = line[idx:idx+30]
        print('After 2026:', repr(after))
        
        # Check: is there \xa0 between 2026 and 年?
        year_pos = line.find('年', idx)
        print('年 found at:', year_pos, 'char before:', repr(line[year_pos-1]) if year_pos > 0 else 'N/A', 'ord:', ord(line[year_pos-1]) if year_pos > 0 else 0)
        
        break
