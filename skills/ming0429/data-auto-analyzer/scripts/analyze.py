"""
广告数据分析脚本 - ad-analyzer-yima v2.0
生成交互式 HTML 报告（ECharts 图表 + 可分页表格）
用法: python3 analyze.py --file report.xlsx --out ./report.html
"""
import sys
import os
import argparse
import json
import warnings
import html as html_mod

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np


# ── 读取文件 ──────────────────────────────────────────────────────
def load_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm"):
        df = pd.read_excel(path, engine="openpyxl")
    elif ext == ".xls":
        df = pd.read_excel(path, engine="xlrd")
    elif ext == ".csv":
        df = None
        for enc in ("utf-8", "utf-8-sig", "gbk", "gb2312"):
            try:
                df = pd.read_csv(path, encoding=enc)
                break
            except Exception:
                continue
        if df is None:
            raise ValueError(f"无法读取 CSV: {path}")
    else:
        raise ValueError(f"不支持的格式: {ext}")

    # 清除汇总/合计/总计 行
    return _drop_summary_rows(df)


def _drop_summary_rows(df):
    """识别并剔除报表中的汇总/合计/总计/平均行。
    规则：某一行的任意一个字符串单元格的值是 '汇总'/'合计'/'总计'/'小计'/'平均'/'total'/'sum'/'summary'/'avg'/'average' 等"""
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
            # 也检查字段值本身是不是"N个逗号分隔的名字"（疑似合计）
            # 若含超过 5 个逗号且无空格后空格模式，很可能是堆叠的维度值
            if s.count(",") >= 5 and len(s) > 20 and " " not in s:
                return True
        return False

    before = len(df)
    mask = df.apply(is_summary_row, axis=1)
    if mask.any():
        df = df[~mask].reset_index(drop=True)
        print(f"  [自动清理] 移除 {before - len(df)} 行汇总/合计类数据")
    return df


# ── 自动识别列类型 ────────────────────────────────────────────────
def _looks_like_date_name(col_name):
    """列名看起来像日期列吗？"""
    s = str(col_name).lower()
    keywords = ["日期", "时间", "date", "time", "day", "month", "year", "周", "月", "年"]
    return any(k in s for k in keywords)


def _looks_like_id_name(col_name):
    """列名看起来像ID/排名等不应作为指标的列吗？"""
    s = str(col_name).lower().strip()
    # 完全匹配的 ID 类
    exact = {"排名", "序号", "编号", "id", "rank", "no", "no.", "#"}
    if s in exact:
        return True
    # 包含匹配
    keywords = ["排名", "序号", "编号", "rank no."]
    return any(s == k or s.endswith(k) for k in keywords)


def detect_columns(df):
    date_col = None
    dim_cols = []
    metric_cols = []

    for col in df.columns:
        series = df[col].copy()
        col_name_str = str(col)

        # 1. ID/排名类列 → 维度（即便是数字也不当指标）
        if _looks_like_id_name(col_name_str):
            dim_cols.append(col)
            continue

        # 2. 日期识别：必须同时满足
        #    (a) 列名含日期关键词，或 (b) 列本身是 datetime 类型
        #    不对纯数字列做 to_datetime（避免数字被当成 Unix 时间戳）
        is_already_datetime = pd.api.types.is_datetime64_any_dtype(series)
        if date_col is None and (is_already_datetime or _looks_like_date_name(col_name_str)):
            try:
                # 对非数字列才尝试解析
                if not pd.api.types.is_numeric_dtype(series):
                    converted = pd.to_datetime(series, errors="coerce")
                    if converted.notna().sum() > len(df) * 0.5:
                        date_col = col
                        df[col] = converted
                        continue
                elif is_already_datetime:
                    date_col = col
                    continue
            except Exception:
                pass

        # 3. 数值列识别（处理千分位逗号和百分号）
        cleaned = series.astype(str).str.replace(",", "").str.replace("%", "").str.strip()
        numeric = pd.to_numeric(cleaned, errors="coerce")
        if numeric.notna().sum() >= len(df) * 0.6:
            df[col] = numeric
            metric_cols.append(col)
        else:
            dim_cols.append(col)

    return date_col, dim_cols, metric_cols


