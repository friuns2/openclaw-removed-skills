> 公共参考见 [`_common.md`](./_common.md)：CLI 调用模板、Domain 表（Walmart domain=21）、错误码、返回结构、限流约束。本文档只描述 Walmart 类目与产品接口独有的参数与字段。

# Walmart 类目与产品接口（5 个）

**本文件接口**：CategoryTree、CategoryRequest、ProductRequest、ProductTrendRequest、ProductSalesVolume

---

## 一、类目市场类接口

### 1. 类目树 (CategoryTree)
- **接口说明**: 返回Walmart全量类目树结构
- **消耗请求数**: 5次
- **注意**: 
  - 返回数据很大（约10MB+），建议设置较长超时时间
  - 可选gzip压缩参数
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | gzip | Integer | 否 | 0或1，默认为0。设置为1时使用gzip压缩并返回base64字符串 |
- **使用示例**:
  ```bash
  # Walmart美国站类目树（不压缩）
  sorftime api CategoryTree --domain 21
  
  # 启用gzip压缩（需要手动解码）
  sorftime api CategoryTree --domain 21 --params '{"gzip": 1}'
  ```
- **返回字段说明** (CategoryTreeObject):
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | id | Integer | 类目ID |
  | parentId | Integer | 父级类目ID，为0表示第一级 |
  | nodeid | String | 类目nodeid |
  | name | String | 类目名称 |
  | cnName | String | 类目中文名称 |
  | url | String | 类目URL地址 |

---

### 2. 类目市场报告 (CategoryRequest)
- **接口说明**: 查询类目Best Seller Top 80产品数据
- **消耗请求数**: 5次
- **注意**: 数据范围为best seller top 80
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | nodePath | String | 是 | 需要查找的类目节点路径 |
- **使用示例**:
  ```bash
  sorftime api CategoryRequest '{"nodePath": "Electronics/Computers"}' --domain 21
  ```
- **返回数据**: ProductSummeryObject Array，产品列表

---

## 二、产品类接口

### 3. 产品数据查询 (ProductRequest)
- **接口说明**: 查询单个产品的详细信息
- **消耗请求数**: 1次
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | productId | String | 是 | 需要查询的产品Id |
- **使用示例**:
  ```bash
  sorftime api ProductRequest '{"productId": "12345678"}' --domain 21
  ```
- **返回字段说明** (ProductSummeryObject):
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | title | String | 产品名称 |
  | photo | String Array | 产品主图URL数组 |
  | listingSalesVolumeOfMonth | Integer | 链接预估月销量（不区分子体），评估产品销量时建议使用 |
  | listingSalesOfMonth | Integer | 链接预估月销售额（单位为美分，如10000表示$100.00） |
  | productId | String | 产品ID |
  | parentProductId | String | 父级产品ID |
  | price | Integer | 产品销售价（单位为美分，如1999表示$19.99） |
  | brand | String | 产品品牌 |
  | seller | String | 采集时的卖家 |
  | shipedby | String | 采集时的发货方式 |
  | wfsFee | Integer | FBA费用（单位为美分） |
  | attribute | String Array | 产品属性数组：["属性1","值1","属性2","值2",...] |
  | firstReviewsDate | String | 首个评论日期（yyyy-MM-dd） |
  | reviewsCount | Integer | 评论数量 |
  | ratings | Number | 评分星级（如4.8） |
  | nodePath | String Array | 产品所属类目节点数组 |
  | label | String Array | 产品标志数组（如pickup、savewith、bestsell等） |
  | popularPick | Integer | Popular Pick标志，存在时为1 |
  | clearance | Integer | Clearance标志，存在时为1 |
  | reducedPrice | Integer | Reduced Price标志，存在时为1 |
  | rollback | Integer | Rollback标志，存在时为1 |
  | flashDeal | Integer | Flash Deal标志，存在时为1 |
  | size | String Array | 外包装尺寸：["最长边","第二长边","最短边"]，单位cm |
  | weight | Integer | 产品重量，单位g |
  | variants | String Array | 子体信息JSON数组 |
  | numberOfStar | String Array | 各星级评论数量：["5","101","4","90",...] |
- **nodePath格式**:
  ```json
  [
    "类目节点名称", "类目节点", "排名时间", "排名",
    "类目节点名称", "类目节点", "排名时间", "排名"
  ]
  ```
- **variants格式**:
  ```json
  [
    {
      "VariantId": "3146561534",
      "Url": "https://...",
      "Property": ["Actual Color", "C"],
      "PriceUpdate": "2024-01-01",
      "DetailUpdate": "-"
    }
  ]
  ```
  - DetailUpdate: 当详情更新时间大于30天时，显示为"-"

---

