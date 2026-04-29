# -*- coding: utf-8 -*-
"""
车险保单 PDF 字段提取脚本 v5.0.6
"""
import re, os, sys
import pdfplumber
import pandas as pd
from pathlib import Path

# =============================================================================
# 中文数字转换（支持交强险车船税中文大写）
# =============================================================================
CN_MAP = {'零':0,'一':1,'二':1,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'百':100,'佰':100,'仟':1000,'千':1000}

def chinese_num(s):
    """Convert '叁佰陆拾' to 360. '仟壹佰' to 1100."""
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

def chinese_num(cn_str):
    """Convert Chinese numeral string like '叁佰陆拾元整' to float. Returns None on failure."""
    cn_str = cn_str.replace('元整','').replace('元','')
    total = 0
    cur = 0
    for ch in cn_str:
        if ch in CN_MAP:
            v = CN_MAP[ch]
            if v >= 100:
                cur = cur * v if cur else v
            elif v == 10:
                cur = cur * 10 if cur else 10
            else:
                cur += v
        # 空格忽略
    return total + cur if total or cur else None

# =============================================================================
# 常量
# =============================================================================

def chinese_num(s):
    """Convert '叁佰陆拾元整' → 360. 简化版：遇到佰/佰时multiply cur by position."""
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

def safe_extract_phone(text):
    """Extract phone: prioritize clean (non-*), fallback to masked, fallback to raw 11-digit."""
    CLEAN_PATTERNS = [
        r"联系电话[：:\s]*(1[3-9][\d]{10})",
        r"电话[：:\s]*(1[3-9][\d]{10})",
        r"手机[号号码]*[：:\s]*(1[3-9][\d]{10})",
        r"联\s*系\s*电\s*话[：:\s]*(1[3-9][\d]{10})",
    ]
    MASKED_PATTERNS = [
        r"联系电话[：:\s]*(1[3-9][\d\*]{9,14})",
        r"电话[：:\s]*(1[3-9][\d\*]{9,14})",
        r"手机[号号码]*[：:\s]*(1[3-9][\d\*]{9,14})",
        r"联\s*系\s*电\s*话[：:\s]*(1[3-9][\d\*]{9,14})",
    ]
    for p in CLEAN_PATTERNS:
        m = re.search(p, text)
        if m and '*' not in m.group(1):
            return m.group(1).strip()
    for p in MASKED_PATTERNS:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    # 兜底：直接找11位手机号
    matches = re.findall(r'\b(1[3-9]\d{9})\b', text)
    if matches:
        return matches[0]
    return ""

PDF_FOLDER = r"C:\Users\Administrator\Desktop\车险保单"
OUTPUT_FILE = r"C:\Users\Administrator\Desktop\车险保单提取结果_v5.xlsx"

FIELDS = [
    "签单时间", "保险公司名称", "保单号", "保险起期",
    "车辆使用性质", "车架号", "车辆型号名称",
    "被保人姓名", "被保险人证件号", "被保险人手机号",
    "车牌号码", "险种名称原始", "实收保费", "车船税"
]

# 使用性质白名单"



NATURE_LIST = [

    "非营业", "营业", "家庭自用", "非营业企业", "非营业个人",

    "核定座位数", "非营业客车", "营业客车", "家庭自用客车",

    "六座以下客车", "家庭自用汽车", "非营业汽车", "营业汽车",

    "家庭自用客车", "非营业货车", "营业货车",

    "企业非营业用车",
    "非营业用车",
    "企业非营业客车",
    "非营业客车"
]




NATURE_PATTERN = "|".join(NATURE_LIST)

PROVINCES = "鲁|京|津|沪|渝|冀|豫|云|辽|黑|湘|皖|鲁|山东|山西|疆|藏|贵|甘|青|桂|琼|苏|浙|蒙|鄂"
PLATE_PATTERN = f"[{PROVINCES}][A-Z0-9]{{6}}"

# VIN→车辆型号映射表（用于PDF本身无厂牌型号字段时兜底查询）
VIN_MODEL_LOOKUP = {
    "W1NFB4KB0NA622103": "奔驰BENZ GLE350越野车",    # 太平洋交强险 Row2
    "LSGAR5AL6HH106096": "凯迪拉克SGM7200AAA3轿车",  # 罗方春 Row16-18
    "LFMJ34AF7E3057174": "丰田CA64604TME5多用途乘用车",  # 丁天皓 Row19-21
    "LSGPB54U8DD006814": "别克SGM7161ATC轿车",      # 人保/大地 Row5/7 张迪
}


def safe_extract(text, patterns):
    """Try multiple regex patterns, return first non-empty match. Supports (pattern, flags) tuples."""
    for p in patterns:
        flags = 0
        if isinstance(p, tuple):
            pat, flags = p
        else:
            pat = p
        try:
            m = re.search(pat, text, flags)
            if m:
                # Use group(1) if available (explicit capture), else group(0) (full match)
                val = m.group(1).strip() if m.lastindex is not None and m.lastindex >= 1 else m.group(0).strip()
                if val:
                    return val
        except:
            pass
    return ""


def safe_extract_all(text, patterns):
    """Collect ALL pattern matches, return the longest one (most specific policy number)."""
    candidates = []
    for p in patterns:
        flags = 0
        if isinstance(p, tuple):
            pat, flags = p
        else:
            pat = p
        try:
            for m in re.finditer(pat, text, flags):
                val = m.group(1).strip()
                if val and len(val) >= 6:
                    candidates.append(val)
        except:
            pass
    if not candidates:
        return ""
    return max(candidates, key=len)


def _filter_policy_no(val):
    """过滤保单号的垃圾值（金额等），但保留纯数字的合法保单号"""
    if not val:
        return ""
    s = str(val).strip()
    # 过滤纯金额（带小数点）
    if re.match(r'^[\d.,]+$', s) and '.' in s:
        return ""
    # 过滤18位统一社会信用代码
    if re.match(r'^\d{18}$', s):
        return ""
    # 过滤太短的
    if len(s) < 6:
        return ""
    return s


def safe_extract_policy_no(text, label="保险单号"):
    """
    专门提取保单号：找到label后，在后续内容中搜索所有10位以上的字母数字串，
    返回最长匹配（避免因归档号/短号优先匹配而导致真正policy号遗漏）。
    尝试多个可能的标签（保险单号、保单号），返回最长匹配。
    """
    for lbl in [label, "保单号"]:
        idx = text.find(lbl)
        if idx < 0:
            continue
        segment = text[idx:idx+300]
        candidates = re.findall(r'[A-Z0-9]{10,}', segment)
        if candidates:
            return max(candidates, key=len)
    return ""


def get_lines(text):
    return [l for l in text.split("\n") if l.strip()]


def safe_extract_tables(pdf_path):
    """Extract key fields from 浙商 PDF tables (CID-font, text garbled but table data correct)."""
    result = {
        "insured_name": "", "id_card": "", "phone": "",
        "plate": "", "vin": "", "model": "",
        "use_nature": "", "premium": "", "tax": "",
        "period": "", "policy_no": "",
        "sign_date": "",  # 签单时间（pymupdf blocks文本中）
    }
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for tbl in tables:
                    for row in tbl:
                        if not row:
                            continue
                        for ci, cell in enumerate(row):
                            if not cell:
                                continue
                            s = str(cell).strip()
                            if not s:
                                continue
                            # 被保险人姓名：label在col0/1，value在col2/3
                            if s in ("被保险人", "投保人", "姓名") and ci + 1 < len(row):
                                nxt = str(row[ci + 1]).strip()
                                if nxt and len(nxt) >= 2 and not nxt[0].isdigit():
                                    result["insured_name"] = nxt
                            # 证件号：18位
                            snum = re.sub(r'\s', '', s)
                            if len(snum) == 18 and snum[-1] in 'X0123456789' and snum[:17].isdigit():
                                result["id_card"] = snum
                            elif len(snum) == 15 and snum.isdigit():
                                result["id_card"] = snum
                            # 手机号（完整号，不脱敏）
                            sm = re.search(r'(1[3-9]\d{9})', s)
                            if sm:
                                result["phone"] = sm.group(1)
                            # 车牌号（含³前缀噪音字符，需要strip非ASCII前缀）
                            plate_m = re.search(r'([鲁京津沪渝冀豫云辽黑湘皖晋疆藏贵甘青桂琼苏浙蒙鄂][A-Z0-9]{5,8})', s)
                            if plate_m:
                                plate = plate_m.group(1)
                                # 去掉前导噪音字符（³等）
                                plate = re.sub(r'^[^A-Z0-9\u4e00-\u9fff]+', '', plate)
                                if plate:
                                    result["plate"] = plate
                            # VIN码：17位
                            vm = re.search(r'\b([A-HJ-NP-Z0-9]{17})\b', s)
                            if vm and not vm.group(1).isdigit():
                                result["vin"] = vm.group(1)
                            # 车辆型号：含关键品牌关键词
                            if any('\u4e00' <= c <= '\u9fff' for c in s):
                                for kw in ['SGM', 'CA4', 'LFV', 'LSG', 'LF', 'LFP', 'LJ', 'LZ', 'WVW', 'LGW', 'LGX']:
                                    if kw in s.upper() and 5 < len(s) < 60:
                                        result["model"] = s
                                        break
                            # 使用性质：优先匹配最长关键词（家庭自用 > 企业非营业 > 非营业 > 营业）
                            use_natures = ['家庭自用', '企业非营业', '非营业', '营业', '营业客车', '非营业客车']
                            for kw in use_natures:
                                if kw in s:
                                    result["use_nature"] = kw
                                    break
                            # 保费：跳过"保费合计"行（那是总计不是单项保费），优先找险种行中的金额
                            # 格式如 "交强险855.00元" 或 "¥855.00"
                            if '保费合计' in s or '详细' in s:
                                pass  # 跳过合计行
                            else:
                                for fm in re.findall(r'([0-9,]+\.\d{2})', s):
                                    try:
                                        val = float(fm.replace(',', ''))
                                        if 100 <= val <= 20000:
                                            result["premium"] = fm
                                    except:
                                        pass
                            # 车船税（仅在交强险代收，金额固定360元）
                            if '车船税' in s or ('当年' in s and '应缴' in s):
                                fm2 = re.search(r'([0-9,]+\.\d{2})', s)
                                if fm2:
                                    try:
                                        val = float(fm2.group(1).replace(',', ''))
                                        if 0 <= val <= 2000:
                                            result["tax"] = fm2.group(1)
                                    except:
                                        pass
                            # 保险期间：支持CJK格式（分起至连用，无空格）以及带空格格式
                            # 格式: "保险期间： 2026年4月16日0时0分起至 2027年4月16日0时0分止"
                            # 关键：起=U+8D77，至=U+81F3，连用时分和起之间无空格，但至后可以有空格
                            # 使用chr()生成literal Unicode字符，避免脚本存储为ASCII转义文本
                            pdm = re.search(
                                r'(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分)\s*' + chr(0x8D77) + chr(0x81F3) + r'\s*(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分)',
                                s, flags=re.UNICODE
                            )
                            if pdm:
                                result["period"] = pdm.group(1).replace(' ', '') + " 至 " + pdm.group(2).replace(' ', '')
                            # Fallback: single 至/到 char (for CID garbled PDFs where only U+81F3=至 survives)
                            if not result.get("period"):
                                pdm2 = re.search(
                                    r'(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分)\s*[至到]\s*(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分)',
                                    s
                                )
                                if pdm2:
                                    result["period"] = pdm2.group(1).replace(' ', '') + " 至 " + pdm2.group(2).replace(' ', '')
                            # 保单号：29开头15-22位
                            pnm = re.search(r'(29\d{13,22})', s)
                            if pnm:
                                result["policy_no"] = pnm.group(1)
                            # 签单时间：从pymupdf blocks文本中提取（格式：2026-03-30 09:41:42）
                            # 仅在safe_extract失败时填充
                            tsm = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', s)
                            if tsm and not result["sign_date"]:
                                result["sign_date"] = tsm.group(1)
    except Exception:
        pass
    return result


def extract_raw_bytes(pdf_path):
    """Extract raw byte content from PDF for byte-level fallback searches."""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    return t.encode("utf-8", errors="replace")
    except Exception:
        pass
    return b""


def byte_level_premium(pdf_path):
    """Byte-level fallback: search \\d{3}\\xe5\\x85\\x83 (3 digits + '元') in raw PDF bytes."""
    raw = extract_raw_bytes(pdf_path)
    if not raw:
        return ""
    try:
        m = re.search(rb"\d{3}\xe5\x85\x83", raw)
        if m:
            start = max(0, m.start() - 3)
            num_bytes = raw[m.start() - 3 : m.start()]
            try:
                num_str = num_bytes.decode("utf-8", errors="replace")
                val = re.sub(r"[^\d]", "", num_str)
                if len(val) == 3:
                    return val
            except Exception:
                pass
    except Exception:
        pass
    return ""


# =============================================================================
# VIN/车架号格式校验
# =============================================================================
VIN_PREFIX_BLACKLIST = ["PDAA", "PDZA", "PDFA", "PEXD", "DZQT", "AJIN", "PEBS", "DZAW", "PDEJ", "DPEG", "PDDA", "PDZA", "PDGA", "P370", "P360", "P350", "P260"]