# ── 异常检测 ──────────────────────────────────────────────────────
def detect_anomalies(df, metric_cols):
    anomalies = []
    for col in metric_cols:
        mean_v = df[col].mean()
        std_v = df[col].std()
        if std_v == 0 or pd.isna(std_v):
            continue
        high = df[df[col] > mean_v + 2 * std_v]
        low = df[(df[col] < mean_v - 2 * std_v) & (mean_v > 0)]
        if len(high):
            anomalies.append({
                "type": "high",
                "col": str(col),
                "count": int(len(high)),
                "mean": round(float(mean_v), 2),
                "threshold": round(float(mean_v + 2 * std_v), 2),
            })
        if len(low):
            anomalies.append({
                "type": "low",
                "col": str(col),
                "count": int(len(low)),
                "mean": round(float(mean_v), 2),
                "threshold": round(float(mean_v - 2 * std_v), 2),
            })
    return anomalies


# ── 优化建议 ──────────────────────────────────────────────────────
def get_suggestions(df, metric_cols, dim_cols):
    suggestions = []
    if not dim_cols:
        suggestions.append("建议数据中包含分类/分组维度列（如类别、部门、渠道等），便于深入对比分析")
        return suggestions
    main_dim = _pick_main_dim(df, dim_cols)
    if main_dim is None:
        return suggestions
    grouped = df.groupby(main_dim)[metric_cols].sum()
    first = metric_cols[0]
    best = grouped[first].idxmax()
    worst = grouped[first].idxmin()
    best_val = grouped.loc[best, first]
    worst_val = grouped.loc[worst, first]
    suggestions.append(f"【{first}】最高的 {main_dim}: {best}（{best_val:,.2f}）")
    suggestions.append(f"【{first}】最低的 {main_dim}: {worst}（{worst_val:,.2f}）")
    if len(metric_cols) >= 2:
        second = metric_cols[1]
        ratio = grouped[first] / grouped[second].replace(0, float("nan"))
        if ratio.notna().any():
            best_r = ratio.idxmax()
            suggestions.append(f"【{first}/{second}】比值最高: {best_r}（{ratio[best_r]:.3f}）")
    suggestions.append(f"建议重点关注【{best}】的成功因素，针对【{worst}】进行分析改进")
    return suggestions


# ── 准备图表数据 ──────────────────────────────────────────────────
def _pick_main_dim(df, dim_cols):
    """从维度列中选一个最适合作为分组主维度的。
    优先级：排除 ID/排名类 > 唯一值数量多的（但不超过行数） > 非数字列"""
    if not dim_cols:
        return None
    candidates = []
    for col in dim_cols:
        # 排除 ID/排名类
        if _looks_like_id_name(str(col)):
            continue
        unique_count = df[col].nunique()
        # 唯一值为1或等于行数的列对分组没意义
        if unique_count <= 1:
            continue
        # 评分：唯一值越多越好，但不能太离散（接近行数说明每行都不同）
        ratio = unique_count / len(df)
        score = unique_count
        # 如果唯一值数量 == 行数（完全唯一），且行数较大，说明每行一个实体，适合做分组
        if ratio == 1.0:
            score = unique_count  # 每行一个值，直接用
        candidates.append((score, col))

    if not candidates:
        # 退而求其次：取 dim_cols[0]
        return dim_cols[0]
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]


