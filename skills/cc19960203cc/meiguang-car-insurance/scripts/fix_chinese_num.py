# -*- coding: utf-8 -*-
with open('run_extract.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the old chinese_num definition (wrong one, after CN_MAP)
old_marker = "def chinese_num(cn_str):"
CN_MAP_marker = "CN_MAP = {'零':0"

idx_cn = content.find(old_marker)
idx_cnmap = content.find(CN_MAP_marker)

if idx_cn < 0 or idx_cnmap < 0:
    print(f"NOT FOUND: cn at {idx_cn}, cnmap at {idx_cnmap}")
else:
    # Find the section to replace: from CN_MAP to end of first chinese_num function
    # The first chinese_num starts after CN_MAP and is the wrong one
    # Find where it ends (blank line or next def)
    start = idx_cnmap
    end = content.find("\ndef chinese_num", start + 10)
    if end < 0:
        end = content.find("\n# ==", start)
    if end < 0:
        end = len(content)
    
    wrong_func = content[start:end]
    print(f"Wrong function ({len(wrong_func)} chars):")
    print(wrong_func[:300])
    
    new_func = """CN_MAP = {'零':0,'一':1,'二':1,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'百':100,'佰':100,'仟':1000,'千':1000}

def chinese_num(s):
    \"\"\"Convert '叁佰陆拾' to 360. '仟壹佰' to 1100.\"\"\"
    for noise in ['元整','元','整','（','）']:
        s = s.replace(noise,'')
    result = cur = 0
    for ch in s:
        if ch not in CN_MAP:
            continue
        v = CN_MAP[ch]
        if v >= 10:
            result += cur * v
            cur = 0
        else:
            cur = cur * 10 + v
    return result + cur
"""
    
    content = content[:start] + new_func + content[end:]
    with open('run_extract.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Done!")
