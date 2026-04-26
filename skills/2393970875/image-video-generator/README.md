# AI Image Generator

基于 AI Artist API 的图片/视频异步生成工具。

- 支持图片与视频任务创建
- 自动轮询任务状态直到完成
- 支持本地参考图自动上传
- 创建任务前自动调用费用预估，余额不足时会拦截并提示充值

## 🚀 快速开始

### 1) 获取 API Key

访问 [https://ai.deepsop.com/](https://ai.deepsop.com/) 注册登录后，在控制台创建 API Key。

### 2) 设置环境变量

```bash
# Linux/macOS/Git Bash
export AI_ARTIST_TOKEN="sk-your_api_key_here"
```

```powershell
# Windows PowerShell
$env:AI_ARTIST_TOKEN="sk-your_api_key_here"
```

### 3) 验证配置

```bash
python3 scripts/test_config.py
```

### 4) 开始生成

```bash
# 默认图片模型（SEEDREAM5_0）
python3 scripts/generate_image.py "一只可爱的猫"
```

## 🎨 支持模型

### 图片模型
- `SEEDREAM5_0`（默认）
- `NANO_BANANA_2`

### 视频模型
- `SEEDANCE_1_5_PRO`
- `VEO3.1FAST_LITE`
- `VEO3.1PRO_LITE`
- `VEO3.1FAST`
- `VEO3.1PRO`
- `WAN2.6_T2V`
- `WAN2.6_I2V`
- `WAN2.6_R2V`

## 📝 常用示例

```bash
# 图片：指定模型
python3 scripts/generate_image.py "一只柴犬" --model NANO_BANANA_2

# 图片：下载到本地
python3 scripts/generate_image.py "海边日落" --download

# 图片：参考图生成（本地文件自动上传）
python3 scripts/generate_image.py "做成赛博朋克风格" --reference-image "./ref.png"

# 视频：基础文生视频
python3 scripts/generate_image.py "城市夜景延时" --model SEEDANCE_1_5_PRO

# 视频：首尾帧控制
python3 scripts/generate_image.py "灯具变形动画" --model VEO3.1PRO --first-image "./start.jpg" --last-image "./end.jpg"
```

## 📖 文档

完整参数说明与更多示例见 `SKILL.md`。

## 🔧 环境要求

- Python 3.6+
- `requests`

## ⚠️ 注意事项

- 必须使用你自己的 `AI_ARTIST_TOKEN`
- 任务创建前会执行费用预估；若余额不足将不会提交任务
- 请遵守 AI Artist API 的使用条款
