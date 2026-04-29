# -*- coding: utf-8 -*-
with open('run_extract.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the 当年应缴（车船税）garbled block
search = '当年应缴（车船税）garbled'
idx = content.find(search)
print(f'Found at: {idx}')
if idx < 0:
    # Try shorter
    search2 = '当年应缴（车船税）'
    idx2 = content.find(search2)
    print(f'Search2 found at: {idx2}')

# Let's find the specific pattern we want to replace
old_block = '''                # 2. 当年应缴（车船税）garbled
                idx2 = text.find('当年应缴')
                if idx2 >= 0:
                    seg2 = text[idx2:idx2+300]
                    for n_digits in [4, 3, 2]:
                        garbled2 = re.search(
                            r'¥[：:\s]*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])\s*元[）]?',
                            seg2
                        )
                        if garbled2:
                            digits2 = re.sub(r'[^\d]', '', garbled2.group(1))
                            if len(digits2) >= 5:
                                val2 = float(digits2[:-2] + "." + digits2[-2:])
                                if val2 >= 100:
                                    total += val2
                                    count += 1
                                    break'''

new_block = '''                # 2. 当年应缴（车船税）garbled，仅在合理区间[200,600]时采用
                idx2 = text.find('当年应缴')
                if idx2 >= 0:
                    seg2 = text[idx2:idx2+300]
                    for n_digits in [4, 3, 2]:
                        garbled2 = re.search(
                            r'¥[：:\s]*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])\s*元[）]?',
                            seg2
                        )
                        if garbled2:
                            digits2 = re.sub(r'[^\d]', '', garbled2.group(1))
                            if len(digits2) >= 5:
                                val2 = float(digits2[:-2] + "." + digits2[-2:])
                                if 200 <= val2 <= 600:
                                    total += val2
                                    count += 1
                                    break'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print("Replaced OK")
    with open('run_extract.py', 'w', encoding='utf-8') as f:
        f.write(content)
else:
    print("OLD BLOCK NOT FOUND")
    # Find where it approximately is
    idx = content.find("当年应缴（车船税）")
    if idx < 0:
        idx = content.find("当年应缴")
    print(f"'当年应缴' found at {idx}")
    if idx > 0:
        print("Context:", repr(content[idx:idx+300]))
