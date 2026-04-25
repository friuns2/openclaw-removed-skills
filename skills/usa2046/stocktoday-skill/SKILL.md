# StockToday Skill

股票数据 MCP 服务器，提供 **200+** A股市场数据接口。

## 功能

- 股票基础数据（代码、财务、股东等）
- 实时行情数据（支持复权、分钟线）
- 财务数据（资产负债表、利润表、现金流）
- 资金流向（同花顺、东方财富）
- 指数数据（沪深、全球、板块指数）
- 基金/期货/期权/现货数据
- 特色数据（龙虎榜、融资融券、筹码等）
- 港股、美股、宏观数据

## 配置

### 环境变量

```bash
# 设置 token
export STOCKTODAY_TOKEN="your_token"

# 可选：自定义API地址
export STOCKTODAY_URL="https://tushare.citydata.club/"
```

## 使用示例

```
User: 查一下茅台今天的行情
→ pro_bar { "ts_code": "600519.SH", "start_date": "20260425", "end_date": "20260425", "adj": "qfq", "freq": "D" }

User: 上证指数今天怎么样？
→ index_daily { "ts_code": "000001.SH", "start_date": "20260425", "end_date": "20260425" }

User: 今天龙虎榜有哪些？
→ top_list { "trade_date": "20260425" }

User: 茅台的财务数据
→ income { "ts_code": "600519.SH" }
```

## 工具列表 (200+)

### 股票-基础数据 (16)
| 工具 | 说明 |
|------|------|
| `stock_basic` | 股票基本信息 |
| `stk_premarket` | 新股上市 |
| `trade_cal` | 交易日历 |
| `stock_st` | ST股票列表 |
| `st` | ST股票列表(别名) |
| `namechange` | 股票名称变更 |
| `stock_company` | 上市公司信息 |
| `stk_managers` | 公司管理层 |
| `stk_rewards` | 高管薪酬 |
| `new_share` | 新股发行 |
| `bak_basic` | 备用基础数据 |
| `stk_account` | 股票账户 |
| `stk_account_old` | 股票账户(旧) |
| `stk_ah_comparison` | AH股对比 |
| `stock_hsgt` | 沪深港通股票列表 |
| `bse_mapping` | 北交所新旧代码对照 |

### 股票-行情数据 (18)
| 工具 | 说明 |
|------|------|
| `daily` | 日线行情 |
| `weekly` | 周线行情 |
| `monthly` | 月线行情 |
| `stk_weekly_monthly` | 周月线行情 |
| `stk_week_month_adj` | 周月线复权行情 |
| `pro_bar` | 行情(支持复权) |
| `adj_factor` | 复权因子 |
| `daily_basic` | 每日指标 |
| `stk_limit` | 涨跌停 |
| `suspend_d` | 停复牌 |
| `hsgt_top10` | 沪深股通前十 |
| `ggt_top10` | 广港通前十 |
| `ggt_daily` | 广港通每日 |
| `ggt_monthly` | 广港通每月 |
| `bak_daily` | 备用每日行情 |
| `get_daily` | 获取日线(简化) |
| `get_index_daily` | 获取指数日线 |
| `get_realtime_quote` | 实时行情 |

### 股票-财务数据 (10)
| 工具 | 说明 |
|------|------|
| `income` | 利润表 |
| `balancesheet` | 资产负债表 |
| `cashflow` | 现金流量表 |
| `forecast` | 业绩预告 |
| `express` | 业绩快报 |
| `dividend` | 分红送股 |
| `fina_indicator` | 财务指标 |
| `fina_audit` | 财务审计 |
| `fina_mainbz` | 主营业务 |
| `disclosure_date` | 披露日期 |

### 股票-参考数据 (9)
| 工具 | 说明 |
|------|------|
| `top10_holders` | 十大股东 |
| `top10_floatholders` | 十大流通股东 |
| `pledge_stat` | 股权质押统计 |
| `pledge_detail` | 股权质押明细 |
| `repurchase` | 股份回购 |
| `share_float` | 流通股本 |
| `block_trade` | 大宗交易 |
| `stk_holdernumber` | 股东户数 |
| `stk_holdertrade` | 股东增减持 |

### 股票-特色数据 (18)
| 工具 | 说明 |
|------|------|
| `report_rc` | 研报 |
| `cyq_perf` | 筹码活跃度 |
| `cyq_chips` | 筹码分布 |
| `stk_factor_pro` | 股票因子(专业版) |
| `ccass_hold` | 中央结算持股 |
| `ccass_hold_detail` | 中央结算持股明细 |
| `hk_hold` | 港股持股 |
| `stk_auction_o` | 集合竞价(开盘) |
| `stk_auction_c` | 盘后定价 |
| `stk_auction` | 股票集合竞价 |
| `stk_nineturn` | 九转序列 |
| `stk_surv` | 舆情监控 |
| `broker_recommend` | 券商研报推荐 |
| `anns_d` | 上市公司公告 |
| `cctv_news` | 新闻联播文字稿 |
| `ths_news` | 同花顺新闻 |
| `npr` | 国家政策库 |
| `research_report` | 券商研究报告 |