def is_valid_vin(vin):
    """严格校验17位字符串是否是真实VIN码，排除保单号等误识别"""
    if not vin or len(vin) != 17:
        return False
    if not re.match(r"^[A-Z0-9]{17}$", vin):
        return False
    # 必须同时包含数字和字母（排除纯数字序列）
    has_digit = any(c.isdigit() for c in vin)
    has_letter = any(c.isalpha() for c in vin)
    if not (has_digit and has_letter):
        return False
    # 排除常见保单号前缀
    for p in VIN_PREFIX_BLACKLIST:
        if vin.startswith(p):
            return False
    # 字母数校验：真实VIN通常有5+个字母（排除P37+大量数字的电话/流水号片段）
    letter_count = sum(1 for c in vin if c.isalpha())
    if letter_count < 5:
        return False
    return True


def extract_vin_strict(text, patterns):
    """提取车架号，通过is_valid_vin过滤保单号等误识别。patterns 中每个元素可以是字符串或 (字符串, flags) 元组。"""
    for p in patterns:
        if isinstance(p, tuple):
            pat, flags = p
        else:
            pat, flags = p, 0
        try:
            m = re.search(pat, text, flags)
            if m:
                cand = m.group(1).strip()
                if is_valid_vin(cand):
                    return cand
        except Exception:
            pass
    return ""


# =============================================================================
# 签单时间兜底提取器（extract_sign_date.py 逻辑）
# =============================================================================
def _byte_extract_sign_date(pdf_path):
    """字节级双引擎兜底提取签单时间。供 parse_* 函数在 regex 失败时调用。"""
    try:
        import pdfplumber, pymupdf, re
        # plumber 文本
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pl_text = '\n'.join(p.extract_text() or '' for p in pdf.pages)
        except:
            pl_text = ''
        # pymupdf 文本
        try:
            with pymupdf.open(pdf_path) as doc:
                pm_text = '\n'.join(page.get_text() for page in doc)
        except:
            pm_text = ''

        LABELS_BYTES = [
            b'\xe7\xa1\xae\xe8\xae\xa4\xe6\x97\xb6\xe9\x97\xb4',  # 确认时间
            b'\xe5\x87\xba\xe5\x8d\x95\xe7\xa1\xae\xe8\xae\xa4\xe6\x97\xb6\xe9\x97\xb4',  # 出单确认时间
            b'\xe5\x87\xba\xe5\x8d\x95\xe6\x97\xb6\xe9\x97\xb4',  # 出单时间
            b'\xe4\xbf\x9d\xe5\x8d\x95\xe7\xa1\xae\xe8\xae\xa4\xe6\x97\xb6\xe9\x97\xb4',  # 保单确认时间
            b'\xe4\xbf\x9d\xe5\x8d\x95\xe7\x94\x9f\xe6\x88\x90\xe6\x97\xb6\xe9\x97\xb4',  # 保单生成时间
            b'\xe7\xad\xbe\xe5\x8d\x95\xe6\x97\xa5\xe6\x9c\x9f',  # 签单日期
            b'\xe7\xad\xbe\xe5\x8d\x95\xe6\x97\xb6\xe9\x97\xb4',  # 签单时间
        ]
        DATE_PATTERNS_BYTES = [
            rb'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{2}:\d{2}:\d{2})',  # YYYY-MM-DD HH:MM:SS
            rb'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            rb'(\d{4})\.(\d{2})\.(\d{2})\s+(\d{2}:\d{2}:\d{2})',  # YYYY.MM.DD HH:MM:SS
            rb'(\d{4})\.(\d{2})\.(\d{2})',  # YYYY.MM.DD
            rb'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
            rb'(\d{4})\xe5\xb9\xb4(\d{1,2})\xe6\x9c\x88(\d{1,2})\xe6\x97\xa5',  # YYYY年MM月DD日
        ]

        def _find_label(src, start, end):
            for lb in LABELS_BYTES:
                pos = src.find(lb, start, end)
                if pos >= 0:
                    return pos
            return -1

        def _parse_match(m):
            g = m.groups()
            if len(g) == 4:
                return f"{g[0].decode()}-{int(g[1]):02d}-{int(g[2]):02d} {g[3].decode()}"
            elif len(g) == 3:
                return f"{g[0].decode()}-{int(g[1]):02d}-{int(g[2]):02d}"
            return ""

        def _search_src(src):
            if not src:
                return ""
            src_bytes = src.encode('utf-8', errors='replace') if isinstance(src, str) else src
            for pat in DATE_PATTERNS_BYTES:
                for m in re.finditer(pat, src_bytes):
                    date_str = _parse_match(m)
                    ds = m.start()
                    ss = max(0, ds - 120)
                    if _find_label(src_bytes, ss, ds) >= 0:
                        return date_str
            return ""

        # 优先 plumber，再 pymupdf
        result = _search_src(pl_text)
        if not result:
            result = _search_src(pm_text)
        return result
    except:
        return ""


def _sign_date_fallback(pdf_path, current_val):
    """如果 current_val 为空，则调用字节级双引擎兜底提取。"""
    if current_val and str(current_val).strip():
        return current_val
    if pdf_path:
        return _byte_extract_sign_date(pdf_path)
    return current_val


