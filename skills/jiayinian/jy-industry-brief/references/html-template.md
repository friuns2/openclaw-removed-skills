# HTML 输出模板

## 完整 HTML 模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>行业速报</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }
        h1, h2, h3 {
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        h1 {
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            background: #fff;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        ol {
            padding-left: 20px;
        }
        li {
            margin: 8px 0;
            list-style-type: none;
        }
        li::before {
            content: "① ";
            color: #3498db;
            font-weight: bold;
        }
        li:nth-child(2)::before { content: "② "; }
        li:nth-child(3)::before { content: "③ "; }
        li:nth-child(4)::before { content: "④ "; }
        li:nth-child(5)::before { content: "⑤ "; }
        li:nth-child(6)::before { content: "⑥ "; }
        li:nth-child(7)::before { content: "⑦ "; }
        .disclaimer {
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }
        .source-info {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #6c757d;
        }
        .section {
            margin: 25px 0;
        }
        .date {
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>2026 年 03 月 30 日新能源汽车行业速报</h1>
    
    <div class="section">
        <h2>1. 备选简读素材：</h2>
        <table>
            <thead>
                <tr>
                    <th>序号</th>
                    <th>资讯标题</th>
                    <th>数据来源</th>
                    <th>发布时间</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>新能源汽车电池技术深度分析</td>
                    <td>某券商研究报告</td>
                    <td>2026-03-30</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>全球新能源汽车市场发展趋势</td>
                    <td>行业研究机构</td>
                    <td>2026-03-29</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>2. 重要新闻信息：</h2>
        <ol>
            <li>国家发改委发布新能源汽车产业发展新政策（新华社，2026-03-30）</li>
            <li>2026 年 2 月新能源汽车销量同比增长 35%（中汽协，2026-03-30）</li>
            <li>多省市出台新能源汽车补贴政策（各地政府官网，2026-03-29）</li>
        </ol>
    </div>
    
    <div class="section">
        <h2>3. 行业企业动态：</h2>
        <ol>
            <li>比亚迪发布新一代刀片电池技术（公司官网，2026-03-30）</li>
            <li>特斯拉上海工厂产能提升至新高度（路透社，2026-03-30）</li>
            <li>宁德时代与某车企达成战略合作协议（公司公告，2026-03-29）</li>
            <li>蔚来汽车推出新车型（公司官网，2026-03-29）</li>
            <li>小鹏汽车技术更新动态（公司官网，2026-03-28）</li>
        </ol>
    </div>
    
    <div class="section">
        <h2>4. 投融资事件：</h2>
        <table>
            <thead>
                <tr>
                    <th>被投资方</th>
                    <th>投资方</th>
                    <th>投融资事件</th>
                    <th>发布时间</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>某电池公司</td>
                    <td>某投资机构</td>
                    <td>B 轮融资</td>
                    <td>2026-03-30</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="disclaimer">
        <strong>免责声明</strong>：本速报仅提供信息整理，不构成任何投资建议。市场有风险，决策需谨慎。
    </div>
    
    <div class="source-info">
        <h3>溯源信息</h3>
        <table>
            <thead>
                <tr>
                    <th>数据类型</th>
                    <th>数据来源</th>
                    <th>原始发布日期</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>行业快讯</td>
                    <td>jy-financedata-api.IndustryNewsFlash</td>
                    <td>2026-03-30</td>
                </tr>
                <tr>
                    <td>新闻舆情</td>
                    <td>jy-financedata-api.NewsPublicOpinionList</td>
                    <td>2026-03-30</td>
                </tr>
                <tr>
                    <td>研究报告</td>
                    <td>jy-financedata-tool.FinancialResearchReport</td>
                    <td>2026-03-29</td>
                </tr>
                <tr>
                    <td>研报观点</td>
                    <td>jy-financedata-api.CorporateResearchViewpoints</td>
                    <td>2026-03-30</td>
                </tr>
            </tbody>
        </table>
        <p><strong>数据核查</strong>：已通过内部一致性核查</p>
    </div>
</body>
</html>
```

## 无投融资事件 HTML 模板

```html
<!-- 投融资事件部分替换为 -->
<div class="section">
    <h2>4. 投融资事件：</h2>
    <p>无</p>
</div>
```

## HTML 输出要求

1. **编码**：使用 UTF-8 编码
2. **语言**：设置 `lang="zh-CN"`
3. **响应式**：添加 viewport meta 标签
4. **样式**：内联 CSS，确保独立文件可正常显示
5. **中文字体**：使用系统默认中文字体栈
6. **表格**：使用 HTML `<table>` 标签，带表头和样式
7. **列表**：使用自定义序号样式（①②③...）
8. **免责声明**：使用醒目背景色突出显示
9. **溯源信息**：放在报告末尾，使用不同背景色区分

## 转换说明

从 Markdown 转换到 HTML 时：
- `##` → `<h2>`
- `###` → `<h3>`
- 表格 → `<table>` with `<thead>` and `<tbody>`
- 序号列表 → `<ol>` with custom CSS counters
- 分隔线 `---` → `<hr>` 或 `<div class="section">`
- 粗体 `**text**` → `<strong>text</strong>`

---

**版本**：v1.0 | **更新**：2026-03-31
