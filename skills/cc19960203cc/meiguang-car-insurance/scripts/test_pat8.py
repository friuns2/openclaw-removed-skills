import pdfplumber, os, re
folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)
with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

# Find the insurance period line
for line in text.split('\n'):
    if '365' in line and '2026' in line and '2027' in line:
        print('LINE:', repr(line[:80]))
        
        # Check the actual bytes
        idx_365 = line.find('365')
        segment = line[idx_365:idx_365+30]
        print()
        print('Segment bytes:', segment.encode('utf-8'))
        
        # Find where 365天起，is
        # The bytes are: 365 e5 a4 a9 e8 b5 b7 ef bc 8c e4 bb 8e
        # Which is: 3 6 5 天 起 ，
        
        # Let's search for the actual bytes
        target_bytes = '365天起，'.encode('utf-8')
        print()
        print('Target bytes:', target_bytes)
        print('Found at:', segment.find(target_bytes))
        
        # Now search in the whole line
        print('Found in line:', target_bytes in line.encode('utf-8'))
        
        # Try the actual pattern
        pat = r'365天起，'
        m = re.search(pat, line)
        print()
        print('Regex 365天起，:', m)
        
        # Maybe there's a different char between 天 and 起
        # Let's look at exact bytes
        bytes_line = line.encode('utf-8')
        idx = bytes_line.find(b'365')
        print()
        print('Bytes around 365:', bytes_line[idx:idx+20])
        
        break