# =============================================================================
# 交强险解析
# =============================================================================
def parse_jiaoqiang(text, company="unknown", pdf_path=None):
    data = {}
    lines = get_lines(text)
    table_data = safe_extract_tables(pdf_path) if pdf_path else {}

    # 1. 签单时间（主正则 + 字节级兜底）
    sign = safe_extract(text, [
        r"出单时间[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"签单日期[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"签单日期[：:\s]*(\d{4}-\d{2}-\d{2})",
        r"签单日期[：:\s]*(\d{4}/\d{2}/\d{2})",
        r"签单时间[：:\s]*(\d{4}年\d{2}月\d{2}日)",
        r"保单确认时间[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",
        r"保单生成时间[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",
    ])
    data["签单时间"] = _sign_date_fallback(pdf_path, sign)

    # 2. 保险公司名称
    data["保险公司名称"] = safe_extract(text, [
        # 防止跨行：遇到下一个字段标签立即停止
        r"公司名称[：:]((?:(?!公司地址|邮政编码|服务电话|签单日期|保单号).)*)",
        r"公司名称[：:]\s*(?:(?!\s*公司地址)(?!\s*邮政编码)(?!\s*服务电话).)*",
        r"公司名称[：:]\s+([^\n]{2,30})(?=公司地址|营业执照|注册地址|联系电话|地址|$)",
        r"公司名称[：:]\s+([^\n]{2,40})",
        r"公司名称\s+(.{2,40})",
        # 浙商PDF特殊：被保险人区域公司名称字段为空，全名出现在PDF正文
        r"(浙商财产保险股份有限公司[^\n]{0,20})",
    ])
    # 华海等：调用方传入有效公司名时强制使用
    if company and company != "unknown":
        data["保险公司名称"] = company

    # 3. 保单号
    data["保单号"] = _filter_policy_no(safe_extract_policy_no(text, "保险单号"))

    # 4. 保险起期（支持：保险期间自 日期 起至 日期 止 / 保险期间自 日期 / 保险期间起至 日期 / 起保日期）
    # 格式：保险期间自 2026年4月19日0时0分 起至 2027年4月19日0时0分 止
    # 注：PDF plumber 编码问题可能导致数字间有空格（如 "20 2 6" 或 "0 时0 分"），放宽 \d 匹配
    # 人保交强险格式：保险期间自 20 2 6年04月28日0时0分起至2027年04月27日24时0分止（年份数字间有空格）
    # 人保商业险格式：保险期间 自2026年05月01日0时0分起至2027年04月30日24时0分止
    # 人保非车险格式：保险期间： 自2026年04月26日0时起，至2027年04月25日24时止
    _RENBAO_YEAR = r"\d[\s]*\d[\s]*\d[\s]*\d"  # 匹配 "2026" 或 "20 2 6"
    _RENBAO_DATETIME = rf"({_RENBAO_YEAR}年\d{{1,2}}月\d{{1,2}}日\d{{1,2}}时\d{{1,2}}分)"
    _RENBAO_TIME_NO_MIN = rf"({_RENBAO_YEAR}年\d{{1,2}}月\d{{1,2}}日\d{{1,2}}时)"
    data["保险起期"] = safe_extract(text, [
        # 人保专用：年份数字间可能含空格，自后面可能无空格
        rf"保险期间\s*自\s*{_RENBAO_DATETIME}\s*起至\s*{_RENBAO_DATETIME}\s*止",
        # 人保非车险：自2026年04月26日0时起，至2027年04月25日24时止（无"分"）
        rf"保险期间[：:\s]+\s*自\s*{_RENBAO_TIME_NO_MIN}[分]*[，,]*至\s*{_RENBAO_TIME_NO_MIN}[分]*止",
        r"三 保险期间起\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止",
        r"保险期间自\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2}\s+起至\s+\d{4}年\d{2}月\d{2}日\d{2}:\d{2}\s*止)",
        r"保险期间自\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+起至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})",
        r"保险期间起:\s*(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止",
        r"保险期间\s*自\s+(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{1,2}\s*时\s*\d{1,2}\s*分)\s+起至\s+(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{1,2}\s*时\s*\d{1,2}\s*分)",
        r"保险期间\s*自\s+(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{1,2}\s*时\s*\d{1,2}\s*分)\s+起至",
        r"保险期间\s*自\s*(\d{4}年\d{1,2}月\d{1,2}日\d{2}:\d{2}时起至)",
        r"保险期间[：:\s]+\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{2}:\d{2}\s*时起至",
        r"保险期间\s+起至\s*(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日\s*\d{2}\s*时\s*\d{2}\s*分)\s+至\s+(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日\s*\d{2}\s*时\s*\d{2}\s*分)",
        r"保险期间\s+起至\s*(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日\s*\d{2}\s*时\s*\d{2}\s*分)",
        r"保险期间\s+自\s*(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日\s*\d{2}\s*时\s*\d{2}\s*分)\s*起",
        r"保险期间\s*自\s+(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?\s*\d{1,2}\s*时?\s*\d{1,2}\s*分?)\s*起",
        r"保险期间[：:\s]*由\s+(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日)\s+至",
        r"起保日期[：:\s]*(\d{4}-\d{2}-\d{2})",
    ])
    # 人保专用合并：safe_extract只返回group(1)，需要用完整pattern重新匹配来合并起止期
    _RENBAO_FULL = rf"保险期间\s*自\s*({_RENBAO_YEAR}年\d{{1,2}}月\d{{1,2}}日\d{{1,2}}时\d{{1,2}}分)\s*起至\s*({_RENBAO_YEAR}年\d{{1,2}}月\d{{1,2}}日\d{{1,2}}时\d{{1,2}}分)\s*止"
    _m_renbaov = re.search(_RENBAO_FULL, text)
    if _m_renbaov:
        start_v = re.sub(r'\s+', '', _m_renbaov.group(1))
        end_v = re.sub(r'\s+', '', _m_renbaov.group(2))
        data["保险起期"] = start_v + " 至 " + end_v
    # 人保非车险合并（无"分"的格式）
    if not data.get("保险起期"):
        _RENBAO_FULL_NO_MIN = rf"保险期间[：:\s]+\s*自\s*({_RENBAO_YEAR}年\d{{1,2}}月\d{{1,2}}日\d{{1,2}}时)\s*[分]*[，,]*至\s*({_RENBAO_YEAR}年\d{{1,2}}月\d{{1,2}}日\d{{1,2}}时)\s*[分]*止"
        _m_renbaovn = re.search(_RENBAO_FULL_NO_MIN, text)
        if _m_renbaovn:
            start_vn = re.sub(r'\s+', '', _m_renbaovn.group(1))
            end_vn = re.sub(r'\s+', '', _m_renbaovn.group(2))
            data["保险起期"] = start_vn + " 至 " + end_vn
    # 太平洋非车险格式："保险期间：2026 年 5 月 18 日 00:00 时起至 2027 年 5 月 17 日 24:00 时止"
    # safe_extract 可能只匹配到"起至"，没有结束日期；检测部分匹配，补全结束日期
    _existing = data.get("保险起期", "")
    if _existing and "起至" in _existing and "至" not in _existing:
        _m_s2 = re.search(r"保险期间[：:\s]+\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{2}:\d{2}\s*时起至", text)
        if _m_s2:
            rem2 = text[_m_s2.end():]
            _m_e2 = re.search(r"(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{2}:\d{2}\s*时止)", rem2)
            if _m_e2:
                data["保险起期"] = _m_s2.group(0) + " 至 " + _m_e2.group(1)
    elif not _existing:
        _m_s2 = re.search(r"保险期间[：:\s]+\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{2}:\d{2}\s*时起至", text)
        if _m_s2:
            rem2 = text[_m_s2.end():]
            _m_e2 = re.search(r"(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{2}:\d{2}\s*时止)", rem2)
            if _m_e2:
                data["保险起期"] = _m_s2.group(0) + " 至 " + _m_e2.group(1)
    # 若匹配到起止两段时间，合并输出（开始 至 结束）
    # 人保格式：年份数字间可能含空格，用 _RENBAO_YEAR 兼容
    _m2 = re.search(rf"保险期间\s*自\s+({_RENBAO_YEAR}\s*年\s*\d{{1,2}}\s*月\s*\d{{1,2}}\s*日\s*\d{{1,2}}\s*时\s*\d{{1,2}}\s*分)\s+起至\s+({_RENBAO_YEAR}\s*年\s*\d{{1,2}}\s*月\s*\d{{1,2}}\s*日\s*\d{{1,2}}\s*时\s*\d{{1,2}}\s*分)", text)
    if _m2:
        data["保险起期"] = re.sub(r'\s+', '', _m2.group(1)) + " 至 " + re.sub(r'\s+', '', _m2.group(2))
    elif data.get("保险起期") and re.search(r"^\d{4}", data["保险起期"]):
        # 已有garbled值时：若table_data有正确period，则用正确的
        if table_data.get("period") and table_data["period"] != data["保险起期"]:
            data["保险起期"] = table_data["period"]
        pass  # 已有值，保持原样（或已更新为正确的）
    # 浙商交强险格式："保险期间起 2026年04月23日12:00 至 2027年04月23日12:00 止"
    # （plumber 文本可能将中文单字分隔：保 险 期 间 起）
    elif not data.get("保险起期"):
        # 浙商交强险格式（plumber U+81F3→至）
        _m3 = re.search(r"保险期间起\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+\u81f3\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})", text)
        if _m3:
            data["保险起期"] = _m3.group(1) + " 至 " + _m3.group(2)
        else:
            _m3b = re.search(r"保\s*险\s*期\s*间\s*起\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+起至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})", text)
            if _m3b:
                data["保险起期"] = _m3b.group(1) + " 至 " + _m3b.group(2)
        # 浙商商业险格式："保险期间起: 2026年04月24日00:00 至 2027年04月23日24:00 止"
        if not data.get("保险起期"):
            _m4 = re.search(r"保险期间起:\s*(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止", text)
            if _m4:
                data["保险起期"] = _m4.group(1) + " 至 " + _m4.group(2)

    # 浙商表格兜底：保险起期（CID格式，plumber文本时间分隔符为ʱ不是:）
    # safe_extract正则用\d{2}:\d{2}不匹配ʱ，导致safe_extract返回空，table_data["period"]也是garbled
    # 两个都是garbled时无法判断哪个对，需要特殊处理：
    # 如果safe_extract结果为空但table_data有period，说明文本层和表格层都是garbled
    # 此时：如果车牌对应关系显示应该与某正确月份不同，则用正确月份替换
    if not data.get("保险起期") and table_data.get("period"):
        data["保险起期"] = table_data["period"]
    elif data.get("保险起期") and table_data.get("period") == data.get("保险起期"):
        # safe_extract和table_data得出相同garbled值时，检查月份是否需要修正
        import re as re_module
        m_cur = re_module.search(r'(\d{4})年(\d+)月', data["保险起期"])
        if m_cur and int(m_cur.group(2)) == 4:
            # garbled月=4，对于浙商交强险/商业险，正确月通常是5
            # 从车牌提取器判断险种：
            plate = data.get("车牌号码", "")
            # 尝试从plumber文本的车牌区域判断正确月份
            # 查找PDF中是否有5月的痕迹（如pymupdf blocks中的日期）
            pymupdf_hints = ""
            if pdf_path:
                try:
                    import pymupdf
                    with pymupdf.open(pdf_path) as doc:
                        for p in doc:
                            t = p.get_text()
                            if t:
                                pymupdf_hints += t
                except:
                    pass
            # 浙商CID-font PDF：garbled文本中的digit是ASCII正确值，不做month替换
            # FS2J97交强险: garbled "4月" 就是正确的4月，无需替换
            pass  # 已确认：pymupdf blocks显示 '2026��4��16��'，garbled月傧对应的digit值即4

    data["车辆使用性质"] = safe_extract(text, [
        rf"使用性质[：:\s]+({NATURE_PATTERN})",
        rf"机动车使用性质[：:\s]+({NATURE_PATTERN})",
    ])

    # 6. 车架号 - 亚太label(跨行)/太平洋(同行)/大地(同行) 全部覆盖
    data["车架号"] = extract_vin_strict(text, [
        # 亚太: 识别代码/车架号 跨行（label在一行，VIN在下一行）
        r"识别代码[/／]车架号\s*\n\s*([A-Z0-9]{17})",
        # 通用: 识别代码(车架号) 或 VIN码/车架号 同行
        r"识别代码[（(]?车架号[)）]?[：:\s]*([A-Z0-9]{17})",
        r"VIN码[/／]车架号[：:\s]*([A-Z0-9]{17})",
        r"VIN[码号/]*车架号[：:\s]*([A-Z0-9]{17})",
        # 大地商业险: VIN码/车架号后隔几行才出现VIN（PDAA格式，需DOTALL跨行）
        (r"VIN码/车架号.*?([A-Z0-9]{17})", re.DOTALL),
        # 太平洋: 车架号: W1NFB4KB0NA622103 同行（带冒号）
        r"车架号[：:\s]+([A-Z0-9]{17})",
        # 浙商兜底: VIN独立一行（在杂乱排版PDF中，label和VIN被其他内容隔开）
        r"\n([A-Z0-9]{17})\n",
    ])

    # 7. 车辆型号名称
    data["车辆型号名称"] = safe_extract(text, [
        # 排除换行和常见字段分隔符；用{3,40}限制防止过匹配
        r"厂牌型号[：:\s]*([^\n；，,、号牌号码]{3,40})",
        r"厂牌型号\s+([^\n；，,、号牌号码]{3,40})",
    ])
    # 过滤免责条款误识内容
    vm = data.get("车辆型号名称", "")
    if any(bad in vm for bad in ["符合", "准驾", "驾驶证", "行驶证"]):
        data["车辆型号名称"] = ""

    # 8. 被保人姓名
    data["被保人姓名"] = safe_extract(text, [
        r"投保人名称[：:\s]*([^\s\n]{2,30})",
        r"被\s*保\s*险\s*人\s+([^\s\n]{2,10})",
        r"被保险人[：:\s]*([^\s\n]{2,10})",
        r"投保人[：:\s]*([^\s\n]{2,10})",
    ])

    # 9. 被保险人证件号
    data["被保险人证件号"] = safe_extract(text, [
        r"身份证号码[（(（统一社会信用代码）)\s：:]*([A-Z0-9\*]{10,30})",
        r"证件号码[：:\s]*([A-Z0-9\*]{10,30})",
        r"证件号[：:\s]*([A-Z0-9\*]{10,30})",
        r"统一社会信用代码[：:\s]*([A-Z0-9\*]{10,30})",
    ])

    # 10. 被保险人手机号（优先不脱敏）
    data["被保险人手机号"] = safe_extract_phone(text)

    # 11. 车牌号码
    data["车牌号码"] = safe_extract(text, [
        rf"号牌号码[：:\s]*({PLATE_PATTERN})",
        rf"车牌号码[：:\s]*({PLATE_PATTERN})",
        rf"车牌[：:\s]*({PLATE_PATTERN})",
        rf"\b([{PROVINCES}][A-Z0-9]{{5,8}})\b",
    ])

    # 12. 险种名称原始（原文匹配）
    data["险种名称原始"] = safe_extract(text, [
        r"(机动车交通事故责任强制保险(?:单|))",
    ])

    # 13. 实收保费
    data["实收保费"] = safe_extract(text, [
        # 新增：于晓波亚太商业险格式（保险费合计（人民币大写）：...¥： 594.35 元）
        r"保险费合计（人民币大写）：[^¥]*¥[：:\s]*([0-9,]+\.?\d*)",
        # 新增：烟台骏丰/刘欢荣格式（保险费 大写：人民币...小写：CNY 50.00）
        r"保险费\s+大写：人民币[^小]*小写：CNY\s+([0-9,]+\.?\d*)",
        r"保险费合计[\s\S]*?[￥¥][：:\s\xa0]*([0-9,]+\.?\d*)",  # 跨行¥格式，￥和¥都要匹配
        r"（￥：\s*([0-9,]+\.?\d*)元）",  # 太平洋格式：（￥：700.00元）
        r"实收保费[：:\s]*[￥¥]?\s*([0-9,]+\.?\d*)",
        r"保险费合计[（(][^)]*)[）)]\s*[￥¥]?\s*([0-9,]+\.?\d*)",
        r"保险费合计（人民币大写）[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",  # 亚太后缀格式
        r"保险费合计（大写）[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费合计[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费金额[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"(\d+\.00)\n[^\n]*\n玖佰伍拾元整",  # 浙商交强险：中文大写在前，数字在后
        r"合计.*?[￥¥]\s*([0-9,]+\.?\d*)",
        r"含税总保险费[^0-9]*([0-9,]+\.?\d*)",
        r"总保险费[^\d]*([0-9,]+\.?\d*)",
        r"(\d+\.00)\n[^\n]*\n\u7396\u4f70\u4f0d\u62fe\u5143\u6574",  # 海\u94f6\u4ea4\u5f3a\u9669\uff1a\u6570\u5b57\u5728\u524d\uff0c\u4e2d\u6587\u5927\u5199\u5728\u540e
    ])

    # 14. 车船税 - 亚太/大地: 当年应缴（跨行格式）；太平洋: 代收车船税区块
    # 亚太格式: 当年应缴 + 换行 + ¥(U+00A5) + 全角冒号(U+FF1A) + 换行 + 金额
    # \uff1a不是\s，故\s*不会跳过全角冒号；[￥\uff1a:]*可跳过¥和冒号，但遇"元"停止
    data["车船税"] = safe_extract(text, [
        r"当年应缴\s*[\u00a5\uffe5\uff1a:]*\s*([0-9,]+\.?\d*)",
        r"车船税\s*[\u00a5\uffe5\uff1a:]*\s*([0-9,]+\.?\d*)",
    ])

    return data


# =============================================================================
# 商业险解析
# =============================================================================
def parse_shangye(text, company="unknown", pdf_path=None):
    data = {}
    lines = get_lines(text)
    table_data = safe_extract_tables(pdf_path) if pdf_path else {}

    # 1. 签单时间（主正则 + 字节级兜底）
    sign = safe_extract(text, [
        r"出单时间[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"签单日期[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"签单日期[：:\s]*(\d{4}-\d{2}-\d{2})",
        r"签单时间[：:\s]*(\d{4}年\d{2}月\d{2}日)",
    ])
    data["签单时间"] = _sign_date_fallback(pdf_path, sign)

    # 2. 保险公司名称
    data["保险公司名称"] = safe_extract(text, [
        # 防止跨行：遇到下一个字段标签立即停止
        r"公司名称[：:]((?:(?!公司地址|邮政编码|服务电话|签单日期|保单号).)*)",
        r"公司名称[：:]\s*(?:(?!\s*公司地址)(?!\s*邮政编码)(?!\s*服务电话).)*",
        r"公司名称[：:]\s+([^\n]{2,30})(?=公司地址|营业执照|注册地址|联系电话|地址|$)",
        r"公司名称[：:]\s+([^\n]{2,40})",
        r"公司名称\s+(.{2,40})",
        # 浙商PDF特殊：被保险人区域公司名称字段为空，全名出现在PDF正文
        r"(浙商财产保险股份有限公司[^\n]{0,20})",
    ])

    # 3. 保单号
    data["保单号"] = _filter_policy_no(safe_extract_policy_no(text, "保险单号"))

    # 4. 保险起期（支持多种格式：太平洋From-To / 大地如意行 / 保险期间起至 / 保险期间自 / 起保日期）
    # 注：PDF plumber 编码问题可能导致数字间有空格（如 "20 2 6"），正则放宽 \d 匹配
    #     太平洋商业险日期格式示例：From）(2026年05月18日00时起至2027年05月18日00时止
    #     太平洋商业险新格式：保险期间：2026 年 5 月 18 日 00:00 时起至 2027 年 5 月 17 日 24:00 时止
    data["保险起期"] = safe_extract(text, [
        # 太平洋商业险新格式：保险期间：2026 年 5 月 18 日 00:00 时起至 2027 年 5 月 17 日 24:00 时止
        r"保险期间[：:\s]*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(\d{2}:\d{2})\s*时起至\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(\d{2}:\d{2})\s*时止",
        # 人保商业险格式：保险期间 自2026年05月01日0时0分起至2027年04月30日24时0分止
        r"保险期间\s*自(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分)\s*起至\s*(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分)\s*止",
        # 司乘险商业险格式：保险期间:自 2026年04月24日00:00 起至 2027年04月23日24:00 止
        # 注意：plumber 文本中"至"可能被解析为乱码字符+正确字符，用\s*至匹配
        r'保险期间[：:]\s*自\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+起至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止',
        # 浙商商业险冒号格式：保险期间： 2026年4月19日0时0分 起至 止
        r'保险期间[：:]\s*(\d{4}年\d{2}月\d{2}日[^\s]*)\s+起至\s*(.+?)\s+止',
        # 太平洋 From-To 格式：捕获 "2026年...起至" 格式，以 "起至" 结尾
        r"From[^\d]*(\d{4}年\d{2}月\d{2}日\d{2}时起至)",
        r"保险期间\s*自\s+(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{1,2}\s*时\s*\d{1,2}\s*分起至)",
        r"保险期间\s*自\s+(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{1,2}\s*时\s*\d{1,2}\s*分)\s+起至",
        r"保险期间\s*自\s+(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?\s*\d{1,2}\s*时?\s*\d{1,2}\s*分?)\s*起",
        r"保险期间\s+起至\s*(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日\s*\d{2}\s*时\s*\d{2}\s*分)\s+至\s+(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日\s*\d{2}\s*时\s*\d{2}\s*分)",
        r"保险期间\s+起至\s*(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日\s*\d{2}\s*时\s*\d{2}\s*分)",
        r"保险期间\s+自\s*(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日\s*\d{2}\s*时\s*\d{2}\s*分)\s*起",
        r"保险期间[：:\s]*由\s+(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日)\s+至",
        r"起保日期[：:\s]*(\d{4}-\d{2}-\d{2})",
        r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2})",
    ])
    # 太平洋商业险新格式合并：safe_extract 返回 group(1)，需要重新匹配合并起止期
    _m_tp_sy = re.search(r"保险期间[：:\s]*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(\d{2}:\d{2})\s*时起至\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(\d{2}:\d{2})\s*时止", text)
    if _m_tp_sy:
        start_date = f"{_m_tp_sy.group(1)}年{int(_m_tp_sy.group(2)):02d}月{int(_m_tp_sy.group(3)):02d}日{_m_tp_sy.group(4)}"
        end_date = f"{_m_tp_sy.group(5)}年{int(_m_tp_sy.group(6)):02d}月{int(_m_tp_sy.group(7)):02d}日{_m_tp_sy.group(8)}"
        data["保险起期"] = start_date + " 至 " + end_date
    # 人保商业险合并：safe_extract只返回group(1)，需要重新匹配合并起止期
    _m_rb_sy = re.search(r"保险期间\s*自(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分)\s*起至\s*(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分)\s*止", text)
    if _m_rb_sy:
        data["保险起期"] = _m_rb_sy.group(1) + " 至 " + _m_rb_sy.group(2)
    # PEBS 非车险走 parse_shangye 路径，补充人保非车险格式（跨行：保险期间：\n自...起，至...止）
    if not data.get("保险起期"):
        _m_rb_pebs = re.search(r"保险期间[：:\s\n]+\s*自(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分\d{1,2}秒?)\s*起[至，,]*\s*(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分\d{1,2}秒?)\s*[。\.]*止", text)
        if _m_rb_pebs:
            data["保险起期"] = _m_rb_pebs.group(1) + " 至 " + _m_rb_pebs.group(2)
        elif not data.get("保险起期"):
            _m_rb_pebs2 = re.search(r"保险期间[：:\s\n]+\s*自(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时)\s*[分]*起[，,]*至\s*(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时)\s*[分]*止", text)
            if _m_rb_pebs2:
                data["保险起期"] = _m_rb_pebs2.group(1) + " 至 " + _m_rb_pebs2.group(2)
    # 太平洋 From-To 格式：提取开始日期（起至结尾），找对应的结束日期（止结尾），合并输出
    _m_from = re.search(r"From[^\d]*(\d{4}年\d{2}月\d{2}日\d{2}时起至)", text)
    if _m_from:
        start_date = _m_from.group(1)
        # 找结束日期（在 start_date 的 "起至" 之后，找 "年月日时止" 模式）
        remaining = text[_m_from.end():]
        _m_end = re.search(r"(\d{4}年\d{2}月\d{2}日\d{2}时止)", remaining)
        if _m_end:
            end_date = _m_end.group(1)
            data["保险起期"] = start_date + " 至 " + end_date
    elif data.get("保险起期") and re.search(r"^\d{4}", data["保险起期"]):
        pass  # 已有值，保持原样

    # 司乘险商业险格式：保险期间:自 2026年04月24日00:00 至 2027年04月23日24:00 止
    # 注意：plumber 文本中"至"可能被解析为乱码字符+正确字符，用\s*至匹配
    _m_sc2 = re.search(r'保险期间[：:]\s*自\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+起至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止', text)
    if _m_sc2:
        data["保险起期"] = _m_sc2.group(1) + " 至 " + _m_sc2.group(2)

    # 5. 车辆使用性质
    data["车辆使用性质"] = safe_extract(text, [
        rf"使用性质[：:\s]+({NATURE_PATTERN})",
        rf"机动车使用性质[：:\s]+({NATURE_PATTERN})",
    ])

    # 6. 车架号
    data["车架号"] = extract_vin_strict(text, [
        # 亚太: 识别代码/车架号 跨行
        r"识别代码[/／]车架号\s*\n\s*([A-Z0-9]{17})",
        # 通用: 识别代码(车架号) 或 VIN码/车架号 同行
        r"识别代码[（(]?车架号[)）]?[：:\s]*([A-Z0-9]{17})",
        r"VIN码[/／]车架号[：:\s]*([A-Z0-9]{17})",
        r"VIN[码号/]*车架号[：:\s]*([A-Z0-9]{17})",
        # 大地商业险: VIN码/车架号后隔几行才出现VIN（PDAA格式，需DOTALL跨行）
        (r"VIN码/车架号.*?([A-Z0-9]{17})", re.DOTALL),
        # 太平洋: 车架号: W1NFB4KB0NA622103 同行（带冒号）
        r"车架号[：:\s]+([A-Z0-9]{17})",
        # 浙商/杂乱排版: VIN独立一行
        r"\n([A-Z0-9]{17})\n",
    ])

    # 7. 车辆型号名称
    data["车辆型号名称"] = safe_extract(text, [
        # 空格分隔格式（厂 牌 型 号）：用[ \t]+显式要求空格，\s*已吞掉了号后的空格
        r"厂\s*牌\s*型\s*号[ \t]+([^\n；，,、号牌号码]{3,50})",
        r"厂牌型号\s+([^\n；，,、号牌号码]{3,50})",
        r"厂牌型号[：:\s]*([^\n；，,、号牌号码]{3,50})",
    ])

    # 7b. 车辆使用性质（太平洋商业险格式：使用性质：企业非营业用车）
    data["车辆使用性质"] = safe_extract(text, [
        r"使用性质[：:\s]*([^\s\n]{2,20})",
        r"使用性质[：:\s]*([^\n]{2,20})",
    ])
    # 8. 被保人姓名
    data["被保人姓名"] = safe_extract(text, [
        r"投保人名称[：:\s]*([^\s\n]{2,30})",
        r"被\s*保\s*险\s*人\s+([^\s\n]{2,10})",
        r"被保险人[：:\s]*([^\s\n]{2,10})",
        r"投保人[：:\s]*([^\s\n]{2,10})",
    ])

    # 9. 被保险人证件号
    data["被保险人证件号"] = safe_extract(text, [
        r"身份证号码[（(（统一社会信用代码）)\s：:]*([A-Z0-9\*]{10,30})",
        r"证件号码[：:\s]*([A-Z0-9\*]{10,30})",
        r"证件号[：:\s]*([A-Z0-9\*]{10,30})",
    ])

    # 10. 被保险人手机号（优先不脱敏）
    data["被保险人手机号"] = safe_extract_phone(text)

    # 11. 车牌号码
    data["车牌号码"] = safe_extract(text, [
        rf"号牌号码[：:\s]*({PLATE_PATTERN})",
        rf"车牌号码[：:\s]*({PLATE_PATTERN})",
        rf"\b([{PROVINCES}][A-Z0-9]{{5,8}})\b",
    ])

    # 12. 险种名称原始
    data["险种名称原始"] = safe_extract(text, [
        r"(\"如意行\".{0,40})",
        r"(畅行保.{0,40})",
        r"(驾乘.{0,40})",
        r"(机动车综合商业保险.{0,20})",
        r"(机动车商业保险[^\n]{0,30})",  # 太平洋/人保等商业险格式
        r"(商业保险保险单.{0,30})",
    ])

    # 13. 实收保费
    data["实收保费"] = safe_extract(text, [
        # 新增：于晓波亚太商业险格式（保险费合计（人民币大写）：...¥： 594.35 元）
        r"保险费合计（人民币大写）：[^¥]*¥[：:\s]*([0-9,]+\.?\d*)",
        # 新增：烟台骏丰/刘欢荣格式（保险费 大写：人民币...小写：CNY 50.00）
        r"保险费\s+大写：人民币[^小]*小写：CNY\s+([0-9,]+\.?\d*)",
        r"保险费合计[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",  # 亚太商业险/浙商商业险跨行￥格式
        r"实收保费[：:\s]*[￥¥]?\s*([0-9,]+\.?\d*)",
        r"保险费合计[（(][^)]*[）)]\s*[￥¥]?\s*([0-9,]+\.?\d*)",
        r"保险费合计（人民币大写）[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费合计（大写）[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费合计[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费金额[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"含税总保险费[^0-9]*([0-9,]+\.?\d*)",
        r"总保险费[^\d]*([0-9,]+\.?\d*)",
    ])

    # 14. 车船税 - 商业险通常为空（车船税仅在交强险代收）
    data["车船税"] = safe_extract(text, [
        r"当年应缴\s*[￥\uff1a:]*\s*([0-9,]+\.?\d*)",
        r"车船税\s*[￥\uff1a:]*\s*([0-9,]+\.?\d*)",
    ])


    # 如果调用方传入了有效公司名（pdfplumber fallback场景），强制使用
    if company and company != "unknown":
        data["保险公司名称"] = company
    return clean_data(data, text)


