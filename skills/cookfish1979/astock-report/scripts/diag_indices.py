#!/usr/bin/env python3
"""诊断腾讯接口字段索引"""
import requests

codes = "sh000001,sz399001,sz399006,sh000688,sh000300,sh000905"
url = f"https://qt.gtimg.cn/q={codes}"
r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
raw = r.content.decode("gbk", errors="replace")
lines = raw.strip().split("\n")

# 只解析第一行 (上证指数) 用于调试
for line in lines[:1]:
    content = line.lstrip("v_")
    parts = content.split("~")
    print(f"总字段数: {len(parts)}")
    print()
    for i, v in enumerate(parts):
        if v and v != "0" and v != "-1" and v != "0.00" and v != "":
            print(f"  [{i:2d}] = {repr(v)}")