# -*- coding: utf-8 -*-
import pymupdf, pdfplumber, os, re

pdf_dir = r"C:\Users\Administrator\Desktop\车险保单"
out = r"C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\y78x92_check.txt"

def chinese_num(s):
    CN = {'零':0,'一':1,'二':1,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,
          '十':10,'百':100,'佰':100,'仟':1000,'千':1000}
    for noise in ['元整','元','整','（','）']:
        s = s.replace(noise,'')
    result = cur = 0
    for ch in s:
        if ch not in CN:
            continue
        v = CN[ch]
        if v >= 10:
            result += cur * v
            cur = 0
        else:
            cur = cur * 10 + v
    return result + cur

for p in sorted(os.listdir(pdf_dir)):
    if 'Y78X92' in p and '交强险' in p:
        path = os.path.join(pdf_dir, p)
        
        pymupdf_text = ""
        try:
            with pymupdf.open(path) as doc:
                for page in doc:
                    t = page.get_text()
                    if t:
                        pymupdf_text += t + "\n"
        except: pass
        
        plumber_text = ""
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        plumber_text += t + "\n"
        except: pass
        
        has_amt = bool(re.search(r"¥\s+[0-9]", pymupdf_text)) if pymupdf_text else False
        text = plumber_text if (not has_amt and plumber_text) else (pymupdf_text if pymupdf_text else plumber_text)
        
        lines = []
        lines.append(f"File: {p}")
        lines.append(f"Text len: {len(text)}")
        lines.append(f"has_amt={has_amt}, text used: {'pymupdf' if has_amt else 'plumber'}")
        
        # 当年应缴 segment
        idx2 = text.find('当年应缴')
        if idx2 >= 0:
            seg2 = text[idx2:idx2+300]
            lines.append(f"\n当年应缴 segment (first 300 chars):")
            # Show garbled area
            for yi in ['¥', '元']:
                pos = seg2.find(yi)
                if pos >= 0:
                    ctx = repr(seg2[pos:pos+30])
                    lines.append(f"  '{yi}' at {pos}: {ctx}")
            
            # Run garbled2
            for n_digits in [4, 3, 2]:
                pat = r'¥[：:\s]*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])\s*元[）]?'
                m = re.search(pat, seg2)
                if m:
                    digits = re.sub(r'[^\d]', '', m.group(1))
                    if len(digits) >= 5:
                        val = float(digits[:-2] + "." + digits[-2:])
                        lines.append(f"  garbled2(n={n_digits}): {m.group(1)!r} -> digits={digits} -> {val} (in [200,600]: {200<=val<=600})")
                    else:
                        lines.append(f"  garbled2(n={n_digits}): MATCH but digits={digits} too short")
                else:
                    lines.append(f"  garbled2(n={n_digits}): NO MATCH")
            
            # Run Chinese number
            idx3 = seg2.find('合计')
            if idx3 >= 0:
                seg3 = seg2[idx3:idx3+80]
                cn_m = re.search(r'[壹贰叁肆伍陆柒捌玖零][壹贰叁肆伍陆柒捌玖拾佰仟]*元整', seg3)
                if cn_m:
                    cn_val = chinese_num(cn_m.group(0))
                    lines.append(f"  Chinese number: {cn_m.group(0)!r} -> {cn_val}")
                else:
                    lines.append(f"  Chinese number: NOT FOUND in {seg3[:50]!r}")
        
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        for l in lines:
            print(l.encode('ascii', errors='replace').decode('ascii'))
        break