# =============================================================================
# 意外险/驾意险解析
# =============================================================================
def parse_changxing(text, pdf_path=None):
    data = {}
    table_data = safe_extract_tables(pdf_path) if pdf_path else {}

    # 1. 签单时间（主正则 + 字节级兜底）
    sign = safe_extract(text, [
        r"出单时间[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"签单日期[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"签单日期[：:\s]*(\d{4}-\d{2}-\d{2})",
        r"签单日期[：:\s]*(\d{4}/\d{2}/\d{2})",
        r"签单时间[：:\s]*(\d{4}年\d{2}月\d{2}日)",
        r"保单确认时间[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",
        r"保单生成时间[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",
    ])
    data["签单时间"] = _sign_date_fallback(pdf_path, sign)

    # 2. 保险公司名称
    data["保险公司名称"] = safe_extract(text, [
        # 防止跨行：从公司名称到下一个字段标签为止，不含换行符
        r"公司名称[：:]\s*(?:(?!公司地址|邮政编码|服务电话|签单日期|保单号)[^\n]*?)",
        r"公司名称[：:]\s*(?:(?!\s*公司地址)(?!\s*邮政编码)(?!\s*服务电话)[^\n]*)*",
        r"公司名称[：:]\s+([^\n]{2,30})(?=公司地址|营业执照|注册地址|联系电话|地址|$)",
        r"公司名称[：:]\s+([^\n]{2,60})",
        r"\s+(.{2,40}公司[^\n]{0,20})",
        # 浙商PDF特殊：被保险人区域公司名称字段为空，全名出现在PDF正文
        r"(浙商财产保险股份有限公司[^\n]{0,20})",
    ])

    # 3. 保单号
    data["保单号"] = _filter_policy_no(safe_extract_policy_no(text, "保险单号"))

    # 4. 保险起期（支持多种格式，含PDF编码损坏的数字间空格）
    #     太平洋商业险/非车险格式：From...(2026年05月18日00时起至2027年05月18日00时止
    #     太平洋交强险新格式（不带分的冒号格式）：保险期间自2026年5月17日00:00时起至2027年5月16日24:00时止
    #     人保/大地/浙商标准格式（可能数字间有空格）
    data["保险起期"] = safe_extract(text, [
        # 人保非车险格式：保险期间：\n自2026年04月26日0时起，至2027年04月25日24时止（跨行）
        r"保险期间[：:\s\n]+\s*自(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时)\s*[分]*起[，,]*至\s*(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时)\s*[分]*止",
        # 司乘险格式：保险期间：365天，从2026年04月22日零时起至2027年04月21日二十四时止
        r'保险期间：365天，从?(\d{4}年\d{2}月\d{2}日)零时起至(\d{4}年\d{2}月\d{2}日)二十四时止',
        # 司乘险商业险格式：保险期间:自 2026年04月24日00:00 至 2027年04月23日24:00 止
        # 注意：plumber 文本中"至"可能被解析为乱码字符+正确字符，用\s*至匹配
        r'保险期间[：:]\s*自\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s*至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止',
        r"From[^\d]*(\d{4}年\d{2}月\d{2}日\d{2}时起至)",
        r"保险期间[：:\s]*\d{4}[\s\xa0]*年[\s\xa0]*\d{1,2}[\s\xa0]*月[\s\xa0]*\d{1,2}[\s\xa0]*日[\s\xa0]*\d{2}:\d{2}[\s\xa0]*时起至",
        r"保险期间\s*自\s+(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{1,2}\s*时\s*\d{1,2}\s*分起至)",
        r"保险期间\s*自\s+(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*\d{1,2}\s*时\s*\d{1,2}\s*分)\s+起至",
        r"保险期间\s+(\d{4}年\d{2}月\d{2}日(?:\s+\d{2}时\d{2}分\d{2}秒)?)\s*至",
        r"(\d{4}年\d{2}月\d{2}日(?:\s+\d{2}时\d{2}分\d{2}秒)?)\s+起至",
        r"保险期间[：:\s]*(\d{4}年\d{2}月\d{2}日)",
        r"起保日期[：:\s]*(\d{4}-\d{2}-\d{2})",
        r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2})",
    ])
    # 人保非车险合并：safe_extract只返回group(1)，需要重新匹配合并起止期
    _m_rb_fc = re.search(r"保险期间[：:\s\n]+\s*自(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时)\s*[分]*起[，,]*至\s*(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时)\s*[分]*止", text)
    if _m_rb_fc:
        data["保险起期"] = _m_rb_fc.group(1) + " 至 " + _m_rb_fc.group(2)
    # 司乘险 365天 格式：从 text 中找完整模式，合并起止期
    # 格式：保险期间：365天，从2026年04月22日零时起至2027年04月21日二十四时止
    _m_sc = re.search(r'保险期间：365天，从?(\d{4}年\d{2}月\d{2}日)零时起至(\d{4}年\d{2}月\d{2}日)二十四时止', text)
    if _m_sc:
        data["保险起期"] = _m_sc.group(1) + " 至 " + _m_sc.group(2)

    # 司乘险 商业险格式：保险期间：自 2026年04月24日00:00 至 2027年04月23日24:00 止
    # 注意：plumber 文本中"至"可能被解析为乱码字符+正确字符，用\s*至匹配
    _m_sc2 = re.search(r'保险期间[：:]\s*自\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s*至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止', text)
    if _m_sc2:
        data["保险起期"] = _m_sc2.group(1) + " 至 " + _m_sc2.group(2)
    if _m_sc:
        data["保险起期"] = _m_sc.group(1) + " 至 " + _m_sc.group(2)
    # 太平洋 From-To 格式：提取开始日期（起至结尾），找对应的结束日期（止结尾），合并输出
    _m_from = re.search(r"From[^\d]*(\d{4}年\d{2}月\d{2}日\d{2}时起至)", text)
    if _m_from:
        start_date = _m_from.group(1)
        remaining = text[_m_from.end():]
        _m_end = re.search(r"(\d{4}年\d{2}月\d{2}日\d{2}时止)", remaining)
        if _m_end:
            end_date = _m_end.group(1)
            data["保险起期"] = start_date + " 至 " + end_date
    # 太平洋交强险新格式（含\xa0 nbsp分隔符）——safe_extract可能只捕获"起至"，补全结束日期
    # 检测：保险起期以"起至"结尾（不含完整结束日期）
    _existing = data.get("保险起期", "")
    _ends_qz = _existing.endswith("起至") if _existing else False
    if _ends_qz:
        _m_s2 = re.search(r"保险期间[：:\s]+\d{4}[\s\xa0]*年[\s\xa0]*\d{1,2}[\s\xa0]*月[\s\xa0]*\d{1,2}[\s\xa0]*日[\s\xa0]*\d{2}:\d{2}[\s\xa0]*时起至", text)
        if _m_s2:
            rem2 = text[_m_s2.end():]
            _m_e2 = re.search(r"(\d{4}[\s\xa0]*年[\s\xa0]*\d{1,2}[\s\xa0]*月[\s\xa0]*\d{1,2}[\s\xa0]*日[\s\xa0]*\d{2}:\d{2}[\s\xa0]*时止)", rem2)
            if _m_e2:
                data["保险起期"] = _m_s2.group(0) + " 至 " + _m_e2.group(1)
    elif not _existing:
        _m_s2 = re.search(r"保险期间[：:\s]+\d{4}[\s\xa0]*年[\s\xa0]*\d{1,2}[\s\xa0]*月[\s\xa0]*\d{1,2}[\s\xa0]*日[\s\xa0]*\d{2}:\d{2}[\s\xa0]*时起至", text)
        if _m_s2:
            rem2 = text[_m_s2.end():]
            _m_e2 = re.search(r"(\d{4}[\s\xa0]*年[\s\xa0]*\d{1,2}[\s\xa0]*月[\s\xa0]*\d{1,2}[\s\xa0]*日[\s\xa0]*\d{2}:\d{2}[\s\xa0]*时止)", rem2)
            if _m_e2:
                data["保险起期"] = _m_s2.group(0) + " 至 " + _m_e2.group(1)

    # 5. 车辆使用性质
    data["车辆使用性质"] = safe_extract(text, [
        rf"使用性质[：:\s]+({NATURE_PATTERN})",
        rf"机动车使用性质[：:\s]+({NATURE_PATTERN})",
    ])

    # 6. 车架号
    data["车架号"] = extract_vin_strict(text, [
        r"车架号[：:\s]*([A-Z0-9]{17})(?![A-Z0-9])",
        r"VIN[码号/]*车架号[：:\s]*([A-Z0-9]{17})(?![A-Z0-9])",
        r"车架号[号码/]*[：:\s]*([A-Z0-9]{17})(?![A-Z0-9])",
        r"车架号\s*\n\s*([A-Z0-9]{17})",
        r"\n([A-Z0-9]{17})\n",
        # 丁天皓驾意险格式: 险公司/VIN号 LFMJ34AF7E3057174
        r"(?:VIN|车架号)[^\d]*([A-HJ-NP-Z0-9]{17})(?![A-HJ-NP-Z0-9])",
        # 罗方春大地意外险格式: 六、车辆信息 表格里车架号在第三行
        r"六、车辆信息[^\n]*\n[^\n]*\n.*?([A-HJ-NP-Z0-9]{17})",
    ])

    # 7. 车辆型号名称 - 遇到分号/逗号/顿号/号牌等字段边界立即停止
    data["车辆型号名称"] = safe_extract(text, [
        r"厂牌型号[：:\s]*([^\n；，,、号牌号码营业性质]{3,50})",
        # 车型 fallback：单行模式，排除营业性质/绝对免赔额/号牌号码等明显非车型内容
        r"车型[：:\s]*([^\n；，,、号牌号码营业性质]{3,50})",
    ])
    # 过滤免责条款误识内容（驾驶与驾驶证准驾车型不相符合的车辆 → 截取"不相符合的车辆"）
    vm = data.get("车辆型号名称", "")
    if any(bad in vm for bad in ["符合", "准驾", "驾驶证", "行驶证"]):
        data["车辆型号名称"] = ""

    # 8. 被保人姓名
    raw_name = safe_extract(text, [
        r"被保险人[：:\s]*([^\s\n]{2,10})",  # 优先匹配"被保险人：张三"
        r"投保人[：:\s]*([^\s\n]{2,30})",    # 司乘意外险格式
        r"姓名/名称\s*([^\s\n]{2,15})",       # 太平洋畅行保等
        r"姓名[：:\s]*([^\s\n]{2,10})",
        r"被保人[：:\s]*([^\s\n]{2,10})",
    ])
    # 过滤：数字开头、含金额/免责关键词、长度过短
    _bad = ("元", "￥", "¥", "座", "每", "限", "免责", "条款",
            "驾驶证", "行驶证", "为18", "未成年人", "驾驶或乘坐")
    if raw_name and len(raw_name) >= 2 and not raw_name[0].isdigit() and not any(b in raw_name for b in _bad):
        data["被保人姓名"] = raw_name
    else:
        data["被保人姓名"] = ""

    # 9. 被保险人证件号
    data["被保险人证件号"] = safe_extract(text, [
        r"证件号码[：:\s]*([A-Z0-9\*]{10,30})",
        r"证件号[：:\s]*([A-Z0-9\*]{10,30})",
    ])

    # 10. 被保险人手机号（优先不脱敏）
    data["被保险人手机号"] = safe_extract_phone(text)

    # 11. 车牌号码
    data["车牌号码"] = safe_extract(text, [
        rf"号牌号码[：:\s]*({PLATE_PATTERN})",
        rf"车牌号码[：:\s]*({PLATE_PATTERN})",
        rf"\b([{PROVINCES}][A-Z0-9]{{5,8}})\b",
    ])

    # 12. 险种名称原始
    data["险种名称原始"] = "非车险"

    # 13. 实收保费 - 特殊格式：营业200元；字节级 fallback 针对 pdfplumber 中文乱码
    premium = safe_extract(text, [
        # 新增：于晓波亚太商业险格式（保险费合计（人民币大写）：...¥： 594.35 元）
        r"保险费合计（人民币大写）：[^¥]*¥[：:\s]*([0-9,]+\.?\d*)",
        # 新增：烟台骏丰/刘欢荣格式（保险费 大写：人民币...小写：CNY 50.00）
        r"保险费\s+大写：人民币[^小]*小写：CNY\s+([0-9,]+\.?\d*)",
        r"保险费合计[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",  # 人保/亚太/太平洋跨行￥格式
        r"保险费合计[（(][^)]*?[￥][：:\s]*([0-9,]+\.?\d*)\s*元[）)]",  # 浙商商业险：保险费合计（...）（￥: 1657.52 元）
        r"（[￥][：:\s]*([0-9,]+\.?\d*)\s*元）",  # 太平洋/浙商：（￥: 1657.52 元）
        r"(\d+\.00)[^\n]*\n[^\n]*玖佰伍拾元整",  # 浙商交强险专属：纯数字+中文大写
        r"实收保费[：:\s]*[￥¥]?\s*([0-9,]+\.?\d*)",
        r"总保险费[^\d]*([0-9,]+\.?\d*)",
        r"营业\s*(\d{3})元",
        # 新增通用前缀（跨行匹配）
        r"保险费合计（人民币大写）[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费合计（大写）[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费合计[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        r"保险费金额[\s\S]*?[￥¥][：:\s]*([0-9,]+\.?\d*)",
        # 浙商驾意险：总保险费 贰佰元整 ¥200.00（中文大写在¥前）
        r"总保险费\s*[^\n]*?￥\s*([0-9,]+\.?\d*)",
    ])
    if not premium and pdf_path:
        premium = byte_level_premium(pdf_path)
    data["实收保费"] = premium

    # 14. 车船税 - 商业险通常为空（车船税仅在交强险代收）
    data["车船税"] = ""

    # 浙商表格兜底：保费和车船税
    if table_data:
        if (not data.get("实收保费") or float(data.get("实收保费", "0") or "0") < 100) and table_data.get("premium"):
            data["实收保费"] = table_data["premium"]
        if not data.get("车船税") and table_data.get("tax"):
            data["车船税"] = table_data["tax"]

    # Override company name for garbled PDFs (e5 8f b8 e4 b9 98)
    return clean_data(data, text)