def prepare_chart_data(df, metric_cols, dim_cols, date_col):
    charts = {}

    # 1. 指标总量柱状图
    totals = df[metric_cols].sum()
    charts["totals"] = {
        "labels": [str(c) for c in totals.index],
        "values": [round(float(v), 2) for v in totals.values],
    }

    # 选一个有意义的主维度（排除排名/ID等列）
    main_dim = _pick_main_dim(df, dim_cols)

    # 2. 维度对比
    if main_dim is not None:
        grouped = (
            df.groupby(main_dim)[metric_cols]
            .sum()
            .sort_values(metric_cols[0], ascending=False)
            .head(15)
        )
        show_metrics = metric_cols[:4]
        charts["dim_compare"] = {
            "dim_name": str(main_dim),
            "labels": [str(x) for x in grouped.index],
            "series": [],
        }
        for col in show_metrics:
            charts["dim_compare"]["series"].append({
                "name": str(col),
                "values": [round(float(v), 2) for v in grouped[col].values],
            })

    # 3. 趋势折线图
    if date_col is not None:
        df2 = df.copy()
        df2[date_col] = pd.to_datetime(df2[date_col], errors="coerce")
        df2 = df2.dropna(subset=[date_col])
        daily = df2.groupby(date_col)[metric_cols].sum().sort_index()
        show_metrics = metric_cols[:5]
        charts["trend"] = {
            "dates": [d.strftime("%Y-%m-%d") for d in daily.index],
            "series": [],
        }
        for col in show_metrics:
            charts["trend"]["series"].append({
                "name": str(col),
                "values": [round(float(v), 2) for v in daily[col].values],
            })

    # 4. 饼图
    if main_dim is not None:
        grouped_pie = df.groupby(main_dim)[metric_cols[0]].sum().sort_values(ascending=False)
        top = grouped_pie.head(10)
        others = grouped_pie.iloc[10:].sum() if len(grouped_pie) > 10 else 0
        pie_data = [{"name": str(k), "value": round(float(v), 2)} for k, v in top.items()]
        if others > 0:
            pie_data.append({"name": "其他", "value": round(float(others), 2)})
        charts["pie"] = {
            "metric_name": str(metric_cols[0]),
            "dim_name": str(main_dim),
            "data": pie_data,
        }

    # 5. 相关性热力图
    if len(metric_cols) >= 3:
        corr = df[metric_cols].corr()
        labels = [str(c) for c in corr.columns]
        data = []
        for i, row_label in enumerate(labels):
            for j, col_label in enumerate(labels):
                data.append([i, j, round(float(corr.iloc[i, j]), 2)])
        charts["heatmap"] = {
            "labels": labels,
            "data": data,
        }

    return charts


# ── 准备表格数据 ──────────────────────────────────────────────────
def prepare_table_data(df, date_col):
    df_display = df.copy()
    if date_col and date_col in df_display.columns:
        df_display[date_col] = df_display[date_col].astype(str).str[:10]

    columns = [str(c) for c in df_display.columns]
    rows = []
    for _, row in df_display.iterrows():
        r = []
        for val in row.values:
            if pd.isna(val):
                r.append("")
            elif isinstance(val, float):
                r.append(round(val, 4))
            else:
                r.append(str(val))
        rows.append(r)
    return columns, rows


# ── 汇总指标 ──────────────────────────────────────────────────────
def get_summary_stats(df, metric_cols):
    stats = []
    for col in metric_cols:
        stats.append({
            "name": str(col),
            "sum": round(float(df[col].sum()), 2),
            "mean": round(float(df[col].mean()), 2),
            "max": round(float(df[col].max()), 2),
            "min": round(float(df[col].min()), 2),
        })
    return stats


# ── 生成 HTML 报告 ────────────────────────────────────────────────
def generate_html(report_data):
    html_template = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>数据分析报告</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js"></script>
