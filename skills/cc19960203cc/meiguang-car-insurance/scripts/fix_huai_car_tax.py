# -*- coding: utf-8 -*-
"""重写华海交强险garbled块 - 实收保费和车船税分开"""
import re, io

fpath = r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\run_extract.py'
with io.open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# The old block to replace (in the huai jiaoqiang section)
old_block = '''            # 2. 当年应缴（车船税）garbled
            idx2 = text.find('当年应缴')
            if idx2 >= 0:
                seg2 = text[idx2:idx2+300]
                for n_digits in [4, 3, 2]:
                    garbled2 = re.search(
                        r'¥[：:\\s]*([0-9](?:\\s*[0-9]){' + str(n_digits-1) + r'}\\s*[.．]\\s*[0-9]\\s*[0-9])\\s*元[）]?',
                        seg2
                    )
                    if garbled2:
                        digits2 = re.sub(r'[^\\d]', '', garbled2.group(1))
                        if len(digits2) >= 5:
                            val2 = float(digits2[:-2] + "." + digits2[-2:])
                            if 200 <= val2 <= 600:
                                total += val2
                                count += 1
                                break
                # 3. 中文数字兜底：在原始text中（不限seg2）搜索合计附近
                idx3 = text.find('合计（人民币大写）')
                if idx3 < 0:
                    idx3 = text.find('合计（人民币大写', idx2)  # 在当年应缴之后
                if idx3 < 0:
                    idx3 = text.find('合计（', idx2)
                if idx3 < 0:
                    idx3 = text.find('合计', idx2)
                if idx3 >= 0:
                    seg3 = text[idx3:idx3+80]
                    cn_match = re.search(r'[壹贰叁肆伍陆柒捌玖零][壹贰叁肆伍陆柒捌玖拾佰仟]*元整', seg3)
                    if cn_match:
                        tax = chinese_num(cn_match.group(0))
                        if tax > 0:
                            total += tax'''

# The new block
new_block = '''            # 2. 当年应缴（车船税）garbled — 仅记录garbled_tax，不加入total
            idx2 = text.find('当年应缴')
            garbled_tax = None
            if idx2 >= 0:
                seg2 = text[idx2:idx2+300]
                for n_digits in [4, 3, 2]:
                    garbled2 = re.search(
                        r'¥[：:\\s]*([0-9](?:\\s*[0-9]){' + str(n_digits-1) + r'}\\s*[.．]\\s*[0-9]\\s*[0-9])\\s*元[）]?',
                        seg2
                    )
                    if garbled2:
                        digits2 = re.sub(r'[^\\d]', '', garbled2.group(1))
                        if len(digits2) >= 5:
                            val2 = float(digits2[:-2] + "." + digits2[-2:])
                            garbled_tax = val2  # 不限范围，记录后break
                            break
            # 3. garbled_tax 强制覆盖车船税（parse_jiaoqiang的值可能是错的）
            if garbled_tax is not None:
                data["车船税"] = f"{garbled_tax:.2f}"'''

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    print('replaced successfully')
else:
    print('OLD BLOCK NOT FOUND - showing context')
    # Find where the block starts
    idx = content.find('# 2. 当年应缴（车船税）garbled')
    if idx >= 0:
        print(repr(content[idx:idx+300]))

with io.open(fpath, 'w', encoding='utf-8') as f:
    f.write(content)
print('done')
