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
        print()
        
        # Test the .? pattern
        pat = r'保险期间：365天起，.?(\d{4}年\d{2}月\d{2}日)[\s\xa0]*零时起至(\d{4}年\d{2}月\d{2}日)[\s\xa0]*二十四时止'
        m = re.search(pat, line)
        print('Match with .?:', m)
        if m:
            print('Groups:', repr(m.group(1)), repr(m.group(2)))
        
        # Also test just the start part
        pat2 = r'保险期间：365天起，.?(\d{4}年)'
        m2 = re.search(pat2, line)
        print('Just start date part:', m2)
        if m2:
            print('Matched start:', repr(m2.group(0)))
            print('Group 1:', repr(m2.group(1)))
        
        break