### 股票-两融 (7)
| 工具 | 说明 |
|------|------|
| `margin` | 融资融券 |
| `margin_detail` | 融资融券明细 |
| `margin_secs` | 融资融券证券 |
| `slb_sec` | 融券余量 |
| `slb_len` | 融资期限 |
| `slb_sec_detail` | 融券余量明细 |
| `slb_len_mm` | 融资期限明细 |

### 股票-资金流向 (8)
| 工具 | 说明 |
|------|------|
| `moneyflow` | 资金流向 |
| `moneyflow_ths` | 资金流向(同花顺) |
| `moneyflow_cnt_ths` | 资金流向分类(同花顺) |
| `moneyflow_dc` | 资金流向(东方财富) |
| `moneyflow_ind_ths` | 行业资金流向(同花顺) |
| `moneyflow_ind_dc` | 行业资金流向(东方财富) |
| `moneyflow_mkt_dc` | 市场资金流向(东方财富) |
| `moneyflow_hsgt` | 沪深港通资金流向 |

### 股票-打板专题 (17)
| 工具 | 说明 |
|------|------|
| `kpl_concept` | 开盘啦概念 |
| `kpl_concept_cons` | 开盘啦概念成分 |
| `kpl_list` | 开盘啦列表 |
| `top_list` | 龙虎榜上榜 |
| `top_inst` | 龙虎榜机构 |
| `limit_list_ths` | 涨停列表(同花顺) |
| `limit_list_d` | 涨跌停明细 |
| `limit_step` | 涨停阶梯 |
| `limit_cpt_list` | 涨停股票池 |
| `ths_index` | 同花顺指数 |
| `ths_member` | 同花顺成分股 |
| `dc_index` | 东财指数 |
| `dc_member` | 东财成分股 |
| `hm_list` | 活跃股列表 |
| `hm_detail` | 活跃股明细 |
| `ths_hot` | 同花顺热点 |
| `dc_hot` | 东方财富热点 |

### 指数 (22)
| 工具 | 说明 |
|------|------|
| `index_basic` | 指数基本信息 |
| `index_daily` | 指数日线 |
| `index_weekly` | 指数周线 |
| `index_monthly` | 指数月线 |
| `index_weight` | 指数成分 |
| `index_dailybasic` | 指数每日指标 |
| `index_classify` | 指数分类 |
| `index_member` | 指数成分股 |
| `index_member_all` | 指数成分股(全) |
| `ci_index_member` | 中证指数成分 |
| `daily_info` | 每日信息 |
| `sz_daily_info` | 深市每日信息 |
| `ths_daily` | 同花顺指数日线 |
| `ci_daily` | 中证指数日线 |
| `sw_daily` | 申万指数日线 |
| `index_global` | 全球指数 |
| `idx_factor_pro` | 指数因子(专业版) |
| `dc_daily` | 东财指数每日 |
| `tdx_index` | 通达信指数 |
| `tdx_daily` | 通达信指数日线 |
| `tdx_member` | 通达信板块成分 |
| `gz_index` | 国证指数 |
| `wz_index` | 万德指数 |

### 基金 (15)
| 工具 | 说明 |
|------|------|
| `fund_basic` | 基金基本信息 |
| `fund_company` | 基金公司 |
| `fund_manager` | 基金经理 |
| `fund_share` | 基金份额 |
| `fund_nav` | 基金净值 |
| `fund_div` | 基金分红 |
| `fund_portfolio` | 基金持仓 |
| `fund_daily` | 基金日线 |
| `fund_adj` | 基金复权 |
| `fund_factor_pro` | 基金因子(专业版) |
| `fund_sales_ratio` | 基金销售比例 |
| `fund_sales_vol` | 基金销售量 |
| `etf_basic` | ETF基本信息 |
| `etf_index` | ETF关联指数 |
| `etf_share_size` | ETF份额 |

### 期货 (11)
| 工具 | 说明 |
|------|------|
| `fut_basic` | 期货基本信息 |
| `fut_daily` | 期货日线 |
| `fut_weekly_monthly` | 期货周/月线 |
| `ft_mins` | 期货分钟线 |
| `fut_wsr` | 期货持仓 |
| `fut_settle` | 期货结算 |
| `fut_holding` | 期货持仓量 |
| `fut_mapping` | 期货映射 |
| `fut_weekly_detail` | 期货每周详情 |
| `ft_limit` | 期货涨跌停 |
| `cb_factor_pro` | 可转债因子(专业版) |

### 现货 (2)
| 工具 | 说明 |
|------|------|
| `sge_basic` | 现货基本信息 |
| `sge_daily` | 现货每日行情 |

