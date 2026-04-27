# API 接口文档

## 基础信息

- 基础路径：`http://localhost:3000/api/v1`
- 数据格式：JSON

## 端点列表

### 健康检查

```
GET /health
```

响应：
```json
{
  "status": "ok"
}
```

### 团队

#### 获取团队列表

```
GET /teams
```

响应：
```json
[
  {
    "id": "uuid",
    "name": "团队名称",
    "users": [...],
    "projects": [...]
  }
]
```

#### 同步团队

```
POST /teams/sync
```

请求体：
```json
{
  "name": "团队名称",
  "members": [
    {
      "name": "成员姓名",
      "email": "邮箱",
      "gitUsername": "Git用户名"
    }
  ]
}
```

### 项目

#### 获取项目列表

```
GET /projects
```

#### 获取单个项目

```
GET /projects/:id
```

#### 创建项目

```
POST /projects
```

请求体：
```json
{
  "name": "项目名称",
  "repository": "仓库地址",
  "teamId": "团队ID"
}
```

### 分析记录

#### 获取分析记录

```
GET /analyses
GET /analyses?periodType=week&periodValue=20260327
```

查询参数：
- `periodType`: 周期类型（week/month）
- `periodValue`: 周期值

#### 获取统计数据

```
GET /analyses/statistics
```

#### 同步分析数据

```
POST /analyses/sync
```

请求体：
```json
{
  "periodType": "week",
  "periodValue": "20260327",
  "teamName": "团队名称",
  "analyses": [...]
}
```

### 代码审查

#### 获取项目代码审查

```
GET /code-review/:projectId
GET /code-review/:projectId?periodType=week&periodValue=20260327
```