<style>
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
    --gradient-2: linear-gradient(135deg, #22c493 0%, #22d3ee 100%);
    --gradient-3: linear-gradient(135deg, #f5a623 0%, #f25757 100%);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
  }

  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 32px 24px;
  }

  /* Header */
  .header {
    text-align: center;
    margin-bottom: 40px;
    padding: 48px 24px;
    background: linear-gradient(180deg, rgba(78,124,255,0.08) 0%, transparent 100%);
    border-bottom: 1px solid var(--border);
  }
  .header h1 {
    font-size: 2rem;
    font-weight: 700;
    background: var(--gradient-1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
    letter-spacing: -0.02em;
  }
  .header .subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
  }

  /* Section title */
  .section-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin: 40px 0 20px;
    padding-left: 14px;
    border-left: 3px solid var(--accent-blue);
    color: var(--text-primary);
  }

  /* Overview cards */
  .overview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
  }
  .ov-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    transition: background 0.2s, border-color 0.2s;
  }
  .ov-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--accent-blue);
  }
  .ov-card .label {
    font-size: 0.8rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
  }
  .ov-card .value {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text-primary);
  }
  .ov-card .sub {
    font-size: 0.78rem;
    color: var(--text-dim);
    margin-top: 4px;
  }

  /* Stats table */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 14px;
    margin-bottom: 32px;
  }
  .stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
  }
  .stat-card .stat-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--accent-blue);
    margin-bottom: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .stat-card .stat-row {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 0.82rem;
  }
  .stat-card .stat-row .lbl { color: var(--text-secondary); }
  .stat-card .stat-row .val { color: var(--text-primary); font-weight: 500; font-variant-numeric: tabular-nums; }

  /* Anomaly & suggestions */
  .info-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
    font-size: 0.88rem;
    line-height: 1.7;
  }
  .info-box.warn { border-left: 3px solid var(--accent-orange); }
  .info-box.ok { border-left: 3px solid var(--accent-green); }
  .info-box.tip { border-left: 3px solid var(--accent-purple); }

  /* Data table */
  .table-wrap {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 32px;
  }
  .table-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
    gap: 10px;
  }
  .table-toolbar .search-box {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 14px;
    color: var(--text-primary);
    font-size: 0.85rem;
    width: 260px;
    outline: none;
    transition: border-color 0.2s;
  }
  .table-toolbar .search-box:focus { border-color: var(--accent-blue); }
  .table-toolbar .page-info { color: var(--text-secondary); font-size: 0.82rem; }

  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }
  .data-table th {
    background: rgba(78,124,255,0.06);
    color: var(--text-secondary);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-size: 0.72rem;
    padding: 12px 16px;
    text-align: left;
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
    position: relative;
    border-bottom: 1px solid var(--border);
  }
  .data-table th:hover { color: var(--accent-blue); }
  .data-table th .sort-icon { margin-left: 4px; opacity: 0.4; }
  .data-table th.sorted .sort-icon { opacity: 1; color: var(--accent-blue); }
  .data-table td {
    padding: 10px 16px;
    border-bottom: 1px solid rgba(42,46,66,0.5);
    color: var(--text-primary);
    white-space: nowrap;
    max-width: 260px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .data-table tr:hover td { background: rgba(78,124,255,0.03); }
  .table-container { overflow-x: auto; }

  .pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 6px;
    padding: 16px;
    border-top: 1px solid var(--border);
  }
  .pagination button {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.82rem;
    transition: all 0.2s;
  }
  .pagination button:hover { border-color: var(--accent-blue); color: var(--accent-blue); }
  .pagination button.active { background: var(--accent-blue); border-color: var(--accent-blue); color: #fff; }
  .pagination button:disabled { opacity: 0.3; cursor: not-allowed; }

  /* Charts */
  .chart-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin-bottom: 32px;
  }
  .chart-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }
  .chart-card.full { grid-column: 1 / -1; }
  .chart-box { width: 100%; height: 420px; }

  /* Footer */
  .footer {
    text-align: center;
    padding: 32px;
    color: var(--text-dim);
    font-size: 0.78rem;
    border-top: 1px solid var(--border);
    margin-top: 40px;
  }

  @media (max-width: 768px) {
    .chart-grid { grid-template-columns: 1fr; }
    .container { padding: 16px 12px; }
    .header h1 { font-size: 1.5rem; }
    .overview-grid { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>

<div class="header">
  <h1>数据分析报告</h1>
  <p class="subtitle">{{FILE_NAME}} · 共 {{TOTAL_ROWS}} 行 × {{TOTAL_COLS}} 列</p>
</div>

<div class="container">

  <!-- 数据概览 -->
  <h2 class="section-title">数据概览</h2>
  <div class="overview-grid" id="overview-grid"></div>

  <!-- 核心指标汇总 -->
  <h2 class="section-title">核心指标汇总</h2>
  <div class="stats-grid" id="stats-grid"></div>

  <!-- 异常检测 -->
  <h2 class="section-title">异常检测</h2>
  <div id="anomaly-box"></div>

  <!-- 优化建议 -->
  <h2 class="section-title">优化建议</h2>
  <div id="suggestion-box"></div>

  <!-- 数据表格 -->
  <h2 class="section-title">明细数据</h2>
  <div class="table-wrap">
    <div class="table-toolbar">
      <input class="search-box" id="search-input" placeholder="搜索数据..." oninput="filterTable()">
      <span class="page-info" id="page-info"></span>
    </div>
    <div class="table-container">
      <table class="data-table" id="data-table">
        <thead id="table-head"></thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
    <div class="pagination" id="pagination"></div>
  </div>

  <!-- 图表区域 -->
  <h2 class="section-title">数据可视化</h2>
  <div class="chart-grid" id="chart-grid"></div>

</div>

<div class="footer">
  Generated by data-auto-analyzer v2.0 · Data processed locally
</div>

<script>
// ===== 报告数据 =====
const REPORT = {{REPORT_JSON}};

const PAGE_SIZE = 20;
let currentPage = 1;
let sortCol = -1;
let sortAsc = true;
let filteredRows = [...REPORT.rows];

const COLORS = ['#4e7cff','#22c493','#f5a623','#f25757','#9370ff','#22d3ee','#ff6b9d','#67e8f9'];

// ===== 格式化数字 =====
function fmt(n) {
  if (n === '' || n === null || n === undefined) return '-';
  if (typeof n === 'string') return n;
  if (Math.abs(n) >= 1e8) return (n / 1e8).toFixed(2) + '亿';
  if (Math.abs(n) >= 1e4) return (n / 1e4).toFixed(2) + '万';
  if (Number.isInteger(n)) return n.toLocaleString();
  return n.toLocaleString(undefined, {maximumFractionDigits: 2});
}

// ===== 概览卡片 =====
function renderOverview() {
  const g = document.getElementById('overview-grid');
  const cards = [
    { label: '数据行数', value: REPORT.total_rows, sub: '条记录' },
    { label: '数据列数', value: REPORT.total_cols, sub: `维度: ${REPORT.dim_cols.length} · 指标: ${REPORT.metric_cols.length}` },
    { label: '日期列', value: REPORT.date_col || '未识别', sub: REPORT.date_range || '' },
    { label: '维度列', value: REPORT.dim_cols.length ? REPORT.dim_cols.join(', ') : '无', sub: '' },
  ];
  g.innerHTML = cards.map(c => `
    <div class="ov-card">
      <div class="label">${c.label}</div>
      <div class="value">${c.value}</div>
      <div class="sub">${c.sub}</div>
    </div>`).join('');
}

// ===== 指标汇总 =====
function renderStats() {
  const g = document.getElementById('stats-grid');
  g.innerHTML = REPORT.summary_stats.map(s => `
    <div class="stat-card">
      <div class="stat-name">${s.name}</div>
      <div class="stat-row"><span class="lbl">合计</span><span class="val">${fmt(s.sum)}</span></div>
      <div class="stat-row"><span class="lbl">均值</span><span class="val">${fmt(s.mean)}</span></div>
      <div class="stat-row"><span class="lbl">最大值</span><span class="val">${fmt(s.max)}</span></div>
      <div class="stat-row"><span class="lbl">最小值</span><span class="val">${fmt(s.min)}</span></div>
    </div>`).join('');
}

// ===== 异常检测 =====
function renderAnomalies() {
  const box = document.getElementById('anomaly-box');
  if (!REPORT.anomalies.length) {
    box.innerHTML = '<div class="info-box ok">✅ 未发现明显异常波动，各指标数据在正常范围内</div>';
    return;
  }
  box.innerHTML = REPORT.anomalies.map(a => {
    const icon = a.type === 'high' ? '📈' : '📉';
    const label = a.type === 'high' ? '异常高值' : '异常低值';
    return `<div class="info-box warn">${icon} 【${a.col}】${label} ${a.count} 行 · 均值 ${fmt(a.mean)} · 阈值 ${fmt(a.threshold)}</div>`;
  }).join('');
}

// ===== 优化建议 =====
function renderSuggestions() {
  const box = document.getElementById('suggestion-box');
  box.innerHTML = REPORT.suggestions.map(s =>
    `<div class="info-box tip">💡 ${s}</div>`
  ).join('');
}

// ===== 数据表格 =====
function renderTableHead() {
  const thead = document.getElementById('table-head');
  thead.innerHTML = '<tr>' + REPORT.columns.map((c, i) =>
    `<th onclick="sortTable(${i})" data-col="${i}"><span>${c}</span><span class="sort-icon">↕</span></th>`
  ).join('') + '</tr>';
}

function renderTableBody() {
  const tbody = document.getElementById('table-body');
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageRows = filteredRows.slice(start, start + PAGE_SIZE);
  tbody.innerHTML = pageRows.map(row =>
    '<tr>' + row.map(v => `<td title="${v}">${typeof v === 'number' ? fmt(v) : v}</td>`).join('') + '</tr>'
  ).join('');

  document.getElementById('page-info').textContent =
    `显示 ${start + 1}-${Math.min(start + PAGE_SIZE, filteredRows.length)} / 共 ${filteredRows.length} 条`;
  renderPagination();
}

function renderPagination() {
  const box = document.getElementById('pagination');
  const totalPages = Math.ceil(filteredRows.length / PAGE_SIZE);
  if (totalPages <= 1) { box.innerHTML = ''; return; }

  let btns = [];
  btns.push(`<button onclick="goPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>‹ 上一页</button>`);

  let pages = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages = [1];
    if (currentPage > 3) pages.push('...');
    for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) pages.push(i);
    if (currentPage < totalPages - 2) pages.push('...');
    pages.push(totalPages);
  }

  pages.forEach(p => {
    if (p === '...') btns.push('<span style="color:var(--text-dim);padding:0 4px">…</span>');
    else btns.push(`<button class="${p === currentPage ? 'active' : ''}" onclick="goPage(${p})">${p}</button>`);
  });

  btns.push(`<button onclick="goPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>下一页 ›</button>`);
  box.innerHTML = btns.join('');
}

