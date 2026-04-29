import pdfplumber, os, re
folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)
with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

# Find what comes after '保险期间：365天'
idx = text.find('保险期间：365天')
print(f'保险期间：365天 at: {idx}')
print(f'After it (50 chars): {repr(text[idx:idx+50])}')
print(f'After it (50 bytes): {text[idx:idx+50].encode("utf-8")}')
print()

# Also find the line with 365
for i, line in enumerate(text.split('\n')):
    if '365' in line and '2026' in line:
        print(f'Line {i}: {repr(line[:80])}')
        line_idx = text.find(line)
        print(f'  In text at: {line_idx}')
        # What comes after 保险期间 in this line?
        idx2 = line.find('保险期间')
        print(f'  After 保险期间 (30 chars): {repr(line[idx2:idx2+30])}')
        print(f'  After 保险期间 (30 bytes): {line[idx2:idx2+30].encode("utf-8")}')
        break