### 4. 产品历史趋势 (ProductTrendRequest)
- **接口说明**: 查询产品历史趋势数据（销量、价格、评论、排名等）
- **消耗请求数**: 2次
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | productId | String | 是 | 需要查询的产品Id |
- **使用示例**:
  ```bash
  sorftime api ProductTrendRequest '{"productId": "12345678"}' --domain 21
  ```
- **返回字段说明** (ProductTrendObject):
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | productId | String | 产品ID |
  | listingSalesVolumeOfMonth | Integer | 链接预估月销量 |
  | listingSalesOfMonth | Integer | 链接预估月销售额（美分） |
  | listingSalesVolumeOfMonthTrend | String Array | 月销量历史趋势数组 |
  | listingSalesOfMonthTrend | String Array | 月销额历史趋势数组（美分） |
  | priceTrend | String Array | 价格趋势数组（美分） |
  | reviewsTrend | String Array | 评论数量趋势数组 |
  | starTrend | String Array | 星级趋势数组（450表示4.5星） |
  | rankTrend | two dimensional String Array | 各类目中的排名趋势 |
- **趋势数据格式**:
  - 数组格式：`["2025-01-01",100,"2025-01-02",200,...]`
  - 偶数下标为日期，奇数下标为对应数据值
- **rankTrend格式**:
  ```json
  [
    [
      "<类目节点名称>",
      "<类目节点>",
      "<日期yyyy-MM-dd>",
      "<排名>",
      "<日期yyyy-MM-dd>",
      "<排名>",
      ...
    ]
  ]
  ```

---

### 5. 产品官方公布子体销量 (ProductSalesVolume)
- **接口说明**: 查询产品官方公布的产品销量历史数据，最早自2024-01开始
- **消耗请求数**: 1次
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | productId | String | 是 | 需要查询的产品Id |
  | queryDate | String | 否 | 查询开始时间（yyyy-MM-dd），最早支持2023-09-01 |
  | queryEndDate | String | 否 | 查询截止时间（yyyy-MM-dd） |
  | pageIndex | Integer | 否 | 分页查询，默认1，每页最多100条数据 |
- **注意**: 
  - 默认（不传参数或参数无效时）返回近30日数据
  - 最早支持从2023年09月01日开始
- **使用示例**:
  ```bash
  # 查询近30日数据
  sorftime api ProductSalesVolume '{"productId": "12345678"}' --domain 21
  
  # 查询指定时间段
  sorftime api ProductSalesVolume '{"productId": "12345678", "queryDate": "2024-01-01", "queryEndDate": "2024-01-31"}' --domain 21
  ```
- **返回格式**: 二维数组
  ```json
  [
    ["2023-10-05", 100, 2],
    ...
  ]
  ```
  - 第1列：记录日期
  - 第2列：销量记录
  - 第3列：2=昨日销量

---

## 注意事项

1. **数据准确性**: 
   - 预估月销量基于当前排名预估未来30天销量
   - 评估产品销量时建议使用listingSalesVolumeOfMonth字段

2. **货币单位**: 
   - 所有价格、销售额、费用等单位为当地货币最小单位（美分）
   - 例如：1999表示$19.99，10000表示$100.00

3. **类目权限**: 如果未开通通用类目权限，查询时默认限于专属类目

4. **产品标志**: 
   - popularPick、clearance、reducedPrice、rollback、flashDeal
   - 存在标志时值为1，不存在时为0或null

5. **子体信息**: variants数组中的DetailUpdate，当详情更新时间大于30天时显示为"-"

6. **请求频率**: 最高10次/秒

7. **账户配置**: 所有接口默认使用当前活跃profile的Account-SK

---

## 最佳实践

### 1. 完整的类目分析流程
```bash
# 步骤1: 获取类目树
sorftime api CategoryTree --domain 21

# 步骤2: 查询类目Best Seller Top 80
sorftime api CategoryRequest '{"nodePath": "Electronics/Computers"}' --domain 21

# 步骤3: 查询具体产品详情
sorftime api ProductRequest '{"productId": "12345678"}' --domain 21

# 步骤4: 查询产品历史趋势
sorftime api ProductTrendRequest '{"productId": "12345678"}' --domain 21
```

### 2. 产品销量分析
```bash
# 查询官方公布的子体销量历史
sorftime api ProductSalesVolume '{"productId": "12345678", "queryDate": "2024-01-01", "queryEndDate": "2024-03-31"}' --domain 21
```

### 3. 产品对比分析
```bash
# 批量查询多个产品
sorftime api ProductRequest '{"productId": "prod1"}' --domain 21
sorftime api ProductRequest '{"productId": "prod2"}' --domain 21
sorftime api ProductRequest '{"productId": "prod3"}' --domain 21

# 对比它们的价格、销量、评论等指标
```
