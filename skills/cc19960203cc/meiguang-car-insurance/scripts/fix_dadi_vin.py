# -*- coding: utf-8 -*-
"""修复大地安行如意保VIN提取：优先从"车架号："标签取，排除CZ合同号"""
import io, re

fpath = r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\run_extract.py'
with io.open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the VIN block in parse_dadi_anyang
old_vin_block = '''    # 6. 车架号
    # 优先用VIN→车型lookup表（大地安行如意行PDF的CID字体导致文本损坏，policy number "PEXD..." 也匹配17位pattern，需排除）
    vin_in_text = safe_extract(text, [r"\\b([A-HJ-NPR-Z0-9]{17})\\b"])
    if vin_in_text and not vin_in_text.upper().startswith(("PEXD", "XD", "PEBS", "PDZA", "PDAA", "AJINF")):
        data["车架号"] = vin_in_text
    else:
        data["车架号"] = ""'''

new_vin_block = '''    # 6. 车架号（优先从"车架号："标签取，PDF中为"车架号：LFV3B28R8E3082130"）
    # 排除保险合同号 CZ263...、policy no（PEXD...）等
    vin = safe_extract(text, [
        r"车架号[：:\s]*([A-HJ-NPR-Z0-9]{17})",  # 优先：车架号：LFV3B28R8E3082130
        r"\\b([A-HJ-NPR-Z0-9]{17})\\b",           # 兜底：全文17位
    ])
    if vin and not vin.upper().startswith(("PEXD", "PEBS", "PDZA", "PDAA", "AJINF", "CZ", "XD")):
        data["车架号"] = vin
    else:
        data["车架号"] = ""'''

if old_vin_block in content:
    content = content.replace(old_vin_block, new_vin_block, 1)
    print('replaced successfully')
else:
    print('OLD BLOCK NOT FOUND')
    # Try to find it
    idx = content.find('# 6. 车架号')
    print(f'VIN block starts at: {idx}')
    if idx >= 0:
        print(repr(content[idx:idx+400]))

with io.open(fpath, 'w', encoding='utf-8') as f:
    f.write(content)
print('done')
