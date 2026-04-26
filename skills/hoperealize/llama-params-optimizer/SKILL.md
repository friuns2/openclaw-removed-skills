---
name: llama-params-optimizer
version: 1.2.0
description: >
  Complete methodology for local LLM performance optimization.
  Discover the "context sweet spot" - 6% less context for 75% faster speed with ZERO quality loss.
  Step-by-step 4-phase 10-step control variable testing process.
  Works for ALL llama.cpp / llama-server models on ANY hardware.
author: fenglai
keywords: [llama.cpp, performance optimization, local llm, llama-server, quantization, long context, control variable testing, speed optimization]
tags: [llm, performance, optimization, local-first, chinese-support]
---

# llama.cpp 启动参数优化技能 / llama.cpp Parameter Optimization Guide

**中文** | **English**  
标准化的 LLM 本地部署启动参数优化评估流程，通过严格的控制变量测试，找到最佳的性能/质量平衡点。  
_A standardized methodology for optimizing local LLM deployment parameters, using rigorous control variable testing to find the optimal performance/quality balance._

## 🎯 核心卖点 / Key Features
- ✅ **独创「上下文甜点阈值」发现方法** / _Discover the "context sweet spot"_：零质量损失，速度提升 50-100% | _Zero quality loss for 50-100% speed boost_
- ✅ **四阶段十步法控制变量测试** / _4-phase 10-step process_：完整的性能/质量评估 | _Comprehensive performance and quality evaluation_
- ✅ **大量反常识踩坑经验** / _Battle-tested counterintuitive findings_：避免踩同样的坑 | _Avoid common pitfalls_
- ✅ **通用方法论** / _Universal methodology_：任何模型、任何硬件都可以直接套用 | _Works for any model, any hardware_
- ✅ **实战验证** / _Real-world proven_：35B+4060Ti 实战案例：从 49 token/s → 86 token/s，提升 75% | _35B + 4060Ti real case: 49 → 86 token/s, 75% improvement_

## 适用场景 / When to Use

**中文** | **English**  
新模型首次部署，需要找到最佳启动参数  
_First-time deployment of a new model, finding optimal launch parameters_  
新硬件环境下的性能调优  
_Performance tuning on new hardware_  
llama.cpp / llama-server 启动参数优化  
_llama.cpp / llama-server launch parameter optimization_  
验证量化损失、长上下文能力等核心特性  
_Verify quantization loss, long context capabilities, and other core features_

---

## 完整评估流程 / Complete Methodology
_**4 phases, 10 steps**_

---

### 📊 第一阶段：基准建立 / Phase 1: Establish Baseline

#### 步骤 1：建立初始基准 / Step 1: Run at default parameters
**中文** | **English**  
在默认参数下运行，记录基础性能数据：  
_Run with default parameters and record baseline performance:_  
```
✅ 记录项 / Metrics to record：
- 生成速度 / Generation speed (tokens/s)
- Prompt 处理速度 / Prompt processing speed (tokens/s)
- 显存占用峰值 / Peak VRAM usage (GB)
- 首字延迟 / Time to first token (ms)
```

#### 步骤 2：枚举所有待测试参数 / Step 2: List all parameters to test
**中文** | **English**  
列出所有可能影响性能的参数：  
_List all parameters that may affect performance:_  
| 参数 / Parameter | 典型测试值 / Typical values |
|------|-----------|
| `--threads` | 4 / 8 / 12 / 16 / CPU 核心数 |
| `-b / --batch-size` | 512 / 1024 / 2048 / 4096 |
| `--ctx-size` | **重要！优先测试！先找甜点阈值，再测其他参数** |
| `--flash-attn` | on / off |
| `--cache-type-k/v` | 不量化 / q8_0 / q4_0 |
| `--parallel` | 1 / 2 / 4 |
| `--ubatch-size` | 256 / 512 / 1024 |

---

### ⚡ 第二阶段：控制变量性能测试 / Phase 2: Control Variable Testing

#### 步骤 3：逐个参数控制变量测试 / Step 3: Test one parameter at a time
**中文** | **English**  
**核心原则：每次只改一个参数，其他所有参数保持基准不变！**  
_**Core principle: Change only ONE parameter each time, keep ALL others at baseline!**_  