function goPage(p) {
  const totalPages = Math.ceil(filteredRows.length / PAGE_SIZE);
  if (p < 1 || p > totalPages) return;
  currentPage = p;
  renderTableBody();
}

function sortTable(colIdx) {
  if (sortCol === colIdx) { sortAsc = !sortAsc; }
  else { sortCol = colIdx; sortAsc = true; }

  filteredRows.sort((a, b) => {
    let va = a[colIdx], vb = b[colIdx];
    if (va === '' || va === null) return 1;
    if (vb === '' || vb === null) return -1;
    if (typeof va === 'number' && typeof vb === 'number') return sortAsc ? va - vb : vb - va;
    return sortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
  });

  document.querySelectorAll('.data-table th').forEach((th, i) => {
    th.classList.toggle('sorted', i === colIdx);
    th.querySelector('.sort-icon').textContent = i === colIdx ? (sortAsc ? '↑' : '↓') : '↕';
  });

  currentPage = 1;
  renderTableBody();
}

function filterTable() {
  const q = document.getElementById('search-input').value.toLowerCase();
  if (!q) { filteredRows = [...REPORT.rows]; }
  else {
    filteredRows = REPORT.rows.filter(row =>
      row.some(v => String(v).toLowerCase().includes(q))
    );
  }
  currentPage = 1;
  renderTableBody();
}

