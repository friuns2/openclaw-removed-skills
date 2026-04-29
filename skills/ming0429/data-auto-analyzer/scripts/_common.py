"""
共享工具模块 - data-auto-analyzer
供 analyze.py / diagnose.py / ab_test.py / daily_report.py 共用
"""
import os
import pandas as pd
import warnings
warnings.filterwarnings("ignore")


def load_file(path):
    """统一读取 xlsx/xls/csv 文件，自动识别编码，自动剔除汇总行"""
    ext = os.path.splitext(path)[1].lower()
    df = None
    if ext in (".xlsx", ".xlsm"):
        df = pd.read_excel(path, engine="openpyxl")
    elif ext == ".xls":
        df = pd.read_excel(path, engine="xlrd")
    elif ext == ".csv":
        for enc in ("utf-8", "utf-8-sig", "gbk", "gb2312"):
            try:
                df = pd.read_csv(path, encoding=enc)
                break
            except Exception:
                continue
    if df is None:
        raise ValueError(f"不支持的格式: {ext}")
    return _drop_summary_rows(df)


def _drop_summary_rows(df):
    """识别并剔除报表中的汇总/合计/总计/小计/平均行"""
    summary_markers = {
        "汇总", "合计", "总计", "小计", "平均", "均值", "求和",
        "total", "sum", "subtotal", "summary", "avg", "average", "mean",
        "总合", "总和"
    }

    def is_summary_row(row):
        for v in row.values:
            if pd.isna(v):
                continue
            s = str(v).strip().lower()
            if s in summary_markers:
                return True
            # 多人名堆叠：超过 5 个逗号且无空格，很可能是汇总行
            if s.count(",") >= 5 and len(s) > 20 and " " not in s:
                return True
        return False

    before = len(df)
    mask = df.apply(is_summary_row, axis=1)
    if mask.any():
        df = df[~mask].reset_index(drop=True)
        print(f"  [自动清理] 移除 {before - len(df)} 行汇总/合计类数据")
    return df


# 常见列名识别规则
COL_KEYWORDS = {
    "cost": ["消耗", "花费", "成本", "费用", "预算", "cost", "spend", "spent"],
    "impression": ["展示", "曝光", "展现", "impression", "show"],
    "click": ["点击", "click", "tap"],
    "conversion": ["转化", "注册", "下单", "成交", "激活", "conversion", "convert"],
    "ctr": ["ctr", "点击率"],
    "cpc": ["cpc", "点击单价"],
    "cpa": ["cpa", "转化成本"],
    "cpm": ["cpm", "千次展示"],
    "revenue": ["收入", "营收", "gmv", "revenue", "income"],
    "roi": ["roi", "roas"],
    "campaign": ["计划", "广告", "campaign", "adgroup", "creative", "ad name", "广告组"],
}


def find_column(df, key, exclude=None):
    """
    在 df.columns 中找关键词对应的列，优先完全匹配，其次部分匹配
    exclude: 已识别的列，避免重复
    """
    exclude = exclude or set()
    keywords = COL_KEYWORDS.get(key, [])

    # 优先：完全匹配（忽略大小写和空格）
    for col in df.columns:
        if col in exclude:
            continue
        col_norm = str(col).lower().strip().replace(" ", "")
        for kw in keywords:
            if col_norm == kw.lower().strip().replace(" ", ""):
                return col

    # 其次：包含匹配
    for col in df.columns:
        if col in exclude:
            continue
        col_norm = str(col).lower().strip()
        for kw in keywords:
            if kw.lower() in col_norm:
                return col

    return None


def auto_detect_columns(df):
    """
    自动识别广告报表中的关键列，返回 dict
    包含: cost/impression/click/conversion/ctr/cpc/cpa/cpm/revenue/roi/campaign
    """
    result = {}
    used = set()
    for key in ["campaign", "cost", "impression", "click", "conversion",
                "ctr", "cpc", "cpa", "cpm", "revenue", "roi"]:
        col = find_column(df, key, exclude=used)
        if col is not None:
            result[key] = col
            used.add(col)
    return result


def to_numeric_safe(series):
    """安全转数值：处理千分位逗号和百分号"""
    cleaned = series.astype(str).str.replace(",", "").str.replace("%", "").str.strip()
    return pd.to_numeric(cleaned, errors="coerce")


def fmt_number(n):
    """格式化数字显示"""
    if pd.isna(n) or n is None:
        return "-"
    if isinstance(n, str):
        return n
    if abs(n) >= 1e8:
        return f"{n / 1e8:.2f}亿"
    if abs(n) >= 1e4:
        return f"{n / 1e4:.2f}万"
    if isinstance(n, float) and not n.is_integer():
        return f"{n:,.2f}"
    return f"{int(n):,}"


def pct_change(new, old):
    """计算环比变化百分比，返回 (百分比, 箭头符号)"""
    if old is None or pd.isna(old) or old == 0:
        return None, "→"
    change = (new - old) / abs(old) * 100
    if abs(change) < 0.5:
        return change, "→"
    return change, "↑" if change > 0 else "↓"


# 通用 HTML 样式（暗色主题）
COMMON_CSS = """
:root {
  --bg-primary: #0f1117;
  --bg-card: #1a1d2e;
  --bg-card-hover: #222640;
  --border: #2a2e42;
  --text-primary: #e8eaf0;
  --text-secondary: #8b90a5;
  --text-dim: #5c6078;
  --accent-blue: #4e7cff;
  --accent-green: #22c493;
  --accent-orange: #f5a623;
  --accent-red: #f25757;
  --accent-purple: #9370ff;
  --accent-cyan: #22d3ee;
  --gradient-1: linear-gradient(135deg, #4e7cff 0%, #9370ff 100%);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  min-height: 100vh;
}
.container { max-width: 1400px; margin: 0 auto; padding: 32px 24px; }
.header {
  text-align: center;
  padding: 48px 24px;
  background: linear-gradient(180deg, rgba(78,124,255,0.08) 0%, transparent 100%);
  border-bottom: 1px solid var(--border);
}
.header h1 {
  font-size: 2rem; font-weight: 700;
  background: var(--gradient-1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
  letter-spacing: -0.02em;
}
.header .subtitle { color: var(--text-secondary); font-size: 0.95rem; }
.section-title {
  font-size: 1.2rem; font-weight: 600;
  margin: 40px 0 20px;
  padding-left: 14px;
  border-left: 3px solid var(--accent-blue);
}
.footer {
  text-align: center; padding: 32px;
  color: var(--text-dim); font-size: 0.78rem;
  border-top: 1px solid var(--border); margin-top: 40px;
}
"""