❌ 错误做法 / Wrong way：链式修改，改完线程改上下文，再改 FA，结果混在一起无法归因  
_Chain modification - change threads, then context, then FA - results can't be attributed_  
✅ 正确做法 / Correct way：每次测试都回到基准配置，只改一个参数  
_Return to baseline config for each test, change only one parameter_  

#### 步骤 4：建立性能对比矩阵 / Step 4: Build comparison matrix

**⚠️ 重要反常识发现 / Critical Counterintuitive Findings**
- ❌ `--parallel 2` 不一定好 / Not always good：在 4060Ti + 35B 组合上，单请求速度反而下降 40%，调度开销超过了并发收益  
  _On 4060Ti + 35B Dense, parallel=2 slows single request by 40% - scheduling overhead exceeds concurrency benefit_  
- ✅ `--flash-attn on` 对长 Prompt 影响巨大 / Huge impact on long prompts：开启前 300-500 token/s，开启后 1858 token/s，快了 3-5 倍  
  _300-500 → 1858 token/s, 3-5x faster, but only ±5% effect on regular generation_  
- ❌ KV 缓存激进量化不一定好 / Aggressive KV quantization not always good：q4_K 在某些版本的 llama.cpp 上会导致模型加载速度极慢，优先用 q8_0  
  _q4_K can cause extremely slow loading on some llama.cpp versions - prefer q8_0_  

**中文** | **English**  
每个参数测试完成后，记录完整的对比表：  
_After each parameter test, record complete comparison table:_  

**示例：线程数对比 / Example: Thread count comparison**
| 线程数 / Threads | 生成速度 / Gen Speed | Prompt 速度 / Prompt Speed | 变化 / Change | 推荐 / Recommend |
|------------------|----------------------|-----------------------------|---------------|------------------|
| 8 | 84.8 | 80.0 | 基准 / Baseline | 🏆 最佳 / Best |
| 12 | 83.1 | 70.2 | -2.0% | |
| 16 | 83.5 | 75.0 | -1.5% | |

---

### 🎯 优先测试：上下文甜点阈值 / Priority: Find Context Sweet Spot
**MUST DO first - highest ROI optimization!**

**中文** | **English**  
这是所有优化里性价比最高的一项，通常能白嫖 50-100% 的速度提升，零质量损失！  
_This is the highest ROI optimization you can do - typically 50-100% speed boost with ZERO quality loss!_

#### 背景 / Background
**中文** | **English**  
几乎所有模型+显卡的组合，都存在一个断崖式的性能阈值：  
_Almost every model + GPU combination has a cliff-like performance threshold:_  
- ✅ 阈值以下：GPU 跑满，速度达到理论最大值  
  _Below threshold: GPU fully utilized, maximum theoretical speed_  
- ❌ 阈值以上：速度直接腰斩（40-60%），但显存只多占了 30-50MB  
  _Above threshold: Speed drops by 40-60% (half speed), but VRAM only increases 30-50MB_  

这不是线性下降，是跳崖式下降！原因通常是：  
_This is NOT a linear degradation, but a cliff! Common causes:_  
1. GDDR 显存 Bank 对齐边界，跨 Bank 访问延迟翻 3-5 倍  
   _GDDR memory bank alignment - cross-bank access latency increases 3-5x_  
2. FlashAttention 的 Tile 块大小阈值，超过之后触发缓存换页  
   _FlashAttention tile size threshold - exceeding triggers cache swapping_  
3. 大页内存分配失败，TLB 命中率骤降  
   _Large page memory allocation failure - TLB hit rate plummets_  

#### 标准测试方法 / Standard Testing Method
**中文** | **English**  
1. **从厂商标称的最大上下文开始** / _Start from manufacturer's advertised maximum_（比如 128K）  
2. **每次降 4K** / _Reduce by 4K each time_（必须是 2 的幂次相关步长 / Must be power-of-2 aligned）  
3. 每次都跑一次完整测速（生成 600 token 左右） / _Run full speed test each time (~600 tokens)_  
4. 找到 **速度突然跳涨的那个点** / _Find the point where speed suddenly jumps_，就是你的黄金甜点阈值 / _That's your sweet spot!_  

