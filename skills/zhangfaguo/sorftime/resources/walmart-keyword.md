> 公共参考见 [`_common.md`](./_common.md)：CLI 调用模板、Domain 表（Walmart domain=21）、错误码、返回结构、限流约束。本文档只描述 Walmart 关键词与词库接口独有的参数与字段。

# Walmart 关键词与词库接口（8 个）

**本文件接口**：KeywordQuery、KeywordSearchResults、KeywordRequest、ProductRequestKeywordv2、KeywordExtends、FavoriteKeyword、ChangeFavoriteKeyword、GetFavoriteKeyword

---

## 一、关键词类接口

### 1. 关键词查询 (KeywordQuery)
- **接口说明**: 查询当前热搜关键词清单
- **消耗请求数**: 5次
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | pattern | Object | 是 | 查询模式，见KeywordQueryPatternObject |
  | pageIndex | Integer | 否 | 查询第几页，默认1 |
  | pageSize | Integer | 否 | 每页条数，最小20，默认20，最大200 |
- **KeywordQueryPatternObject结构**:
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | keyword | String | 查询的关键词 |
  | rankCondition | String Array | 周排名筛选条件：[最小值,最大值] |
  | searchVolumeCondition | String Array | 近30日搜索量筛选条件：[最小值,最大值] |
- **使用示例**:
  ```bash
  # 查询热门关键词
  sorftime api KeywordQuery '{"pattern": {}, "pageIndex": 1, "pageSize": 50}' --domain 21

  # 筛选排名1-5000的关键词
  sorftime api KeywordQuery '{"pattern": {"rankCondition": ["1", "5000"]}, "pageIndex": 1, "pageSize": 50}' --domain 21

  # 筛选搜索量大于10000的关键词
  sorftime api KeywordQuery '{"pattern": {"searchVolumeCondition": ["10000"]}, "pageIndex": 1, "pageSize": 50}' --domain 21
  ```

---

### 2. 关键词近15日搜索结果产品 (KeywordSearchResults)
- **接口说明**: 近15日关键词搜索结果产品，仅支持当前的热搜词
- **消耗请求数**: 5次
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | keyword | String | 是 | 关键词 |
  | pageIndex | Integer | 否 | 查询第几页，默认1 |
  | pageSize | Integer | 否 | 每页条数，最小20，默认20，最大200 |
- **使用示例**:
  ```bash
  sorftime api KeywordSearchResults '{"keyword": "water bottle", "pageIndex": 1, "pageSize": 50}' --domain 21
  ```
- **返回数据**: ProductSummeryObject Array

---

### 3. 关键词详情 (KeywordRequest)
- **接口说明**: 关键词详情查询
- **消耗请求数**: 1次
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | keyword | String | 是 | 关键词 |
- **使用示例**:
  ```bash
  sorftime api KeywordRequest '{"keyword": "water bottle"}' --domain 21
  ```
- **返回字段说明** (KeywordSummeryObject):
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | keyword | String | 关键词 |
  | keywordCNName | String | 关键词中文名称 |
  | images | String Array | 某次搜索结果前10个产品图片 |
  | update | String | 最新更新时间 |
  | rank | Integer | 周搜索排名 |
  | searchVolume | Integer | 近30天搜索量 |
  | productCount | Integer | 竞品数量 |
  | searchFirstPageAvgPrice | Integer | 首页自然位产品平均价格（美分） |
  | searchFirstPageAvgReviews | Integer | 首页自然位产品平均评论数 |
  | searchFirstPageAvgStar | Number | 首页自然位产品平均星级（如4.5） |

---

### 4. 产品反查关键词 (ProductRequestKeywordv2)
- **接口说明**: 查询该产品近30天站内在哪些关键词搜索结果的前3页中曝光
- **消耗请求数**: 1次
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | productId | String | 是 | 需要查询的productId |
  | pageIndex | Integer | 否 | 查询第几页，默认1 |
  | pageSize | Integer | 否 | 每页条数，最小20，默认20，最大200 |
- **使用示例**:
  ```bash
  sorftime api ProductRequestKeywordv2 '{"productId": "12345678", "pageIndex": 1, "pageSize": 50}' --domain 21
  ```
- **返回字段说明** (ProductKeywordItemObject):
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | ShowShare | Number | 在此产品的反查关键词中，此词贡献的流量占比 |
  | recentlyPosition | String | 最近一次曝光位，格式："1,2/18"表示第1页第2位，共18个位置 |
  | organicPosition | String | 最近一次自然曝光位 |
  | adPosition | String | 最近一次广告曝光位 |
  | keyword | Object | 关键词详情（KeywordSummeryObject） |

---

### 5. 查延伸关键词 (KeywordExtends)
- **接口说明**: 基于关键词查延伸词
- **消耗请求数**: 5次
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | keyword | String | 是 | 查询的关键词 |
  | pageIndex | Integer | 否 | 查询第几页，默认1 |
  | pageSize | Integer | 否 | 每页条数，最小20，默认20，最大200 |