### 期权 (3)
| 工具 | 说明 |
|------|------|
| `opt_basic` | 期权基本信息 |
| `opt_daily` | 期权每日行情 |
| `opt_mins` | 期权分钟行情 |

### 可转债 (7)
| 工具 | 说明 |
|------|------|
| `cb_basic` | 可转债基本信息 |
| `cb_issue` | 可转债发行 |
| `cb_call` | 可转债回售 |
| `cb_rate` | 可转债转股溢价率 |
| `cb_daily` | 可转债每日行情 |
| `cb_price_chg` | 可转债价格变化 |
| `cb_share` | 可转债转股 |

### 债券 (6)
| 工具 | 说明 |
|------|------|
| `repo_daily` | 回购每日行情 |
| `bc_otcqt` | 银行间报价 |
| `bc_bestotcqt` | 银行间最优报价 |
| `bond_blk` | 债券大宗交易 |
| `bond_blk_detail` | 债券大宗交易明细 |
| `yc_cb` | 可转债收益率 |

### 宏观经济 (17)
| 工具 | 说明 |
|------|------|
| `eco_cal` | 经济日历 |
| `shibor` | SHIBOR利率 |
| `shibor_quote` | SHIBOR报价 |
| `shibor_lpr` | LPR贷款基础利率 |
| `cn_gdp` | 中国GDP |
| `cn_cpi` | 中国CPI |
| `cn_ppi` | 中国PPI |
| `cn_m` | 货币供应量(月) |
| `cn_pmi` | 采购经理指数PMI |
| `sf_month` | 上海黄金现货月报 |
| `libor` | Libor利率 |
| `hibor` | Hibor利率 |
| `us_tbr` | 美国短期国债利率 |
| `us_tycr` | 美国国债收益率曲线利率 |
| `us_trycr` | 美国国债实际收益率曲线利率 |
| `us_tltr` | 美国国债长期利率 |
| `us_trltr` | 美国国债实际长期利率平均值 |

### 外汇 (2)
| 工具 | 说明 |
|------|------|
| `fx_obasic` | 外汇基本信息 |
| `fx_daily` | 外汇每日行情 |

### 港股 (10)
| 工具 | 说明 |
|------|------|
| `hk_basic` | 港股基本信息 |
| `hk_tradecal` | 港股交易日历 |
| `hk_daily` | 港股每日行情 |
| `hk_daily_adj` | 港股每日行情(复权) |
| `hk_mins` | 港股分钟线 |
| `hk_income` | 港股利润表 |
| `hk_balancesheet` | 港股资产负债表 |
| `hk_cashflow` | 港股现金流量表 |
| `hk_adjfactor` | 港股复权因子 |
| `hk_fina_indicator` | 港股财务指标 |

### 美股 (9)
| 工具 | 说明 |
|------|------|
| `us_basic` | 美股基本信息 |
| `us_tradecal` | 美股交易日历 |
| `us_daily` | 美股每日行情 |
| `us_daily_adj` | 美股每日行情(复权) |
| `us_income` | 美股利润表 |
| `us_balancesheet` | 美股资产负债表 |
| `us_cashflow` | 美股现金流量表 |
| `us_adjfactor` | 美股复权因子 |
| `us_fina_indicator` | 美股财务指标 |

### 资讯 (2)
| 工具 | 说明 |
|------|------|
| `news` | 资讯 |
| `major_news` | 重要资讯 |

### 其他 (10)
| 工具 | 说明 |
|------|------|
| `tmt_twincome` | 台湾电子产业月营收 |
| `tmt_twincomedetail` | TMT月营收明细 |
| `film_record` | 电影剧本备案公示 |
| `teleplay_record` | 电视剧备案公示 |
| `bo_daily` | 电影日度票房 |
| `bo_monthly` | 电影月度票房 |
| `bo_weekly` | 电影周度票房 |
| `bo_cinema` | 影院日度票房 |
| `irm_qa_sh` | 上证e互动问答 |
| `irm_qa_sz` | 深证易互动问答 |

### 实时数据 (11)
| 工具 | 说明 |
|------|------|
| `rt_min` | 股票实时分钟 |
| `rt_k` | 股票实时日线 |
| `rt_idx_k` | 指数实时日线 |
| `rt_idx_min` | 指数实时分钟 |
| `rt_sw_k` | 申万指数实时行情 |
| `rt_etf_k` | ETF实时日线 |
| `rt_fut_min` | 期货实时分钟 |
| `rt_hk_k` | 港股实时日线 |
| `stk_mins` | 股票历史分钟 |
| `idx_mins` | 指数历史分钟 |

## 后端

使用自定义后端服务: `https://tushare.citydata.club/`

不需要 Tushare 官方 Token。

---
*Published via ClawHub*
*Version 1.0.6*