#### 典型测试结果示例 / Typical Test Results
**Qwen3.6-35B + RTX 4060Ti 16GB**

| 上下文大小 / Context | 生成速度 / Speed | 显存占用 / VRAM | 状态 / Status |
|---------------------|------------------|-----------------|---------------|
| 128K (厂商标称 / advertised) | 48.9 token/s | 15928MiB | ❌ Half speed |
| 124K | 50.6 token/s | 15969MiB | ❌ Half speed |
| **120K (黄金点 / SWEET SPOT)** | **86.4 token/s** | 15931MiB | ✅ Full speed |
| 96K | 86.1 token/s | 15666MiB | ✅ Full speed |

#### 核心结论 / Key Takeaways
**中文** | **English**  
- 通常甜点阈值 = 厂商标称最大值的 90-95%  
  _Typically sweet spot = 90-95% of advertised maximum_  
- 上下文只少 5-10%（完全感知不到），速度提升 50-100%  
  _Only 5-10% less context (completely unnoticeable) for 50-100% speed boost_  
- **这一步必须第一个做！** 所有后续参数测试都应该在甜点阈值下进行  
  _**DO THIS FIRST!** All subsequent parameter testing should be done at the sweet spot_  


---

### ✅ 第三阶段：质量验证

#### 步骤 5：量化损失验证
对比开/关量化的输出质量，使用相同的 Prompt + 温度=0.1 最小化随机性：
```
测试方法：
1. 关 KV 量化（FP16），输出结果 A
2. 开 KV q8_0 量化，相同 Prompt，输出结果 B
3. 人工对比 A 和 B，判断是否有可感知的质量损失
```

#### 步骤 6：上下文回忆能力测试
使用「密钥召回法」验证长上下文能力：
```
测试方法：
1. 构造长 Prompt：前面是大量无关填充文本
2. 在 Prompt 的 10% / 50% / 90% 位置分别藏一个随机密钥
3. 问模型：「文档中的秘密密钥是什么？」
4. 记录不同距离的召回成功率
```

**典型测试距离：**
- 短距离：~1000 token
- 中距离：~20000 token
- 长距离：~50000 token（根据最大上下文调整）

#### 步骤 7：基本能力冒烟测试
验证模型的基础能力没有因为参数调整而下降：
```
测试用例：
1. 简单数学题：小明有5个苹果，给了小红2个，又买了3个，现在有几个？
2. 简单逻辑题：正方形边长4cm，面积是多少？
3. 简单代码题：用Python写一个函数求列表偶数的和
```

---

### 🎯 第四阶段：综合评估与产出

#### 步骤 8：多维度综合评分
| 维度 | 权重 | 评分标准（10分制） |
|------|------|-------------------|
| **性能** | 50% | 生成速度(30%) + Prompt速度(20%) |
| **质量** | 40% | 量化损失(15%) + 上下文回忆(15%) + 基本能力(10%) |
| **稳定性** | 10% | 启动成功率、运行稳定性、API兼容性 |

#### 步骤 9：反常识发现总结
**必须记录所有反直觉的结论！** 这些是最有价值的经验：

**示例（来自 Qwen3.5-MoE 实战）：**
1. ❗ 默认 batch size 是 512，改成 2048 直接快 67.7%！
2. ❗ KV q8_0 量化不是损失，反而让 Prompt 处理快了 128%！
3. ❗ Flash Attention 对 MoE 模型：生成慢 1.3%，但 Prompt 快 128%，整体收益巨大！
4. ❗ 线程不是越多越好：8 线程比 12/16 都快！
5. ❗ 链式测试会严重误导结论：必须严格控制变量！

#### 步骤 10：产出最终最佳配置
最终输出：
1. ✅ 最佳性能配置（最快速度）
2. ✅ 最佳上下文配置（最大窗口）
3. ✅ 综合推荐配置（平衡最佳）
4. ✅ 一键启动的完整命令

---

## 实战案例合集

---

### 案例1：Qwen3.5-MoE 35B + RTX 4060Ti 16GB（MoE 模型）