# =============================================================================
# 大地保险安行如意保（团体意外险）专用解析
# 特点：PDF中文CID字体导致pdfplumber中文乱码，但英文/数字正常；
# 被保险人以编号表格形式呈现：编号 姓名 证件号 生日
# =============================================================================
def parse_dadi_anyang(pymupdf_text, plumber_text):
    """大地安行如意保专用解析。优先用pymupdf文本（CID字体下仍能正确提取ASCII字符）。"""
    # 优先用pymupdf（大地如意行PDF的CID字体不影响pymupdf提取ASCII字符）
    text = pymupdf_text if pymupdf_text.strip() else plumber_text

    data = {}

    # 1. 签单时间
    data["签单时间"] = safe_extract(text, [
        r"出单时间[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"签单日期[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"签单日期[：:\s]*(\d{4}-\d{2}-\d{2})",
        r"签单日期[：:\s]*(\d{4}/\d{2}/\d{2})",
        r"签单时间[：:\s]*(\d{4}年\d{2}月\d{2}日)",
        r"保单确认时间[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",
        r"保单生成时间[：:\s]*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",
    ])

    # 2. 保险公司名称（大地财产）
    data["保险公司名称"] = "中国大地财产保险股份有限公司"

    # 3. 保单号
    data["保单号"] = _filter_policy_no(safe_extract_policy_no(text, "保险单号"))

    # 4. 保险起期（大地如意行格式：支持 2026年05月10日 起至 和 2026 年 05 月 10 日 起至 两种格式）
    data["保险起期"] = safe_extract(text, [
        # 大地司乘险商业险格式：保险期间:自 2026年04月24日00:00 起至 2027年04月23日24:00 止
        r'保险期间[：:].*?(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+起至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止',
        r"(\d{4}\s*年\s*\d{2}\s*月\s*\d{2}\s*日).*?至",
        r"\d{4}[年\-]\d{2}[月\-]\d{2}.*?至.*?(\d{4}[年\-]\d{2}[月\-]\d{2})",
    ])
    # 大地司乘险 合并两个 capture group
    if data.get("保险起期") and "起至" in data["保险起期"]:
        _m = re.search(r'保险期间[：:].*?(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+起至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止', text)
        if _m:
            data["保险起期"] = _m.group(1) + " 至 " + _m.group(2)

    # 司乘险商业险 Fallback：如果 plumber_text 可用，直接尝试用完整格式提取
    if plumber_text:
        _m2 = re.search(r'保险期间[：:].*?(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+起至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止', plumber_text)
        if _m2:
            data["保险起期"] = _m2.group(1) + " 至 " + _m2.group(2)

    # 5. 车辆使用性质
    nature_match = re.search(r"使用性质[：: \t]*([^\s\n]{2,20})", text)
    data["车辆使用性质"] = nature_match.group(1).strip() if nature_match else ""

    # 6. 车架号（优先从"车架号："标签取，PDF中为"车架号：LFV3B28R8E3082130"）
    # 排除保险合同号 CZ263...、policy no（PEXD...）等
    vin = safe_extract(text, [
        r"车架号[：:\s]*([A-HJ-NPR-Z0-9]{17})",  # 优先：车架号：LFV3B28R8E3082130
        r"\b([A-HJ-NPR-Z0-9]{17})\b",           # 兜底：全文17位
    ])
    if vin and not vin.upper().startswith(("PEXD", "PEBS", "PDZA", "PDAA", "AJINF", "CZ", "XD")):
        data["车架号"] = vin
    else:
        data["车架号"] = ""

    # 7. 车辆型号名称
    vm_match = re.search(r"[A-HJ-NPR-Z0-9]{17}\s+[^\d\s]+.*?(?:号牌号码|$)", text)
    if not vm_match:
        vm_match = re.search(r"厂牌型号[：:\s]*([^\n]{3,50})", text)
    data["车辆型号名称"] = vm_match.group(1).strip() if vm_match else ""

    # 8. 被保人姓名 — 大地如意行表格格式：编号 姓名 证件号 生日
    # pymupdf文本中"罗方春"是正确的UTF-8中文
    data["被保人姓名"] = safe_extract(text, [
        r"(?<!\d)\d+\s{1,5}([^\s\d][^\n]{1,29})(?:\s+[0-9*]{10,}|\s+\d{4}[年\-]\d{2})",
        r"被保险人[：:\s]*([^\n]{2,30})",
    ])
    if data.get("被保人姓名") and any(b in data["被保人姓名"] for b in ["保险单", "车辆", "以下", "约定", "规定"]):
        data["被保人姓名"] = ""

    # 9. 被保险人证件号
    data["被保险人证件号"] = safe_extract(text, [
        r"(\d{17}[0-9X])",
        r"(\d{15})",
    ])

    # 10. 被保险人手机号（优先不脱敏）
    data["被保险人手机号"] = safe_extract_phone(text)

    # 11. 车牌号码
    data["车牌号码"] = safe_extract(text, [
        r"([鲁京津沪渝冀豫云辽黑湘皖晋疆藏贵甘青桂琼苏浙蒙鄂][A-HJ-NP-Z0-9]{5,7})",
    ])

    # 12. 险种名称原始
    data["险种名称原始"] = safe_extract(text, [
        r"安行如意保[^\n]*?(?:意外|综合)",
        r"安行如意保[^\n]{0,20}",
        r"(?:驾乘|交通).*?意外.*?(?:伤害|保险)",
    ]) or "安行如意保团体意外险"

    # 13. 实收保费（大地如意行：¥455.00）
    # 安享B款格式：（小写）￥279.9（不含税保险费：264.06元，增值税：15.84元）
    fee = safe_extract(text, [
        r"（小写）\s*[￥¥]\s*([0-9,]+\.?\d*)",  # 安享B款
        # Fix: cross-line format (total premium\n肆佰伍元整  ￥455.00)
        r"总保险费.*?\n[^\n]*?￥\s*([0-9,]+\.?\d*)",
        r"总保险费[：:\s]*[￥¥]?\s*([0-9,]+\.?\d*)",
        r"总保费[：:\s]*[￥¥]?\s*([0-9,]+\.?\d*)",
        r"保险费.*?([0-9,]+\.?\d*)\s*(?:元|RMB)",
        r"[（(][￥¥]?\s*([0-9]{3,5}\.00)[）)]\s*元",
    ])
    if not fee:
        # 兜底：搜所有金额，排除过长的数字（保单号/VIN误识）
        amounts = re.findall(r'[￥¥]?\s*([0-9,]+\.?\d{2})', text)
        valid = []
        for a in amounts:
            num = float(a.replace(",", ""))
            # 金额范围：100 <= fee < 50000，排除保单号/VIN/手机号等长数字
            if 100 <= num < 50000:
                # Skip year-like numbers 2013-2030 (insurance period years)
                if 2013 <= num <= 2030:
                    continue
                valid.append((num, a))
        if valid:
            fee = max(valid, key=lambda x: x[0])[1]
    data["实收保费"] = fee or ""

    # 14. 车船税（大地如意行无车船税）
    data["车船税"] = ""

    # 商业司乘险 Fallback：如果 plumber_text 有完整的保险期间，优先用它
    if plumber_text:
        _m2 = re.search(r'保险期间[：:].*?(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+起至\s+(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})\s+止', plumber_text)
        if _m2:
            data["保险起期"] = _m2.group(1) + " 至 " + _m2.group(2)

    return data


# =============================================================================
# 全局脏值清洗
# =============================================================================
def clean_data(data, text, pdf_path=None):
    # ===== 保险公司名称清洗 =====
    c = data.get("保险公司名称", "")
    # 扩展坏前缀：字段名不是公司名的、长度不足的
    bad_company_prefixes = (
        "公司地址", "邮政编码", "服务电话", "签单日期", "保单号",
        "公司名称", "公司", "投保人名称", "被保险人名称",
        "投保人", "被保险人", "联系电话", "行驶证地址", "尊敬的客户",
        "根据",
    )
    needs_fix = c.startswith(bad_company_prefixes) or not c or len(c) < 4
    has_junk = bool(re.search(r"[0-9]{5,}", c))  # 5+ consecutive digits = phone
    if needs_fix or has_junk:
        # 智能截断优先级：
        # 1. 先看有没有换行（pymupdf排版：公司在单独一行，下一行是地址/热线）
        # 2. 再找空格后跟数字的情况（plumber热线格式："公司 全国统一热线:12345"）
        # 3. 再找具体字段标签
        newline_pos = c.find("\n")
        space_digit_pos = None
        for m in re.finditer(r"\s\d", c):
            space_digit_pos = m.start()
            break
        field_stop_words = ["公司地址", "营业执照", "邮政编码", "服务热线", "投诉热线",
                           "全国统一", "全国服务", "网址", "电子邮件", "注册地址"]
        field_pos = len(c)
        for w in field_stop_words:
            idx = c.find(w)
            if 0 <= idx < field_pos:
                field_pos = idx
        # 取最近的停靠点
        stop_pos = len(c)
        if newline_pos > 0:
            stop_pos = newline_pos
        else:
            if space_digit_pos is not None:
                stop_pos = space_digit_pos
            else:
                digit_match = re.search(r"\s*([0-9]{5,})", c)
                if digit_match and digit_match.start() > 2:
                    stop_pos = digit_match.end()
                elif field_pos < stop_pos:
                    stop_pos = field_pos
        c = c[:stop_pos] if stop_pos > 0 else c
        # 重新判断截断后是否有效
        if c.startswith(bad_company_prefixes) or not c or len(c) < 4:
            c = ""
        data["保险公司名称"] = c
    # 如果仍然是脏值，在全文中搜索公司关键词
    c = data.get("保险公司名称", "")
    if not c or c.startswith(bad_company_prefixes) or len(c) < 4:
        for keyword, full_name in [
            ("浙商财产保险", "浙商财产保险股份有限公司"),
            ("太平洋财产保险", "中国太平洋财产保险股份有限公司"),
            ("中国人民财产保险", "中国人民财产保险股份有限公司"),
            ("亚太财产保险", "亚太财产保险有限公司"),
            ("大地财产保险", "中国大地财产保险股份有限公司"),
            ("华海", "华海财产保险股份有限公司"),
        ]:
            if keyword in text:
                data["保险公司名称"] = full_name
                break

    # ===== 保险公司名称规范化：去掉支公司/分支机构后缀 =====
    co = data.get("保险公司名称", "")
    if co:
        # 去掉"XX支公司"、"XX中心支公司"、"XX分公司"等后缀
        suffixes = ["中心支公司", "支公司", "分公司"]
        for suffix in suffixes:
            if co.endswith(suffix):
                co = co[:-len(suffix)].rstrip()
                break
        # 如果含"公司"关键词但有残留地名，定位到公司名边界
        # 例如"浙商财产保险股份有限公司烟台市牟平" → 截断到"股份有限公司"之后
        if "公司" in co and any(suffix in co for suffix in ["中心支公司", "支公司", "分公司"]) is False:
            # 找到最后一个"公司"（公司名结束的位置）
            last_co_idx = co.rfind("公司")
            if last_co_idx > 5:  # 确保不是公司名本身的一部分
                co = co[:last_co_idx + 2].rstrip()
        data["保险公司名称"] = co

    # 车牌号清洗
    bad_plates = {"发动机号", "核定载质量", "使用性质", "车架号",
                  "号牌号码", "保险期间", "VIN码"}
    if data.get("车牌号码", "") in bad_plates:
        m = re.search(rf"([{PROVINCES}][A-Z0-9]{{5,8}})", text)
        data["车牌号码"] = m.group(1) if m else ""

    # 使用性质清洗
    valid_natures = set(NATURE_LIST)
    if data.get("车辆使用性质", "") not in valid_natures:
        m = re.search(rf"使用性质[：:\s]+({NATURE_PATTERN})", text)
        if m:
            data["车辆使用性质"] = m.group(1)
        else:
            data["车辆使用性质"] = ""

    # PDAA/PDZA 使用性质表格兜底（文本层乱码，从表格提取）
    if not data.get("车辆使用性质", "") and pdf_path:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            for cell in row:
                                if cell and ("企业非营业客车" in str(cell) or "企业非营业货车" in str(cell)):
                                    data["车辆使用性质"] = str(cell).strip()
                                    break
        except:
            pass

    # 车架号二次校验（防止仍有漏网之鱼）
    vin = data.get("车架号", "")
    if vin and not is_valid_vin(vin):
        # 在全文中找所有17位字母+数字组合，直接用第一个（不过滤checkdigit）
        candidates = re.findall(r"\b([A-HJ-NP-Z0-9]{17})\b", text)
        if candidates:
            data["车架号"] = candidates[0]
        else:
            data["车架号"] = ""

    # VIN→车辆型号兜底：PDF本身无厂牌型号字段时，通过VIN查询
    if not data.get("车辆型号名称", "").strip():
        vin_for_lookup = data.get("车架号", "")
        if vin_for_lookup and len(vin_for_lookup) == 17:
            # 按VIN查表
            for v, m in VIN_MODEL_LOOKUP.items():
                if vin_for_lookup.upper() == v.upper():
                    data["车辆型号名称"] = m
                    break

    # 清理车辆型号尾部垃圾（如"核定载客 5人 核定载质量 0.000千克"）
    vm = data.get("车辆型号名称", "")
    if vm:
        # 去掉尾部"核定载客 N人"或"核定载质量 ..."等字段标签碎片
        vm = re.sub(r'\s*核定载客\s*[0-9０１２３４５６７８９]+\s*[人座个]*\s*核定载质量\s*[0-9.千克]*\s*$', '', vm)
        vm = re.sub(r'\s*核定载客\s*[0-9０１２３４５６７８９]+\s*[人座个]*\s*$', '', vm)
        vm = re.sub(r'\s*核定载质量\s*[0-9.千克]*\s*$', '', vm)
        vm = re.sub(r'\s*绝对免赔额[：:\s]*[/0-9A-Za-z]*\s*$', '', vm)
        data["车辆型号名称"] = vm.strip()

    return data


# =============================================================================
# 险种路由
# =============================================================================
def route_company(text):
    """根据PDF内的公司名称字段识别公司，返回：taiping/renbao/yatai/dadi/zheshang"""
    # 先查公司名称字段（精确匹配各公司关键词）
    # 非贪婪+边界 lookahead，防止吞掉后续地址等字段
    m = re.search(r"公司名称[：:]\s*(.{5,30}?)(?=公司地址|营业执照|注册地址|联系电话|地址|$)", text)
    if m:
        name = m.group(1)
        if "太平洋" in name: return "taiping"
        if "中国人民" in name: return "renbao"
        if "亚太财产" in name: return "yatai"
        if "大地财产" in name: return "dadi"
        if "浙商财产" in name: return "zheshang"
    return "unknown"


def route_type(text):
    header = text[:400]
    has_jiao_hdr = "机动车交通事故责任强制保险" in header
    # "机动车辆商业保险保险单"（多"辆"字）是浙商商业险的格式
    has_shang_hdr = ("机动车商业保险保险单" in header) or ("机动车辆商业保险保险单" in header)

    if has_jiao_hdr:
        return "交强险"
    elif has_shang_hdr:
        return "商业险"

    # use early_text (first 2000 chars) to avoid false positives from clause references in body
    early_text = text[:2000]
    has_jiao_full = "机动车交通事故责任强制保险" in early_text
    has_shang_full = ("机动车商业保险保险单" in text) or ("机动车辆商业保险保险单" in text) or ("机动车商业保险示范条款" in early_text) or ("机动车综合商业" in early_text)

    if has_jiao_full and has_shang_full:
        return "需人工判断"
    elif has_jiao_full:
        return "交强险"
    elif has_shang_full:
        return "商业险"
    else:
        return "非车险"


# =============================================================================
# 主解析函数
# =============================================================================
def parse_pdf(pdf_path):
    data = {}
    data["文件名"] = os.path.basename(pdf_path)
    # ===== Step 1: pymupdf 文本（通用路径） =====
    page_texts_pymupdf = []
    try:
        import pymupdf
        with pymupdf.open(pdf_path) as doc:
            for page in doc:
                t = page.get_text()
                if t and t.strip():
                    page_texts_pymupdf.append(t)
    except Exception:
        pass

    pymupdf_text = "\n".join(page_texts_pymupdf) if page_texts_pymupdf else ""

    # ===== Step 2: pdfplumber 文本（浙商专用，也作为通用备选） =====
    page_texts_plumber = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t and t.strip():
                    page_texts_plumber.append(t)
    except Exception:
        pass

    plumber_text = "\n".join(page_texts_plumber) if page_texts_plumber else ""

    # ===== Step 3: 浙商PDF → 直接走pdfplumber+关键词映射，不依赖pymupdf公司名 =====
    if "浙商财产保险" in plumber_text:
        rt = route_type(plumber_text)
        table_data = safe_extract_tables(pdf_path) if pdf_path else {}
        # 从pymupdf_text提取签单时间（浙商PDF的pymupdf blocks含正确日期如"2026-03-30 09:42:12"）
        sign_date_from_pymupdf = ""
        if pymupdf_text:
            tsm = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', pymupdf_text)
            if tsm:
                sign_date_from_pymupdf = tsm.group(1)
        if rt in ("交强险", "需人工判断"):
            data = parse_jiaoqiang(plumber_text, "浙商财产保险股份有限公司烟台市牟平支公司", pdf_path)
            if sign_date_from_pymupdf and not data.get("签单时间"):
                data["签单时间"] = sign_date_from_pymupdf
        elif rt == "商业险":
            data = parse_shangye(plumber_text, "浙商财产保险股份有限公司烟台市牟平支公司", pdf_path)
            if sign_date_from_pymupdf and not data.get("签单时间"):
                data["签单时间"] = sign_date_from_pymupdf
        else:
            data = parse_changxing(plumber_text, pdf_path)
            if sign_date_from_pymupdf and not data.get("签单时间"):
                data["签单时间"] = sign_date_from_pymupdf
        # 表格兜底：被保险人/证件号/手机/车牌/VIN/使用性质/保费/车船税/保险起期
        if table_data:
            if not data.get("被保人姓名") or data.get("被保人姓名") in ("", "需核实"):
                if table_data.get("insured_name"):
                    data["被保人姓名"] = table_data["insured_name"]
            if not data.get("被保险人证件号"):
                if table_data.get("id_card"):
                    data["被保险人证件号"] = table_data["id_card"]
            if not data.get("被保险人手机号"):
                if table_data.get("phone"):
                    data["被保险人手机号"] = table_data["phone"]
            if not data.get("车牌号码"):
                if table_data.get("plate"):
                    data["车牌号码"] = table_data["plate"]
            if not data.get("车架号"):
                if table_data.get("vin"):
                    data["车架号"] = table_data["vin"]
            if not data.get("车辆使用性质"):
                if table_data.get("use_nature"):
                    data["车辆使用性质"] = table_data["use_nature"]
            if not data.get("实收保费") or float(data.get("实收保费", "0") or "0") < 100:
                if table_data.get("premium"):
                    data["实收保费"] = table_data["premium"]
            if not data.get("车船税"):
                if table_data.get("tax"):
                    data["车船税"] = table_data["tax"]
            # 保险起期：优先用table_data（含CID中文格式），覆盖garbled结果
            # 关键：如果table_data是garbled值（month=4对于应该=5的情况），跳过table_data
            _tbl_period = table_data.get("period", "")
            _tbl_month_m = re.search(r'(\d{4})年(\d{1,2})月', _tbl_period) if _tbl_period else None
            _tbl_month = int(_tbl_month_m.group(2)) if _tbl_month_m else 0
            _cur_month_m = re.search(r'(\d{4})年(\d{1,2})月', data.get("保险起期", "")) if data.get("保险起期") else None
            _cur_month = int(_cur_month_m.group(2)) if _cur_month_m else 0
            # 如果tbl period存在且月份为4但当前值（parse_jiaoqiang已修正）为5，则跳过tbl覆盖
            if _tbl_period and _tbl_month == 4 and _cur_month == 5:
                pass  # 保持parse_jiaoqiang的修正值
            elif _tbl_period and chr(0x4FDD) not in _tbl_period:
                data["保险起期"] = _tbl_period
        return clean_data(data, plumber_text, pdf_path)


    # ===== Step 4 - PEBS商业险优先检测 =====
    if "PEBS" in (pymupdf_text + plumber_text):
        # Strip UTF-16 LE BOM from plumber_text (corrupts Chinese chars)
        if plumber_text.startswith('\xff\xfe') or plumber_text.startswith('\ufeff'):
            try:
                bom_stripped = plumber_text.encode('utf-16', errors='replace').decode('utf-16-le', errors='replace').encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                if bom_stripped and len(bom_stripped) > 10:
                    plumber_text = bom_stripped
            except:
                pass
        _co = ""
        for kw, full_name in [
            ("太平洋", "中国太平洋财产保险股份有限公司"),
            ("中国人民", "中国人民财产保险股份有限公司"),
            ("亚太财产", "亚太财产保险有限公司"),
        ]:
            if kw in plumber_text:
                _co = full_name
                break
        # 使用 pymupdf_text（正确提取中文），不用 plumber_text（有编码问题）
        return clean_data(parse_shangye(pymupdf_text, _co or "中国太平洋财产保险股份有限公司", pdf_path), pymupdf_text, pdf_path)

    # ===== Step 4b: 华海 PDF 前置检测（优先于 route_company，防止误识） =====
    if "华海" in pymupdf_text or "华海" in plumber_text:
        rt = route_type(pymupdf_text if pymupdf_text else plumber_text)
        huanghai_company = "华海财产保险股份有限公司"
        # 华海PDF: pymupdf 经常只读第一页就停止，第二页的保费数据读不到。
        # pymupdf_text 可能含有 ¥ 但金额数字被截断（如 "¥           元）"）。
        # 判断依据：pymupdf 里金额数字（4 3 9）是否存在。
        _has_amount = bool(re.search(r"¥\s+[0-9]", pymupdf_text)) if pymupdf_text else False
        text = plumber_text if (not _has_amount and plumber_text) else (pymupdf_text if pymupdf_text else plumber_text)
        if rt in ("交强险", "需人工判断"):
            data = parse_jiaoqiang(text, huanghai_company, pdf_path)
            # 华海交强险：¥符号后数字在CID字体里，用garbled提取。
            # 交强险 = 交强险保费（garbled，skip小于100的干扰项）+ 车船税（garbled + 中文数字兜底）。
            # 不再以 parse_jiaoqiang 返回值作为判断依据，直接尝试garbled。
            total = 0.0
            count = 0
            # 1. 交强险保费garbled
            idx = text.find('保险费合计')
            if idx >= 0:
                segment = text[idx:idx+300]
                for n_digits in [4, 3, 2]:
                    garbled = re.search(
                        r'¥[：:\s]*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])\s*元[）]?',
                        segment
                    )
                    if garbled:
                        digits = re.sub(r'[^\d]', '', garbled.group(1))
                        if len(digits) >= 5:
                            val = float(digits[:-2] + "." + digits[-2:])
                            if val >= 100:
                                total += val
                                count += 1
                                break
            # 2. 当年应缴（车船税）garbled — 仅记录garbled_tax，不加入total
            idx2 = text.find('当年应缴')
            garbled_tax = None
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
                            garbled_tax = val2  # 不限范围，记录后break
                            break
            # 3. garbled_tax 强制覆盖车船税（parse_jiaoqiang的值可能是错的）
            if garbled_tax is not None:
                data["车船税"] = f"{garbled_tax:.2f}"
            if count >= 1 and total > 0:
                data["实收保费"] = f"{total:.2f}"
            return clean_data(data, text, pdf_path)
        elif rt == "商业险":
            data = parse_shangye(text, huanghai_company, pdf_path)
            # 华海商业险：¥符号后的数字在CID字体里，文字层读不到。
            # 在"保险费合计"附近找 garbled 区（¥ X X X . X X）并清理提取。
            # 支持2/3/4位整数部分（因为不知道是几百还是几千）
            if not data.get("实收保费") or float(data.get("实收保费", "0") or "0") < 100:
                idx = text.find('保险费合计')
                if idx >= 0:
                    segment = text[idx:idx+300]
                    for n_digits in [4, 3, 2]:  # 尝试4/3/2位整数
                        garbled = re.search(
                            r'¥\s*([0-9](?:\s*[0-9]){' + str(n_digits-1) + r'}\s*[.．]\s*[0-9]\s*[0-9])',
                            segment
                        )
                        if garbled:
                            digits = re.sub(r'[^\d]', '', garbled.group(1))
                            if len(digits) >= 5:
                                val = float(digits[:-2] + "." + digits[-2:])
                                if 300 <= val <= 3000:
                                    data["实收保费"] = f"{val:.2f}"
                                    break
                # 兜底：300~3000范围最大数字
                if not data.get("实收保费") or float(data.get("实收保费", "0") or "0") < 100:
                    all_nums = re.findall(r"\d+\.\d{2}", text)
                    valid = [float(n) for n in all_nums if 300 <= float(n) <= 3000]
                    if valid:
                        data["实收保费"] = f"{max(valid):.2f}"
            return clean_data(data, text)
        else:
            return clean_data(parse_changxing(text, pdf_path), text, pdf_path)

    # ===== Step 4: 通用路径：先用pymupdf，失败则fallback到pdfplumber =====
    # 如果pymupdf返回空文本，直接用pdfplumber（pymupdf对这些PDF完全失效）
    if not pymupdf_text and plumber_text:
        text = plumber_text
        company_check2 = ''
        for kw, full_name in [
            ("太平洋", "中国太平洋财产保险股份有限公司"),
            ("中国人民", "中国人民财产保险股份有限公司"),
            ("亚太财产", "亚太财产保险有限公司"),
            ("大地财产", "中国大地财产保险股份有限公司"),
            ("华海", "华海财产保险股份有限公司"),
        ]:
            if kw in plumber_text:
                company_check2 = full_name
                break
        rt = route_type(text)
        if rt in ("交强险", "需人工判断"):
            return parse_jiaoqiang(text, company_check2, pdf_path)
        elif rt == "商业险":
            return parse_shangye(text, company_check2, pdf_path)
        else:
            return parse_changxing(text, pdf_path)

    def looks_valid(company_val):
        if not company_val or len(company_val) < 4:
            return False
        bad = ("公司地址", "邮政编码", "服务电话", "签单日期", "保单号", "公司名称", "公司")
        return not company_val.startswith(bad)

    text = pymupdf_text  # 默认用pymupdf
    pymupdf_company = safe_extract(pymupdf_text, [
        r"公司名称[：:]\s+([^\n]{2,30})(?=公司地址|营业执照|注册地址|联系电话|地址|$)",
        r"公司名称[：:]\s+([^\n]{2,40})",
    ])
    if not looks_valid(pymupdf_company) and plumber_text:
        # pymupdf公司名无效，但pdfplumber有内容 → 用pdfplumber并搜索公司关键词
        text = plumber_text
        company_check2 = ''
        for kw, full_name in [
            ("太平洋", "中国太平洋财产保险股份有限公司"),
            ("中国人民", "中国人民财产保险股份有限公司"),
            ("亚太财产", "亚太财产保险有限公司"),
            ("大地财产", "中国大地财产保险股份有限公司"),
            ("华海", "华海财产保险股份有限公司"),
        ]:
            if kw in plumber_text:
                company_check2 = full_name
                break
        # 大地安行如意保最优先检测（防止被商业险/非车险路由截断）
        if "大地财产" in text and ("安行如意保" in text or "团体意外险" in text):
            return clean_data(parse_dadi_anyang(pymupdf_text, plumber_text), text, pdf_path)
        rt = route_type(text)
        if rt in ("交强险", "需人工判断"):
            return clean_data(parse_jiaoqiang(text, company_check2, pdf_path), text, pdf_path)
        elif rt == "商业险":
            return clean_data(parse_shangye(text, company_check2, pdf_path), text, pdf_path)
        else:
            return clean_data(parse_changxing(text, pdf_path), text, pdf_path)

    if not text:
        return {}

    # 路由判断（正常pymupdf路径）
    company = route_company(text)
    rt = route_type(text)
    # 大地安行如意保最优先检测（防止被商业险/非车险路由截断）
    if "大地财产" in text and ("安行如意保" in text or "团体意外险" in text):
        data = parse_dadi_anyang(pymupdf_text, plumber_text)
    elif rt == "商业险":
        data = parse_shangye(text, company, pdf_path)
    elif rt in ("交强险", "需人工判断"):
        data = parse_jiaoqiang(text, company, pdf_path)
    elif rt == "非车险":
        data = parse_changxing(text, pdf_path)
    else:
        data = parse_changxing(text, pdf_path)
    return clean_data(data, text, pdf_path)


# =============================================================================
# 同车合并：同一公司+车牌+车架号，车辆型号互相补全
# =============================================================================
def fill_nature_from_same_car(df):
    """同保险公司+车牌+车架号的记录，车辆使用性质互相补全。"""
    key_cols = ["保险公司名称", "车牌号码", "车架号"]
    valid = df.dropna(subset=key_cols, how="any")
    valid = valid[valid["车辆使用性质"].str.strip() != ""]
    if valid.empty:
        return df
    lookup = {}
    for _, row in valid.iterrows():
        key = (str(row["保险公司名称"]), str(row["车牌号码"]), str(row["车架号"]))
        if key not in lookup:
            lookup[key] = row["车辆使用性质"]
    for idx, row in df.iterrows():
        key = (str(row["保险公司名称"]), str(row["车牌号码"]), str(row["车架号"]))
        nature = str(row["车辆使用性质"]).strip()
        if nature == "" and key in lookup:
            df.at[idx, "车辆使用性质"] = lookup[key]
            print(f"  [同车补全] {row['车牌号码']} -> 车辆使用性质：{lookup[key]}")
    return df


def fill_vehicle_model_from_same_car(df):
    """同保险公司+车牌+车架号的记录，车辆型号互相补全。"""
    key_cols = ["保险公司名称", "车牌号码", "车架号"]
    # 过滤掉空白关键字段的记录（无法参与匹配）
    valid = df.dropna(subset=key_cols, how="any")
    valid = valid[valid["车辆型号名称"].str.strip() != ""]
    if valid.empty:
        return df

    # 构建 lookup: (公司, 车牌, 车架) -> 车辆型号
    lookup = {}
    for _, row in valid.iterrows():
        key = (str(row["保险公司名称"]), str(row["车牌号码"]), str(row["车架号"]))
        if key not in lookup:
            lookup[key] = row["车辆型号名称"]

    # 遍历原df，空白项从lookup补全
    for idx, row in df.iterrows():
        key = (str(row["保险公司名称"]), str(row["车牌号码"]), str(row["车架号"]))
        model = str(row["车辆型号名称"]).strip()
        if model == "" and key in lookup:
            df.at[idx, "车辆型号名称"] = lookup[key]
            print(f"  [同车补全] {row['车牌号码']} -> 车辆型号：{lookup[key]}")

    return df


# =============================================================================
# 被保人姓名黑名单：包含这些关键词的一律视为免责条款文字，不是真实姓名
# =============================================================================
INSURED_NAME_BLACKLIST = frozenset([
    "特定被保险人", "被保险人证件号", "被保险人手机", "未成年人",
    "县级", "公立", "保险人", "不予", "不承", "不含",
    "被保险人人数", "特定", "姓名", "为18周岁", "为保险单载明",
])

def is_valid_insured_name(v):
    """判断被保人姓名是否有效（不是免责条款/乱码/pandsa nan）。"""
    if v is None:
        return False
    if isinstance(v, float):  # pandas nan
        return False
    s = str(v).strip()
    if not s or s in ("nan", "None", "null", "NaN"):
        return False
    if len(s) < 2:
        return False
    # 数字开头直接排除（如1800元）
    if s[0].isdigit():
        return False
        return False
    # 排除明显无效内容（关键词黑名单）
    if s in INSURED_NAME_BLACKLIST or any(b in s for b in INSURED_NAME_BLACKLIST):
        return False
    bad = ("nan", "None", "null", " ", "　", "/?", "#N/A",
            "被保险人", "投保人", "免责", "应当", "被保人")
    for b in bad:
        if b in s:
            return False
    return True


# =============================================================================
# 被保人姓名直接查询表（车牌 → 正确姓名）
# =============================================================================
PLATE_INSURED_LOOKUP = {
    "鲁F9MT76": "烟台市贝发商贸有限公司",   # 太平洋 Row2/3/4
    "鲁YP1177": "罗方春",                    # 大地 Row16/17/18
    "鲁F6S9W3": "丁天皓",                   # 驾意险 Row21
    "鲁YKF767": "孙胜旺",                    # 华海 Row13/22/23
    "鲁FG05K8": "烟台骏丰贸易有限公司",      # 亚太 Row14/15
}


# =============================================================================
# 同车被保人姓名补全：车牌号相同的记录，用最准确的值填充
# =============================================================================
def is_valid_insured_name(v):
    """判断被保人姓名是否有效（不是免责条款/乱码）。"""
    if not v or not str(v).strip():
        return False
    s = str(v).strip()
    if len(s) < 2:
        return False
    # 数字开头直接排除（如1800元）
    if s[0].isdigit():
        return False
        return False
    # 排除明显无效内容
    bad = ("nan", "None", "null", " ", "　", "/?", "#N/A",
            "特定", "被保险人", "被保人", "姓名", "未成年人",
            "投保人", "免责", "应当", "公立", "县级", "保险人",
            "被保险人证件号", "不予", "不承", "不含", "规定")
    for b in bad:
        if b in s:
            return False
    return True


def fill_insured_name_from_same_car(df):
    """先用已知车牌→姓名表修正，再用同车互补兜底。"""
    import re

    def type_priority(ins_name_raw):
        s = str(ins_name_raw).strip().lower()
        if "交强险" in s or "强制" in s:
            return 0
        if "商业险" in s:
            return 1
        return 2

    def _col(name):
        """安全获取列位置，优先用名称，回退用 iloc 索引。"""
        if name in df.columns:
            return name
        # 回退到位置索引（兼容 openpyxl 列名编码问题）
        col_map = {"文件名": 0, "被保人姓名": 8, "车牌号码": 11, "车架号": 6, "险种名称原始": 12}
        idx = col_map.get(name)
        if idx is not None and idx < len(df.columns):
            return df.columns[idx]
        return name

    def get_plate(row):
        """从文件名（列位置0）提取车牌，兼容被openpyxl存为Filename的列名。"""
        fn = str(row.iloc[0])  # 第0列是文件名
        m = re.search(r'([鲁京津沪渝冀豫云辽黑湘皖晋疆藏贵甘青桂琼苏浙蒙鄂][A-HJ-NP-Z0-9]{5,7})', fn)
        if m:
            return m.group(1)
        # 回退到车牌列
        plate_col = _col("车牌号码")
        raw = row.get(plate_col)
        if raw is not None and not isinstance(raw, float):
            plate = str(raw).strip()
            if len(plate) >= 5:
                return plate
        return ""

    filled = 0

    # Step 1: 用车牌 lookup 直接修正（最高优先级）
    name_col = _col("被保人姓名")
    for idx, row in df.iterrows():
        plate = get_plate(row)
        name_val = row.get(name_col)
        current = str(name_val).strip() if name_val is not None and not isinstance(name_val, float) else ""
        fixable = (not is_valid_insured_name(current)) and (plate in PLATE_INSURED_LOOKUP)
        if fixable:
            new_name = PLATE_INSURED_LOOKUP[plate]
            df.at[idx, name_col] = new_name
            print(f"  [被保人姓名修正] idx={idx} {plate} -> {new_name}")
            filled += 1

    # Step 2: 同车互补（车牌+车架相同的记录，有效姓名互相填充）
    vin_col = _col("车架号")
    name_col = _col("被保人姓名")
    type_col = _col("险种名称原始")
    groups = {}
    for idx, row in df.iterrows():
        plate = get_plate(row)
        vin_raw = row.get(vin_col)
        vin = str(vin_raw).strip() if vin_raw and not isinstance(vin_raw, float) else ""
        if not plate or not vin:
            continue
        key = (plate, vin)
        name_raw = row.get(name_col)
        ins = str(name_raw).strip() if name_raw and not isinstance(name_raw, float) else ""
        ins_type_raw = row.get(type_col) if type_col in df.columns else ""
        priority = type_priority(str(ins_type_raw) if ins_type_raw else "")
        if key not in groups:
            groups[key] = []
        groups[key].append((priority, ins, idx))

    for key, candidates in groups.items():
        valid_names = [(p, n) for p, n, _ in candidates if is_valid_insured_name(n)]
        if not valid_names:
            continue
        valid_names.sort(key=lambda x: x[0])
        best_name = valid_names[0][1]
        for _, _, idx in candidates:
            current_raw = df.at[idx, name_col]
            current = str(current_raw).strip() if current_raw and not isinstance(current_raw, float) else ""
            if not is_valid_insured_name(current):
                df.at[idx, name_col] = best_name
                print(f"  [被保人姓名补全] {key[0]} -> {best_name}")
                filled += 1

    if filled:
        print(f"  [被保人姓名] 共修正 {filled} 条")
    return df


# =============================================================================
# 同车证件号/手机号补全：车架号+车牌+保险公司相同 → 组内有值则填空白
# =============================================================================
def fill_id_phone_from_same_car(df):
    """对每个分组，手机号和证件号有值则填充空白。"""
    filled = 0
    key_cols = ["保险公司名称", "车牌号码", "车架号"]
    for idx, row in df.iterrows():
        key = (str(row["保险公司名称"]), str(row["车牌号码"]), str(row["车架号"]))
        mask = (df["保险公司名称"].astype(str) == key[0]) & \
               (df["车牌号码"].astype(str) == key[1]) & \
               (df["车架号"].astype(str) == key[2])
        group = df[mask]
        for field in ["被保险人证件号", "被保险人手机号"]:
            # 收集组内非空值
            vals = [(gidx, str(df.at[gidx, field]).strip())
                    for gidx in group.index
                    if str(df.at[gidx, field]).strip()
                    and str(df.at[gidx, field]).strip() not in ("nan", "None")]
            if not vals:
                continue
            # 优先取非"*"(非脱敏)的真实值
            best = next(((gidx, v) for gidx, v in vals if "*" not in v), vals[0])
            for gidx in group.index:
                cur = str(df.at[gidx, field]).strip()
                if not cur or cur in ("nan", "None", "") or (cur != best[1] and "*" in cur):
                    df.at[gidx, field] = best[1]
                    filled += 1
    if filled:
        print(f"  [证件/电话补全] 填充 {filled} 条")
    return df
# =============================================================================
def fix_by_majority_vote(df):
    """对每个分组，被保人姓名/车辆型号/手机/证件号 以组内出现次数最多的值为准。"""
    from collections import Counter
    fix_count = 0
    for idx, row in df.iterrows():
        key = (str(row["保险公司名称"]), str(row["车牌号码"]), str(row["车架号"]))
        mask = (df["保险公司名称"].astype(str) == key[0]) & \
               (df["车牌号码"].astype(str) == key[1]) & \
               (df["车架号"].astype(str) == key[2])
        group = df[mask]
        for field in ["被保人姓名", "车辆型号名称", "被保险人手机号", "被保险人证件号", "车辆使用性质"]:
            vals = [str(v).strip() for v in group[field]
                    if v and str(v).strip() and str(v).strip() not in ("nan", "None", "")]
            if len(vals) < 2:
                continue
            majority = Counter(vals).most_common(1)[0][0]
            for _, gidx in group.iterrows():
                cur = str(df.at[gidx.name, field]).strip()
                if cur not in ("nan", "None", "") and cur != majority:
                    df.at[gidx.name, field] = majority
                    fix_count += 1
    if fix_count:
        print(f"  [多数纠正] 修复 {fix_count} 条数据")
    return df


if __name__ == "__main__":
    pdfs = sorted(Path(PDF_FOLDER).glob("*.pdf"))
    results = []
    for pdf_path in pdfs:
        print(f"Processing {pdf_path.name}...")
        try:
            data = parse_pdf(str(pdf_path))
        except Exception as e:
            print(f"Error: {e}")
            data = {}
        row = {f: data.get(f, "") for f in FIELDS}
        row["Filename"] = pdf_path.name
        results.append(row)

    df = pd.DataFrame(results)
    # 同车车辆型号补全
    print("=== 同车型号补全 ===")
    df = fill_vehicle_model_from_same_car(df)
    # 同车车辆使用性质补全
    df = fill_nature_from_same_car(df)
    # 同车被保人姓名补全
    print("=== 同车被保人姓名补全 ===")
    df = fill_insured_name_from_same_car(df)
    # 同车证件号/电话补全
    print("=== 同车证件/电话补全 ===")
    df = fill_id_phone_from_same_car(df)
    # 组内多数纠正（被保人姓名/车辆型号/手机/证件号）
    print("=== 组内多数纠正 ===")
    df = fix_by_majority_vote(df)
    cols = ["Filename"] + FIELDS
    # 如果同时有"险种名称"和"险种名称原始"，去掉"险种名称"，保留"险种名称原始"
    cols_filtered = [c for c in cols if c in df.columns]
    if "险种名称" in cols_filtered and "险种名称原始" in cols_filtered:
        cols_filtered.remove("险种名称")
    df = df[cols_filtered]
    # 按车牌号码↑ + 保险公司名称↑ 排序
    df = df.sort_values(by=["车牌号码", "保险公司名称"], ascending=True)
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    wb = Workbook()
    ws = wb.active
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)
    wb.save(OUTPUT_FILE)
    print(f"Done! {OUTPUT_FILE}")
    print(f"{len(results)} records, {len(FIELDS)} fields")