// ===== ECharts 图表 =====
function renderCharts() {
  const grid = document.getElementById('chart-grid');
  const charts = REPORT.charts;
  let html = '';

  // 1. 指标总量柱状图
  if (charts.totals) {
    html += '<div class="chart-card"><div class="chart-box" id="chart-totals"></div></div>';
  }

  // 2. 饼图
  if (charts.pie) {
    html += '<div class="chart-card"><div class="chart-box" id="chart-pie"></div></div>';
  }

  // 3. 趋势折线图 - 每个指标独立一个图
  if (charts.trend) {
    charts.trend.series.forEach((s, i) => {
      html += `<div class="chart-card"><div class="chart-box" id="chart-trend-${i}"></div></div>`;
    });
  }

  // 4. 维度对比
  if (charts.dim_compare) {
    html += '<div class="chart-card full"><div class="chart-box" id="chart-dim"></div></div>';
  }

  // 5. 热力图
  if (charts.heatmap) {
    html += '<div class="chart-card full"><div class="chart-box" id="chart-heatmap"></div></div>';
  }

  grid.innerHTML = html;

  // 初始化 ECharts
  setTimeout(() => {
    initTotalsChart(charts.totals);
    initPieChart(charts.pie);
    initTrendChart(charts.trend);
    initDimChart(charts.dim_compare);
    initHeatmapChart(charts.heatmap);
  }, 100);
}

function ecOption(overrides) {
  return Object.assign({
    backgroundColor: 'transparent',
    textStyle: { color: '#8b90a5', fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' },
    tooltip: { backgroundColor: '#1a1d2e', borderColor: '#2a2e42', textStyle: { color: '#e8eaf0', fontSize: 12 } },
  }, overrides);
}

function initTotalsChart(data) {
  if (!data) return;
  const el = document.getElementById('chart-totals');
  if (!el) return;
  const chart = echarts.init(el);
  chart.setOption(ecOption({
    title: { text: '各指标总量', left: 'center', textStyle: { color: '#e8eaf0', fontSize: 15, fontWeight: 600 } },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.labels, axisLabel: { color: '#8b90a5', rotate: 20, fontSize: 11 }, axisLine: { lineStyle: { color: '#2a2e42' } } },
    yAxis: { type: 'value', axisLabel: { color: '#8b90a5', fontSize: 11 }, splitLine: { lineStyle: { color: '#2a2e42' } } },
    series: [{ type: 'bar', data: data.values.map((v, i) => ({ value: v, itemStyle: { color: COLORS[i % COLORS.length], borderRadius: [4,4,0,0] } })),
      label: { show: true, position: 'top', color: '#8b90a5', fontSize: 10, formatter: p => fmt(p.value) },
      barMaxWidth: 50 }],
    grid: { top: 60, bottom: 40, left: 60, right: 20 },
  }));
  window.addEventListener('resize', () => chart.resize());
}