#### 优化成果
**初始速度：23.4 tokens/s → 最终速度：84.8 tokens/s，提升 262%！**

#### 最佳参数
| 参数 | 最佳值 | 收益 |
|------|--------|------|
| `--threads` | 8 | +2.4% |
| `-b / --batch-size` | 2048 | +67.7% 最大提升！ |
| `--ctx-size` | 65536（最快）或 262144（最大） | 64K 比 256K 快 3.7 倍 |
| `--flash-attn` | on | Prompt +128%，生成 -1.3% |
| `--cache-type-k/v` | q8_0 | Prompt +128%，省 512MB，零质量损失 |
| `--parallel` | 2 | Prompt 最快，支持 2 并发 |
| `--ubatch-size` | 默认 512 | 改了反而慢 17-60% |

---

### 案例2：Qwen3.6-35B Dense + RTX 4060Ti 16GB（Dense 模型，2026-04-26 最新测试）

#### 优化成果
**初始速度：48.9 tokens/s → 最终速度：86.4 tokens/s，提升 77%！**

#### 核心发现：断崖式甜点阈值
| 上下文 | 速度 | 状态 |
|--------|------|------|
| 128K（厂商默认） | 48.9 token/s | ❌ 腰斩 |
| 124K | 50.6 token/s | ❌ 腰斩 |
| **120K（甜点阈值）** | **86.4 token/s** | ✅ 满速 |
| 96K / 64K / 32K | 83-86 token/s | ✅ 满速 |

仅减少 6% 上下文，速度提升 **77%**，零质量损失！

#### 最佳参数
| 参数 | 最佳值 | 说明 |
|------|--------|------|
| `--ctx-size` | **122880（120K）** | 甜点阈值，再大直接腰斩 |
| `--threads` | 8 | 最佳 |
| `-b / --batch-size` | 2048 | 最佳 |
| `--parallel` | **1** | ❗ Dense 模型上 parallel=2 反而慢 40% |
| `--flash-attn` | on | 必须开，长 Prompt 处理快 3-5 倍 |
| `--cache-type-k/v` | q8_0 | q4_K 有兼容性问题 |

### 最终最佳启动命令（Qwen3.6-35B Dense + 4060Ti，120K甜点阈值）
```cmd
# Windows
llama-server.exe -m "你的模型路径.gguf" --n-gpu-layers 9999 --ctx-size 122880 --port 8080 --host 0.0.0.0 --threads 8 --mlock --parallel 1 --kv-unified --flash-attn on -b 2048 --cache-type-k q8_0 --cache-type-v q8_0

# Linux/WSL2（加上CPU亲和性绑定，+5%）
taskset -c 0-7 llama-server -m "你的模型路径.gguf" --n-gpu-layers 9999 --ctx-size 122880 --port 8080 --host 0.0.0.0 --threads 8 --mlock --parallel 1 --kv-unified --flash-attn on -b 2048 --cache-type-k q8_0 --cache-type-v q8_0
```

### 进阶：CPU 亲和性绑定（+1-5% 速度，聊胜于无）
Linux/WSL2 下可以用 taskset 把线程绑到同一物理核心簇上，减少跨核通讯开销：
```bash
taskset -c 0-7 llama-server ...
```
注意：核心范围要和你的 `--threads` 参数对应，不要跨 CCX 模块。

---

## 核心原则

1. **控制变量高于一切**：每次只改一个参数，其他全部保持不变
2. **不要只看生成速度**：Prompt 处理速度同样重要，甚至更重要
3. **量化不一定是损失**：有时候反而更快，一定要实际测试
4. **默认参数通常很保守**：一定要测试更大的 batch size、不同的线程数
5. **不同模型结论不同**：MoE 和 Dense 模型的最佳参数可能完全相反，不要经验主义

---

## 快速检查清单

每次优化前过一遍：
- [ ] 已记录默认参数下的基准速度
- [ ] 已列出所有待测试的参数
- [ ] 每次测试只改一个参数
- [ ] 已验证量化损失（如果开了量化）
- [ ] 已测试长上下文回忆能力
- [ ] 已做基本能力冒烟测试
- [ ] 已记录所有反常识的发现
- [ ] 已产出最终的一键启动命令
