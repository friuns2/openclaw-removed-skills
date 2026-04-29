import pdfplumber, os, re
folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)

with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

# Search the FULL text (not just a line) for the insurance period pattern
# Print the full text between 600 and 700 characters
print('Text[600:700]:', repr(text[600:700]))
print()

# Search for the pattern in the full text
pat = r'保险期间：365天起，从?(\d{4}年\d{2}月\d{2}日)零时起至(\d{4}年\d{2}月\d{2}日)二十四时止'
m = re.search(pat, text)
print('Match in full text:', m)
if m:
    print('Groups:', m.group(1), m.group(2))
else:
    # Try simpler: just search for the start
    pat2 = r'保险期间：365天'
    m2 = re.search(pat2, text)
    print('保险期间：365天 in text:', m2)
    if m2:
        print('  Matched:', repr(m2.group(0)[:30]))
        start = m2.start()
        end = m2.end()
        print('  After it (30 chars):', repr(text[end:end+30]))
        print('  After it (60 bytes):', text[start:end+60].encode('utf-8'))
