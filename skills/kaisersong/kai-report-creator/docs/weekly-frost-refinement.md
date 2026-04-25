# weekly-frost 主题细化设计

基于预览效果，逐项优化参数。

---

## 1. KPI 网格列数

**当前：** 固定 4 列  
**问题：** 如果只有 2-3 个指标，4 列会显得空洞

**优化方案：**
```css
/* 动态列数 */
.kpi-row {
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: .5rem;
}
```

**效果：**
- 2 个 KPI → 2 列
- 3 个 KPI → 3 列
- 4 个 KPI → 4 列
- 5+ 个 KPI → 自动换行

---

## 2. 时间线节点大小

**当前：** 7px + 1.5px border  
**问题：** 在深色背景上不够突出

**优化：**
```css
.tl-dot {
  width: 8px;
  height: 8px;
  border: 2px solid var(--bg);  /* 加粗边框 */
  box-shadow: 0 0 0 1px var(--primary); /* 添加光晕，本周节点 */
}
.tl-item.future .tl-dot {
  box-shadow: none;  /* 下周节点无光晕 */
}
```

**效果：** 本周节点有青蓝光晕，下周节点纯灰色，对比更强

---

## 3. 本周/下周分界线样式

**当前：** 灰色虚线 + "下周▸" 文字标签  
**问题：** 灰色在深色背景上不够醒目，这是唯一的时间转折点

**优化：**
```css
.week-divider {
  border: none;
  border-top: 1px dashed var(--primary);
  opacity: .3;  /* 用主色，但低透明度 */
  margin: .8rem 0;
}
.week-divider::after {
  content: '下周 ▸';
  color: var(--primary);  /* 用主色，醒目 */
  opacity: 1;  /* 标签不透明 */
  background: var(--bg);
  padding: 0 .5rem;
  /* ... */
}
```

**效果：** 分界线用青蓝色（低透明度），标签用青蓝色（不透明），时间转折点醒目但不抢眼

---

## 4. 项目卡片状态线宽度

**当前：** 3px  
**问题：** 在紧凑布局中稍粗

**优化：**
```css
.proj {
  border-left: 2px solid var(--border);  /* 2px 更细 */
}
```

**效果：** 2px 边框更精致，不占空间

---

## 5. Callout 背景

**当前：** `rgba(251,191,36,.08)` 等 8% 透明度  
**问题：** 在深色背景上几乎看不出来

**优化：**
```css
.callout--warn {
  background: rgba(251,191,36,.15);  /* 15% 透明度 */
  border-color: var(--status-warn);
}
.callout--info {
  background: rgba(56,189,248,.15);  /* 15% 透明度 */
  border-color: var(--primary);
}
```

**效果：** callout 背景 15% 透明度，有足够对比度但不抢眼

---

## 6. Badge 字重

**当前：** 700  
**问题：** 周报高频查看，太粗会累

**优化：**
```css
.badge {
  font-weight: 600;  /* 600 更轻盈 */
}
```

---

## 7. 表格 mono 字体日期列

**当前：** `.tl-date` 用 mono  
**问题：** 表格日期列也应该用 mono，保持一致性

**优化：**
```css
.tbl td:first-child {
  font-family: var(--font-mono);  /* 日期列 mono */
}
```

---

## 最终参数汇总

| 设计项 | 原值 | 优化值 | 理由 |
|--------|------|--------|------|
| KPI 网格列数 | 固定 4 列 | `auto-fit minmax(140px,1fr)` | 动态适应 KPI 数量 |
| 时间线节点大小 | 7px + 1.5px border | 8px + 2px border + 光晕 | 本周节点更突出 |
| 分界线颜色 | 灰色虚线 | primary 色 30% 透明度 | 时间转折点醒目 |
| 项目状态线宽度 | 3px | 2px | 更精致紧凑 |
| Callout 背景 | 8% 透明度 | 15% 透明度 | 有足够对比度 |
| Badge 字重 | 700 | 600 | 更轻盈不累 |

---

**下一步：创建完整主题 CSS 文件（A）**