function initPieChart(data) {
  if (!data) return;
  const el = document.getElementById('chart-pie');
  if (!el) return;
  const chart = echarts.init(el);
  chart.setOption(ecOption({
    title: { text: `【${data.dim_name}】${data.metric_name} 占比`, left: 'center', textStyle: { color: '#e8eaf0', fontSize: 15, fontWeight: 600 } },
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { type: 'scroll', bottom: 10, textStyle: { color: '#8b90a5', fontSize: 11 } },
    color: COLORS,
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '48%'],
      data: data.data,
      label: { color: '#8b90a5', fontSize: 11 },
      emphasis: { label: { fontSize: 14, fontWeight: 'bold' }, itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,0,0,0.3)' } },
      itemStyle: { borderRadius: 6, borderColor: '#1a1d2e', borderWidth: 2 },
    }],
  }));
  window.addEventListener('resize', () => chart.resize());
}

function initTrendChart(data) {
  if (!data) return;
  data.series.forEach((s, i) => {
    const el = document.getElementById(`chart-trend-${i}`);
    if (!el) return;
    const color = COLORS[i % COLORS.length];
    const chart = echarts.init(el);
    chart.setOption(ecOption({
      title: { text: `${s.name} 趋势`, left: 'center', textStyle: { color: '#e8eaf0', fontSize: 14, fontWeight: 600 } },
      tooltip: { trigger: 'axis', formatter: params => {
        const p = params[0];
        return `${p.axisValue}<br/><span style="color:${color}">●</span> ${s.name}: <b>${fmt(p.value)}</b>`;
      }},
      color: [color],
      xAxis: { type: 'category', data: data.dates, axisLabel: { color: '#8b90a5', rotate: 30, fontSize: 10 }, axisLine: { lineStyle: { color: '#2a2e42' } }, boundaryGap: false },
      yAxis: { type: 'value', axisLabel: { color: '#8b90a5', fontSize: 10, formatter: v => fmt(v) }, splitLine: { lineStyle: { color: '#2a2e42' } } },
      series: [{
        name: s.name, type: 'line', data: s.values, smooth: true, symbol: 'circle', symbolSize: 4,
        lineStyle: { width: 2.5 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: color + '30' },
          { offset: 1, color: color + '05' }
        ])},
      }],
      grid: { top: 50, bottom: 80, left: 65, right: 20 },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }, { type: 'slider', bottom: 10, height: 20, borderColor: '#2a2e42', fillerColor: 'rgba(78,124,255,0.15)', handleStyle: { color: '#4e7cff' }, textStyle: { color: '#8b90a5', fontSize: 10 } }],
    }));
    window.addEventListener('resize', () => chart.resize());
  });
}

