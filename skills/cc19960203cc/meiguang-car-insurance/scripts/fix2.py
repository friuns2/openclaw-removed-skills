# -*- coding: utf-8 -*-
with open('run_extract.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find 当年应缴 section and replace just the threshold line
search1 = "if val2 >= 100:"
replacement1 = "if 200 <= val2 <= 600:"

idx1 = content.find(search1)
print(f"Found 'if val2 >= 100:' at {idx1}")
if idx1 >= 0:
    content = content.replace(search1, replacement1, 1)
    print("Replaced threshold OK")
else:
    print("NOT FOUND - searching alternatives")
    idx2 = content.find("当年应缴")
    print(f"'当年应缴' at {idx2}")
    if idx2 >= 0:
        print("Context around 当年应缴:")
        print(repr(content[idx2:idx2+500]))

with open('run_extract.py', 'w', encoding='utf-8') as f:
    f.write(content)