- **使用示例**:
  ```bash
  sorftime api KeywordExtends '{"keyword": "water bottle", "pageIndex": 1, "pageSize": 50}' --domain 21
  ```

---

## 二、关键词词库管理

### 6. 添加关键词到词库 (FavoriteKeyword)
- **接口说明**: 添加关键词到我的关键词词库（不限为热搜关键词）
- **消耗请求数**: 1次
- **注意**:
  - API的词库和Sorftime专业版的收藏夹不互通
  - 相同收藏夹下关键词不能重复（不同收藏夹下可以）
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | keyword | String | 是 | 需要收藏的词 |
  | dict | String | 否 | 指定收藏夹，不存在则新建。不指定则添加到`未分类` |
- **使用示例**:
  ```bash
  # 添加到未分类收藏夹
  sorftime api FavoriteKeyword '{"keyword": "water bottle"}' --domain 21

  # 添加到指定收藏夹
  sorftime api FavoriteKeyword '{"keyword": "water bottle", "dict": "我的词库"}' --domain 21
  ```
- **返回**:
  - 0: 收藏成功
  - 1: 此关键词已存在无需重复收藏
  - 9: 收藏失败

---

### 7. 移动/删除词库关键词 (ChangeFavoriteKeyword)
- **接口说明**: 移动关键词到指定收藏夹或删除关键词
- **消耗请求数**: 0次
- **注意**: 单个收藏夹最多只能收藏2000个关键词
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | keyword | String | 是 | 已收藏的词 |
  | dict | String | 否 | 指定收藏夹，不指定则操作`未分类`收藏夹 |
  | command | String | 是 | del=删除；move=<文件夹名称>=移动 |
- **使用示例**:
  ```bash
  # 删除关键词
  sorftime api ChangeFavoriteKeyword '{"keyword": "water bottle", "command": "del"}' --domain 21

  # 移动到指定文件夹
  sorftime api ChangeFavoriteKeyword '{"keyword": "water bottle", "command": "move=热门词"}' --domain 21
  ```
- **返回**:
  - 0: 操作成功
  - 9: 词未添加收藏

---

### 8. 查询词库关键词 (GetFavoriteKeyword)
- **接口说明**: 查询词库
- **消耗请求数**: 1次
- **请求参数**:
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|------|------|
  | command | String | 是 | all=全部词；dict=<名称>=指定文件夹；dict=文件夹列表 |
  | page | Integer | 否 | 分页查询，默认1，每页最多100条 |
- **使用示例**:
  ```bash
  # 查询全部词
  sorftime api GetFavoriteKeyword '{"command": "all", "page": 1}' --domain 21

  # 查询指定文件夹
  sorftime api GetFavoriteKeyword '{"command": "dict=我的词库", "page": 1}' --domain 21

  # 查询文件夹列表
  sorftime api GetFavoriteKeyword '{"command": "dict"}' --domain 21
  ```
- **返回格式**: JSON数组 `["kw1","kw2",...]`

---

## 注意事项

1. **热搜词限制**: KeywordSearchResults 仅支持当前热搜词，非热搜词查询可能无结果
2. **词库隔离**: API词库与Sorftime专业版收藏夹不互通，需分别管理
3. **收藏夹上限**: 单个收藏夹最多2000个关键词
4. **货币单位**: 价格相关字段单位为美分（如10000表示$100.00）
5. **请求频率**: 最高10次/秒，建议批量查询时控制速度

---

## 最佳实践

### 1. 关键词研究流程
```bash
# 步骤1: 产品反查关键词
sorftime api ProductRequestKeywordv2 '{"productId": "12345678"}' --domain 21

# 步骤2: 查询关键词详情
sorftime api KeywordRequest '{"keyword": "water bottle"}' --domain 21

# 步骤3: 拓展相关关键词
sorftime api KeywordExtends '{"keyword": "water bottle", "pageSize": 100}' --domain 21

# 步骤4: 查询关键词搜索结果
sorftime api KeywordSearchResults '{"keyword": "water bottle", "pageSize": 50}' --domain 21

# 步骤5: 收藏高价值关键词
sorftime api FavoriteKeyword '{"keyword": "water bottle", "dict": "核心词"}' --domain 21
```

### 2. 关键词筛选
```bash
# 筛选周排名1-5000且搜索量大于10000的关键词
sorftime api KeywordQuery '{"pattern": {"rankCondition": ["1", "5000"], "searchVolumeCondition": ["10000"]}, "pageSize": 100}' --domain 21
```

### 3. 词库管理
```bash
# 批量添加关键词到词库
sorftime api FavoriteKeyword '{"keyword": "water bottle", "dict": "竞品词"}' --domain 21
sorftime api FavoriteKeyword '{"keyword": "sport bottle", "dict": "竞品词"}' --domain 21

# 查询词库结构
sorftime api GetFavoriteKeyword '{"command": "dict"}' --domain 21

# 清理无效关键词
sorftime api ChangeFavoriteKeyword '{"keyword": "old keyword", "command": "del"}' --domain 21
```