function initDimChart(data) {
  if (!data) return;
  const el = document.getElementById('chart-dim');
  if (!el) return;
  const chart = echarts.init(el);
  chart.setOption(ecOption({
    title: { text: `按【${data.dim_name}】分组对比`, left: 'center', textStyle: { color: '#e8eaf0', fontSize: 15, fontWeight: 600 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: data.series.map(s => s.name), bottom: 10, textStyle: { color: '#8b90a5', fontSize: 11 } },
    color: COLORS,
    xAxis: { type: 'category', data: data.labels, axisLabel: { color: '#8b90a5', rotate: 30, fontSize: 10, interval: 0 }, axisLine: { lineStyle: { color: '#2a2e42' } } },
    yAxis: { type: 'value', axisLabel: { color: '#8b90a5', fontSize: 10 }, splitLine: { lineStyle: { color: '#2a2e42' } } },
    series: data.series.map(s => ({
      name: s.name, type: 'bar', data: s.values,
      barMaxWidth: 30, itemStyle: { borderRadius: [3,3,0,0] },
    })),
    grid: { top: 60, bottom: 60, left: 60, right: 20 },
  }));
  window.addEventListener('resize', () => chart.resize());
}

function initHeatmapChart(data) {
  if (!data) return;
  const el = document.getElementById('chart-heatmap');
  if (!el) return;
  const chart = echarts.init(el);
  chart.setOption(ecOption({
    title: { text: '指标相关性热力图', left: 'center', textStyle: { color: '#e8eaf0', fontSize: 15, fontWeight: 600 } },
    tooltip: { formatter: p => `${data.labels[p.data[0]]} ↔ ${data.labels[p.data[1]]}<br/>相关系数: ${p.data[2]}` },
    xAxis: { type: 'category', data: data.labels, axisLabel: { color: '#8b90a5', fontSize: 10, rotate: 30 }, axisLine: { lineStyle: { color: '#2a2e42' } } },
    yAxis: { type: 'category', data: data.labels, axisLabel: { color: '#8b90a5', fontSize: 10 }, axisLine: { lineStyle: { color: '#2a2e42' } } },
    visualMap: { min: -1, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: 10,
      inRange: { color: ['#f25757', '#2a2e42', '#22c493'] }, textStyle: { color: '#8b90a5' } },
    series: [{ type: 'heatmap', data: data.data, label: { show: true, color: '#e8eaf0', fontSize: 11 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } } }],
    grid: { top: 60, bottom: 80, left: 100, right: 20 },
  }));
  window.addEventListener('resize', () => chart.resize());
}

// ===== 初始化 =====
renderOverview();
renderStats();
renderAnomalies();
renderSuggestions();
renderTableHead();
renderTableBody();
renderCharts();
</script>
</body>
</html>"""
    return html_template


# ── 主入口 ────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="广告数据分析工具 v2.0")
    parser.add_argument("--file", required=True, help="报表文件路径 (.xlsx/.xls/.csv)")
    parser.add_argument("--out", default="./ad_report.html", help="输出 HTML 文件路径")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        sys.exit(1)

    print(f"\n正在读取: {args.file}")
    df = load_file(args.file)
    print(f"读取成功，共 {len(df)} 行 × {len(df.columns)} 列")

    date_col, dim_cols, metric_cols = detect_columns(df)

    if not metric_cols:
        print("❌ 未找到数值列，请确认文件中包含数字数据")
        sys.exit(1)

    print(f"日期列: {date_col or '未识别'}")
    print(f"维度列: {', '.join(str(c) for c in dim_cols) or '无'}")
    print(f"指标列: {', '.join(str(c) for c in metric_cols)}")

    # 准备报告数据
    anomalies = detect_anomalies(df, metric_cols)
    suggestions = get_suggestions(df, metric_cols, dim_cols)
    charts = prepare_chart_data(df, metric_cols, dim_cols, date_col)
    columns, rows = prepare_table_data(df, date_col)
    summary_stats = get_summary_stats(df, metric_cols)

    # 日期范围
    date_range = ""
    if date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
        if len(dates):
            date_range = f"{dates.min().strftime('%Y-%m-%d')} ~ {dates.max().strftime('%Y-%m-%d')}"

    report = {
        "file_name": os.path.basename(args.file),
        "total_rows": len(df),
        "total_cols": len(df.columns),
        "date_col": str(date_col) if date_col else None,
        "date_range": date_range,
        "dim_cols": [str(c) for c in dim_cols],
        "metric_cols": [str(c) for c in metric_cols],
        "summary_stats": summary_stats,
        "anomalies": anomalies,
        "suggestions": suggestions,
        "charts": charts,
        "columns": columns,
        "rows": rows,
    }

    # 生成 HTML
    html_content = generate_html(report)
    report_json = json.dumps(report, ensure_ascii=False, default=str)
    html_content = html_content.replace("{{REPORT_JSON}}", report_json)
    html_content = html_content.replace("{{FILE_NAME}}", html_mod.escape(report["file_name"]))
    html_content = html_content.replace("{{TOTAL_ROWS}}", str(report["total_rows"]))
    html_content = html_content.replace("{{TOTAL_COLS}}", str(report["total_cols"]))

    # 确保输出目录存在
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n{'=' * 60}")
    print(f"✅ 分析完成！交互式 HTML 报告已生成")
    print(f"   报告路径: {os.path.abspath(args.out)}")
    print(f"   包含: 数据概览 · 指标汇总 · 异常检测 · 优化建议")
    print(f"         可分页表格 · {len(charts)} 个 ECharts 图表")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
