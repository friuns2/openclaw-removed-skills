# -*- coding: utf-8 -*-
with open('run_extract.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the 当年应缴 block and add Chinese number independent search
# The current block ends with "break" after garbled2
# We need to add the Chinese number search after garbled2 loop

old_ending = "                                    break\n\n                # 3. 中文数字兜底"
new_ending = "                                    break\n\n                    # 3. 中文数字独立搜索：在seg2后半段找\n                    seg_late = text[idx2+150:idx2+500]\n                    cn_m = re.search(\n                        r'[壹贰叁肆伍陆柒捌玖零][壹贰叁肆伍陆柒捌玖拾佰仟]*元整',\n                        seg_late\n                    )\n                    if cn_m:\n                        tax = chinese_num(cn_m.group(0))\n                        if tax > 0:\n                            total += tax\n\n                # 3. 中文数字兜底"

if old_ending in content:
    content = content.replace(old_ending, new_ending)
    print("Replaced OK")
    with open('run_extract.py', 'w', encoding='utf-8') as f:
        f.write(content)
else:
    print("OLD ENDING NOT FOUND")
    # Show what's near the 当年应缴 block
    idx = content.find("break\n\n                # 3.")
    print(f"'break...# 3.' at: {idx}")
    if idx > 0:
        print(repr(content[idx:idx+200]))
