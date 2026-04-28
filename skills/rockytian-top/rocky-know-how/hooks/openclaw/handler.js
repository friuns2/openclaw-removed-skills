/**
 * rocky-know-how Hook for OpenClaw
 *
 * v3.3.0 - 去除 pending/draft 中间层
 * - agent:bootstrap: 注入经验提醒 + 扫描 memory 直接 LLM 判断写入
 * - memory 候选 → LLM 判断 → 决定新增/追加 → 直接写入 experiences.md
 * - 移除 pending 文件、draft 文件、processPendingItem 等中间层
 */

const { existsSync, readFileSync, writeFileSync, appendFileSync, unlinkSync, mkdirSync, renameSync, readdirSync, statSync } = require('fs');
const { join } = require('path');
const { execSync } = require('child_process');

/**
 * 宽容的 JSON 解析 - 处理 trailing comma 等 JSON5 特性
 * openclaw.json 可能包含 trailing comma（JSON5 格式）
 */
function parseJSONLenient(text) {
  // 移除对象和数组中的 trailing comma: ,} → },  ,] → ],
  const cleaned = text.replace(/,\s*([}\]])/g, '$1');
  return JSON.parse(cleaned);
}

/**
 * Shell 安全转义函数
 * 使用单引号包裹，将单引号转义为 '\''
 * 防止 $() ` $var 等 shell 元字符注入
 */
function shellEscape(str) {
  if (str == null) return '';
  return str
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\$/g, '\\$')
    .replace(/`/g, '\\`')
    .replace(/\n/g, ' ');
}

/**
 * 通过 fetch 调用 LLM API，避免 API Key 暴露在进程列表
 */
async function callLLMApi(apiUrl, apiKey, payload, timeoutMs = 30000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(payload),
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * 从 sessionKey 提取 agent ID 并构造工作区路径
 */
function getWorkspace(sessionKey, env) {
  const openclawDir = env.OPENCLAW_STATE_DIR || `${env.HOME || '~'}/.openclaw`;
  if (env.OPENCLAW_WORKSPACE) return env.OPENCLAW_WORKSPACE;
  if (sessionKey && typeof sessionKey === 'string') {
    const parts = sessionKey.split(':');
    if (parts.length >= 2 && parts[0] === 'agent') {
      return `${openclawDir}/workspace-${parts[1]}`;
    }
  }
  return `${openclawDir}/workspace`;
}

/**
 * 动态定位 scripts 目录
 */
function findScriptsDir(sessionKey, env, requiredFile = 'search.sh') {
  const openclawDir = env.OPENCLAW_STATE_DIR || `${env.HOME || '~'}/.openclaw`;
  const workspace = getWorkspace(sessionKey, env);
  return findScriptsDirByWorkspace(workspace, openclawDir, requiredFile);
}

/**
 * 根据 workspace 直接定位 scripts 目录（不依赖 sessionKey）
 * 供 agent_end 插件调用
 */
function findScriptsDirByWorkspace(workspace, openclawDir, requiredFile = 'search.sh') {
  const candidates = [
    join(workspace, 'skills', 'rocky-know-how', 'scripts'),
    join(workspace, 'scripts'),
    join(openclawDir, 'skills', 'rocky-know-how', 'scripts'),
    join(openclawDir, 'shared-skills', 'rocky-know-how', 'scripts'),
  ];
  for (const dir of candidates) {
    if (dir && existsSync(join(dir, requiredFile))) return dir;
  }
  return join(openclawDir, 'skills', 'rocky-know-how', 'scripts');
}

/**
 * 获取共享学习数据目录
 */
function getLearningsDir(env) {
  const openclawDir = env.OPENCLAW_STATE_DIR || `${env.HOME || '~'}/.openclaw`;
  return `${openclawDir}/.learnings`;
}

/**
 * 从 LLM API 响应中提取 assistant 消息
 * 支持 OpenAI completions 格式和 Anthropic messages 格式
 * @param {object} parsed - JSON.parse 后的响应
 * @returns {string} assistant 消息内容
 */
function extractAssistantMessage(parsed) {
  // Anthropic messages format: content[].text (优先，minimax 等)
  if (parsed.content && Array.isArray(parsed.content)) {
    // 优先找 text 类型的 block
    const textBlocks = parsed.content.filter(block => block.type === 'text' && block.text);
    if (textBlocks.length > 0) {
      return textBlocks.map(b => b.text).join('');
    }
    // minimax 有时只返回 thinking，没有 text
    const thinkingBlocks = parsed.content.filter(block => block.type === 'thinking' && block.thinking);
    if (thinkingBlocks.length > 0) {
      return thinkingBlocks.map(b => b.thinking).join('');
    }
  }
  // OpenAI format: choices[0].message.content
  if (parsed.choices?.[0]?.message?.content) {
    return parsed.choices[0].message.content;
  }
  // 国产模型 reasoning 字段 (glm-5, stepfun 等)
  if (parsed.choices?.[0]?.message?.reasoning_content) {
    return parsed.choices[0].message.reasoning_content;
  }
  if (parsed.choices?.[0]?.message?.reasoning) {
    return parsed.choices[0].message.reasoning;
  }
  return '';
}

/**
 * 从 event context 或 agent 配置解析 provider 信息
 * @param {object} event - hook event 对象
 * @param {object} ctx - hook ctx 对象（包含 agentId/sessionKey）
 * @returns {object|null} provider 信息
 */
function resolveProviderInfo(event, ctx) {
  const context = event?.context || {};
  let providerId = context.modelProviderId;
  let modelId = context.modelId;
  const homeDir = process.env.HOME || require('os').homedir() || '~';
  const ocStateDir = process.env.OPENCLAW_STATE_DIR || join(homeDir, '.openclaw');

  // 从 agent 配置反查 provider/model（hook context 缺失时补全）
  if (ctx?.agentId) {
    try {
      const openclawConfig = parseJSONLenient(readFileSync(join(ocStateDir, 'openclaw.json'), 'utf8'));
      const agents = openclawConfig?.agents?.list || [];
      const agent = agents.find(a => a.id === ctx.agentId);
      if (agent?.model) {
        // model 可能是字符串 "zai/glm-5.1" 或对象 { primary, fallbacks }
        const modelStr = typeof agent.model === 'string' ? agent.model : agent.model?.primary || '';
        if (modelStr.includes('/')) {
          const [pId, mId] = modelStr.split('/');
          providerId = providerId || pId;
          modelId = modelId || mId;
        }
      }
    } catch (e) {
      // 忽略，继续尝试其他方式
    }
  }

  if (!providerId) {
    console.log('[rocky-know-how] resolveProviderInfo: no providerId found, skipping');
    return null;
  }

  try {
    const openclawConfig = parseJSONLenient(readFileSync(join(ocStateDir, 'openclaw.json'), 'utf8'));
    const providers = openclawConfig?.models?.providers || {};
    const provider = providers[providerId];

    if (!provider) {
      console.log(`[rocky-know-how] resolveProviderInfo: provider ${providerId} not found in config`);
      return null;
    }

    if (!provider.baseUrl) {
      console.log(`[rocky-know-how] resolveProviderInfo: provider ${providerId} has no baseUrl`);
      return null;
    }

    // 根据 api 类型确定路径
    let apiPath = '/chat/completions';
    if (provider.api === 'anthropic-messages') {
      apiPath = '/v1/messages';
    }

    const apiKey = provider.apiKey || '';

    // OAuth provider (无 apiKey): 尝试从 auth-profiles.json 读取 token
    if (provider.authHeader && !apiKey) {
      try {
        const authProfilesPath = join(ocStateDir, 'agents', 'main', 'agent', 'auth-profiles.json');
        if (existsSync(authProfilesPath)) {
          const authStore = JSON.parse(readFileSync(authProfilesPath, 'utf8'));
          const profileId = `${providerId}:default`;
          const profile = authStore?.profiles?.[profileId];
          if (profile?.access) {
            const token = profile.access;
            console.log(`[rocky-know-how] resolveProviderInfo: ${providerId} using OAuth token from auth-profiles.json`);
            const apiUrl = `${provider.baseUrl}${apiPath}`;
            const model = modelId || provider.model || '';
            return { provider, providerId, apiUrl, apiKey: token, model };
          }
        }
      } catch (e) {
        console.log(`[rocky-know-how] resolveProviderInfo: failed to read OAuth token: ${e.message}`);
      }
      console.log(`[rocky-know-how] resolveProviderInfo: ${providerId} is OAuth (no apiKey), skipping LLM`);
      return null;
    }

    const apiUrl = `${provider.baseUrl}${apiPath}`;
    const model = modelId || provider.model || '';
    const api = provider.api || 'openai-completions';

    return { provider, providerId, apiUrl, apiKey, model, api };
  } catch (e) {
    console.log(`[rocky-know-how] resolveProviderInfo failed: ${e.message}`);
    return null;
  }
}

/**
 * 执行 auto-review.sh 全自动审核
 */
function runAutoReview(scriptsDir, learningsDir) {
  try {
    // 优先使用全局安装目录的 auto-review.sh，回退到传入的 scriptsDir
    const homeDir = process.env.HOME || require('os').homedir() || '~';
    const openclawDir = process.env.OPENCLAW_STATE_DIR || join(homeDir, '.openclaw');
    const globalScriptsDir = join(openclawDir, 'skills', 'rocky-know-how', 'scripts');
    const autoReviewScript = existsSync(join(globalScriptsDir, 'auto-review.sh'))
      ? join(globalScriptsDir, 'auto-review.sh')
      : join(scriptsDir, 'auto-review.sh');

    if (!existsSync(autoReviewScript)) {
      console.log('[rocky-know-how] auto-review.sh not found, skipping');
      return;
    }

    // 执行 auto-review.sh
    execSync(`bash "${autoReviewScript}"`, {
      cwd: learningsDir,
      stdio: 'pipe',
      timeout: 30000
    });
    console.log('[rocky-know-how] auto-review.sh completed');
  } catch (e) {
    console.log('[rocky-know-how] auto-review.sh failed:', e.message);
  }
}

/**
 * 根据 provider API 类型构建请求 payload
 */
function buildLLMPayload({ system, user, model, api, temperature = 0.1, maxTokens = 4096, extra = {} }) {
  if (api === 'anthropic-messages') {
    return { model, max_tokens: maxTokens, system, messages: [{ role: 'user', content: user }], ...extra };
  }
  // openai-completions 格式（默认）
  return { model, messages: [{ role: 'system', content: system }, { role: 'user', content: user }], temperature, max_tokens: maxTokens, ...extra };
}

/**
 * @param {string} type - "draft" 或 "formal"
 * @param {object} providerInfo - resolveProviderInfo() 返回的 provider 信息
 * @returns {object} { worth: boolean, reason: string, summary?: string, tags?: string[] }
 */
async function callLLMJudge(content, type, providerInfo) {
  if (!providerInfo?.apiUrl) {
    console.log('[rocky-know-how] callLLMJudge: no provider configured, skipping');
    return { worth: false, reason: '无模型配置' };
  }

  const { apiUrl, apiKey, model, api = 'openai-completions' } = providerInfo;

  let systemPrompt, userPrompt;

  if (type === 'draft') {
    systemPrompt = `你是一个经验诀窍判断助手。判断以下对话内容是否值得写入草稿经验。

判断标准:
- 有实际操作(工具调用) + 有问题或解决方案 → worth
- 只有闲聊、无关内容 → not worth

回复格式(仅输出JSON,不要其他内容):
{
  "worth": true或false,
  "reason": "判断理由(20字内)",
  "summary": "提取的问题/解决方案摘要(50字内)",
  "tags": ["tag1", "tag2"]
}`;
    userPrompt = `对话内容:
${content}`;
  } else {
    systemPrompt = `你是一个经验诀窍判断助手。判断并优化以下草稿内容。

任务:
1. 判断草稿是否值得写入正式经验
2. 如果值得,优化和增强解决方案,使其更完整、更实用

判断标准:
- 有具体问题 + 可优化 → worth
- 草稿质量低、重复、不完整 → not worth

优化要求:
- 补充遗漏的关键步骤
- 修正不准确的描述
- 增加预防措施和最佳实践
- 使解决方案可直接复用

回复格式(仅输出JSON,不要其他内容):
{
  "worth": true或false,
  "reason": "判断理由(20字内)",
  "solution": "优化后的完整解决方案(如worth=true则必填)",
  "prevention": "预防措施和最佳实践(如worth=true则必填)"
}`;
    userPrompt = `草稿内容:
${content}`;
  }

  try {
    const extra = {};
    // minimax-portal 使用 anthropic-messages API，需要显式禁用 thinking
    if (providerInfo.providerId === 'minimax-portal') {
      extra.thinking = { type: 'disabled' };
    }
    const payload = buildLLMPayload({ system: systemPrompt, user: userPrompt, model, api, temperature: 0.1, maxTokens: 4096, extra });

    const parsed = await callLLMApi(apiUrl, apiKey, payload, 60000);
    const assistantMsg = extractAssistantMessage(parsed);

    // 解析 JSON 响应
    const jsonMatch = assistantMsg.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
  } catch (e) {
    console.log(`[rocky-know-how] LLM judge failed: ${e.message}`);
  }

  // 默认返回不worth,避免误写
  return { worth: false, reason: 'LLM调用失败', llmFailed: true };
}

/**
 * 用 LLM 判断草稿应该新增还是追加到已有经验
 * @param {object} draft - 草稿对象
 * @param {object[]} similarExperiences - 相似经验列表
 * @param {object} providerInfo - resolveProviderInfo() 返回的 provider 信息
 * @returns {object} { action: "create" | "append", targetId?: string, reason: string, optimizedSolution?: string, optimizedPrevention?: string }
 */
async function decideCreateOrAppend(draft, similarExperiences, providerInfo) {
  if (!providerInfo?.apiUrl) {
    // 无配置，降级到关键词判断
    if (similarExperiences && similarExperiences.length > 0) {
      return { action: 'append', targetId: similarExperiences[0].id, reason: '无LLM配置，降级到关键词判断' };
    }
    return { action: 'create', reason: '无LLM配置且无相似经验' };
  }

  const { apiUrl, apiKey, model, api = 'openai-completions' } = providerInfo;

  // 构造相似经验上下文
  let similarCtx = '无相似经验';
  if (similarExperiences && similarExperiences.length > 0) {
    similarCtx = similarExperiences.slice(0, 3).map(exp =>
      `【经验 ${exp.id}】\n问题: ${exp.problem}\n方案: ${exp.solution}\n标签: ${(exp.tags || []).join(', ')}`
    ).join('\n\n');
  }

  const systemPrompt = `你是一个经验诀窍审核助手。判断草稿应该"新增经验"还是"追加到已有经验"。

判断标准:
- 草稿与已有经验问题本质相同/高度相似 → 追加到已有（补充新解决方案）
- 草稿问题独特，无类似经验 → 新增经验
- 已有经验解决方案已包含草稿方案 → 追加（补充另一种方式）
- 已有经验标签/领域相同但问题不同 → 新增经验

优化要求（追加时）:
- 补充遗漏的关键步骤
- 修正不准确的描述
- 给出更完整的预防措施

回复格式（仅输出JSON）:
{
  "action": "create"或"append",
  "targetId": "EXP-XXX（append时必填）",
  "reason": "判断理由（30字内）",
  "optimizedSolution": "优化后的完整解决方案（create和append时都必填）",
  "optimizedPrevention": "优化后的预防措施（create和append时都必填）"
}`;

  const userPrompt = `草稿内容:
问题: ${draft.problem || '无'}
踩坑过程: ${draft.tried || '无'}
解决方案: ${draft.solution || '待补充'}
标签: ${(draft.tags || []).join(', ')}

相似经验:
${similarCtx}`;

  try {
    const extra = {};
    // minimax-portal 使用 anthropic-messages API，需要显式禁用 thinking
    if (providerInfo.providerId === 'minimax-portal') {
      extra.thinking = { type: 'disabled' };
    }
    const payload = buildLLMPayload({ system: systemPrompt, user: userPrompt, model, api, temperature: 0.1, maxTokens: 4096, extra });

    const parsed = await callLLMApi(apiUrl, apiKey, payload, 60000);
    const assistantMsg = extractAssistantMessage(parsed);
    const jsonMatch = assistantMsg.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
  } catch (e) {
    console.log(`[rocky-know-how] decideCreateOrAppend LLM failed: ${e.message}`);
  }

  // LLM 失败，降级到关键词
  if (similarExperiences && similarExperiences.length > 0) {
    return { action: 'append', targetId: similarExperiences[0].id, reason: 'LLM失败，降级关键词', llmFailed: true };
  }
  return { action: 'create', reason: 'LLM失败且无相似经验', llmFailed: true };
}

/**
 * 解析 experiences.md 为结构化条目
 */
function parseExperiences(content) {
  const entries = [];
  // 按 ## [EXP- 分割
  const blocks = content.split(/(?=^## \[EXP-)/m);
  for (const block of blocks) {
    const idMatch = block.match(/^## \[(EXP-\d{8}-\d{3})\]/);
    if (!idMatch) continue;
    const id = idMatch[1];
    const problem = block.match(/(?:\*\*问题\*\*:\s*|### 问题\s*\n)(.+)/i)?.[1]?.trim() || '';
    const solution = block.match(/(?:\*\*正确方案\*\*:\s*|### 正确方案\s*\n)([\s\S]+?)(?=\n###|\n\*\*|\n##|$)/i)?.[1]?.trim() || '';
    const tagsMatch = block.match(/\*\*Tags\*\*:\s*(.+)/i)?.[1];
    const tags = tagsMatch ? tagsMatch.split(',').map(t => t.trim().replace(/^"|"$/g, '')) : [];
    entries.push({ id, problem, solution, tags, block });
  }
  return entries;
}

/**
 * 搜索相似经验并读取完整内容（Node.js 内存直接搜索，无需 shell 调用）
 * @param {string} scriptsDir - scripts 目录（保留参数兼容）
 * @param {string} keywords - 搜索关键词
 * @returns {object[]} 相似经验列表 [{id, problem, solution, tags, area}, ...]
 */
function searchSimilarExperiences(scriptsDir, keywords) {
  try {
    const experiencesFile = join(getLearningsDir(process.env), 'experiences.md');
    if (!existsSync(experiencesFile)) return [];
    if (!keywords || keywords.trim().length === 0) return [];

    const content = readFileSync(experiencesFile, 'utf8');
    const entries = parseExperiences(content);

    const kwList = keywords.split(/\s+/).filter(k => k.length > 0);
    if (kwList.length === 0) return [];

    // 评分：每个关键词命中 +1 分，全入搜索（不截断）
    const scored = [];
    for (const entry of entries) {
      const text = entry.block.toLowerCase();
      let score = 0;
      for (const kw of kwList) {
        if (text.includes(kw.toLowerCase())) score++;
      }
      if (score > 0) {
        scored.push({ ...entry, score });
      }
    }

    // 按匹配度降序，取前5
    scored.sort((a, b) => b.score - a.score);
    const top = scored.slice(0, 5);

    return top.map(e => ({
      id: e.id,
      problem: e.problem,
      solution: e.solution,
      tags: e.tags
    }));
  } catch (e) {
    console.log(`[rocky-know-how] searchSimilarExperiences failed: ${e.message}`);
    return [];
  }
}

/**
 * 从任务推断领域
 */
function inferArea(task) {
  if (!task) return 'global';
  const lower = task.toLowerCase();
  if (/nginx|apache|web|server|mysql|redis|mongodb|docker|k8s|kubernetes/i.test(lower)) return 'infra';
  if (/php|java|python|code|git|merge|compile|build/i.test(lower)) return 'code';
  if (/wechat|weixin|wx|公众号|小程序/i.test(lower)) return 'wx.newstt';
  if (/test|测试|qa/i.test(lower)) return 'test';
  return 'global';
}

/**
 * 生成提醒文本(用于注入 systemPrompt)
 * 含经验库动态统计
 */
function generateReminder(scriptsDir, learningsDir) {
  let totalEntries = 0, thisMonthEntries = 0;
  let recentEntries = [], topTags = [];
  let lastScanInfo = null;

  try {
    const ef = join(learningsDir, 'experiences.md');
    if (existsSync(ef)) {
      const content = readFileSync(ef, 'utf8');
      const expMatches = content.match(/^## \[EXP-/gm);
      totalEntries = expMatches ? expMatches.length : 0;

      const currentMonth = new Date().toISOString().slice(0, 7);
      thisMonthEntries = (content.match(new RegExp(`^## \\[EXP-${currentMonth.replace('-', '')}`, 'gm')) || []).length;

      const allExps = content.match(/^## \[EXP-\d{8}-\d{3}\] .+$/gm);
      if (allExps) {
        recentEntries = allExps.slice(-5).map(l => l.replace(/^## \[/, '').replace(']', ': '));
      }

      const tagMatches = content.match(/\*\*Tags\*\*:[^\S\n]*(.+)$/gm);
      if (tagMatches) {
        const tagCounts = {};
        tagMatches.forEach(tm => {
          tm.replace(/\*\*Tags\*\*:\s*/, '').split(',').forEach(t => {
            const tag = t.trim();
            if (tag) tagCounts[tag] = (tagCounts[tag] || 0) + 1;
          });
        });
        topTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([t, c]) => `${t}(${c})`);
      }
    }
  } catch (e) {}

  try {
    const lf = join(learningsDir, '.last-scan.json');
    if (existsSync(lf)) {
      lastScanInfo = JSON.parse(readFileSync(lf, 'utf8'));
    }
  } catch (e) {}

  const activityLine = lastScanInfo && lastScanInfo.processedCount > 0
    ? `\n📌 上次会话处理:\n` +
      (lastScanInfo.created?.length > 0 ? `  ✨ 新增 ${lastScanInfo.created.length} 条: ${lastScanInfo.created.map(r => r.title).join('、')}\n` : '') +
      (lastScanInfo.appended?.length > 0 ? `  🔄 优化 ${lastScanInfo.appended.length} 条: ${lastScanInfo.appended.map(r => r.title).join('、')}\n` : '')
    : '';

  return `
## 📚 经验诀窍提醒 (rocky-know-how) v3.3.0

📊 本地经验库: ${totalEntries} 条经验 (本月新增 ${thisMonthEntries} 条)${activityLine}

${recentEntries.length > 0 ? `📋 最近经验:\n  ${recentEntries.join('\n  ')}` : ''}
${topTags.length > 0 ? `\n🏷️ 热门标签: ${topTags.join(', ')}` : ''}

**失败≥2次时** → 执行搜经验诀窍:
\`\`\`bash
bash ${scriptsDir}/search.sh "关键词1" "关键词2"
\`\`\`
命中 → 读"正确方案"和"预防",按答案执行。
没命中 → 继续自己排查。

**失败≥2次后成功** → 执行写入经验诀窍:
\`\`\`bash
bash ${scriptsDir}/record.sh "问题一句话" "踩坑过程" "正确方案" "预防措施" "tag1,tag2" "area"
\`\`\`
area 可选: frontend|backend|infra|tests|docs|config (默认: infra)

**其他命令**:
- \`${scriptsDir}/search.sh --all\` - 查看全部
- \`${scriptsDir}/search.sh --preview "关键词"\` - 摘要模式
- \`${scriptsDir}/stats.sh\` - 统计面板
- \`${scriptsDir}/promote.sh\` - Tag晋升检查

**重要**: 经验诀窍存储在 ~/.openclaw/.learnings/(全局共享),所有 agent 通用。
`;
}


/**
 * 扫描指定 workspace 的 memory 目录，提取并处理经验候选
 * 供 bootstrap handler 和 agent_end 插件共用
 */
async function processMemoryDir(workspace, env, scriptsDir, providerInfo) {
  const memoryDir = join(workspace, 'memory');
  const learningsDir = getLearningsDir(env);
  const markerFile = join(learningsDir, '.memory-sizes.json');

  if (!existsSync(memoryDir)) return;

  // 只处理当天文件（memoryFlush 只写入当天文件）
  const today = new Date().toISOString().slice(0, 10);
  const todayFile = today + '.md';
  const filePath = join(memoryDir, todayFile);
  if (!existsSync(filePath)) return;

  // 读取已记录的文件大小（key 含 workspace 前缀，隔离不同工作区）
  let sizeMap = {};
  try {
    if (existsSync(markerFile)) sizeMap = JSON.parse(readFileSync(markerFile, 'utf8'));
  } catch (e) {}

  const wsName = workspace.split('/').pop() || workspace;
  const sizeKey = wsName + '/' + todayFile;
  try {
    const currentSize = statSync(filePath).size;
    if (currentSize === (sizeMap[sizeKey] || 0)) return;

    console.log(`[rocky-know-how] detected change in ${wsName}/${todayFile}`);

    const content = readFileSync(filePath, 'utf8');
    if (!content || content.trim().length < 50) return;

    const candidates = extractExperienceCandidates(content, today);
    if (candidates.length === 0) return;

    console.log(`[rocky-know-how] found ${candidates.length} experience candidate(s) in ${todayFile}`);

    let processedCount = 0;
    const results = [];
    for (const candidate of candidates) {
      try {
        const result = await processCandidate(candidate, scriptsDir, learningsDir, providerInfo);
        if (result) results.push(result);
        processedCount++;
      } catch (e) {
        console.log(`[rocky-know-how] candidate processing error: ${e.message}`);
      }
    }

    // 更新大小记录（仅记录已处理的）
    sizeMap[sizeKey] = currentSize;
    try { writeFileSync(markerFile, JSON.stringify(sizeMap), 'utf8'); } catch (e) {}

    if (processedCount > 0) {
      console.log(`[rocky-know-how] memory scan complete, processed ${processedCount} experience(s)`);
      // 记录本次扫描活动，供 generateReminder 展示
      try {
        const created = results.filter(r => r.action === 'create');
        const appended = results.filter(r => r.action === 'append');
        writeFileSync(join(learningsDir, '.last-scan.json'), JSON.stringify({
          timestamp: new Date().toISOString(),
          processedCount,
          wsName,
          date: today,
          created: created.map(r => ({ title: r.title })),
          appended: appended.map(r => ({ title: r.title, targetId: r.targetId }))
        }), 'utf8');
      } catch (e) {}
    }
  } catch (e) {
    console.log(`[rocky-know-how] error reading ${todayFile}: ${e.message}`);
  }
}

/**
 * 【bootstrap 入口】从 sessionKey 解析 workspace，扫描 memory 提取经验
 */
async function scanMemoryForExperiences(sessionKey, env, scriptsDir, event, agentId) {
  const workspace = getWorkspace(sessionKey, env);
  const providerInfo = resolveProviderInfo(event, { agentId });
  await processMemoryDir(workspace, env, scriptsDir, providerInfo);
}

/**
 * 处理 memory 提取的经验候选：AI 全权判断新增、优化增强、还是跳过
 */
async function processCandidate(candidate, scriptsDir, learningsDir, providerInfo) {
  const title = candidate.title || '';
  const tags = candidate.tags || [];
  const solution = candidate.solution || '';

  // 无 LLM 则跳过（全部由 AI 判断，无关键词降级）
  if (!providerInfo) {
    console.log(`[rocky-know-how] No LLM available, skipped: ${title}`);
    return { action: 'skip', title, reason: 'no_llm' };
  }

  // LLM 判断：新增、优化增强、还是跳过
  const summary = `任务: ${title}\n标签: ${tags.join(', ') || '无'}`;
  const judgeResult = await callLLMJudge(summary, 'draft', providerInfo);

  if (judgeResult.llmFailed || !judgeResult.worth) {
    console.log(`[rocky-know-how] LLM: not worth, skipped: ${title}`);
    return { action: 'skip', title, reason: 'not_worth' };
  }

  const problem = judgeResult.summary || title;
  const decisionTags = judgeResult.tags || tags;

  // LLM 决定新增还是追加到已有经验
  const keywords = decisionTags.slice(0, 3).join(' ');
  const similarExperiences = searchSimilarExperiences(scriptsDir, keywords);
  const draftContent = { problem, tried: '', solution, tags: decisionTags };
  const decision = await decideCreateOrAppend(draftContent, similarExperiences, providerInfo);

  if (decision.llmFailed) {
    console.log(`[rocky-know-how] LLM decision failed, skipped: ${title}`);
    return { action: 'skip', title, reason: 'decision_failed' };
  }

  if (decision.action === 'append' && decision.targetId) {
    const sol = decision.optimizedSolution || solution;
    execSync(`bash "${join(scriptsDir, 'append-record.sh')}" "${shellEscape(decision.targetId)}" "${shellEscape(sol)}" "${shellEscape(decisionTags.join(','))}"`, {
      cwd: learningsDir, stdio: 'pipe', timeout: 15000
    });
    console.log(`[rocky-know-how] AI: appended to ${decision.targetId}`);
    return { action: 'append', title: problem, targetId: decision.targetId };
  } else {
    const sol = decision.optimizedSolution || solution;
    const prev = decision.optimizedPrevention || '';
    const area = inferArea(problem);
    execSync(`bash "${join(scriptsDir, 'record.sh')}" "${shellEscape(problem)}" "" "${shellEscape(sol)}" "${shellEscape(prev)}" "${shellEscape(decisionTags.join(','))}" "${shellEscape(area)}"`, {
      cwd: learningsDir, stdio: 'pipe', timeout: 15000
    });
    console.log(`[rocky-know-how] AI: created new experience`);
    return { action: 'create', title: problem };
  }
}

/**
 * 从 memory 日志内容中提取经验候选
 * 查找包含经验教训、踩坑、解决方案的段落
 */
function extractExperienceCandidates(content, fileDate) {
  const candidates = [];
  const lines = content.split('\n');

  let currentSection = '';
  let currentContent = [];
  let inExperienceSection = false;

  // 经验相关标题关键词
  const expKeywords = [
    '经验', '教训', '踩坑', '总结', '解决方案', '关键发现', '根因',
    '修复', '排查', '故障', 'troubleshoot', 'fix', 'solution', 'lesson',
    'pitfall', 'resolved', '注意事项', '避坑', '坑'
  ];

  // 跳过关键词（不是经验的段落）
  const skipKeywords = ['TODO', '待办', '待处理'];

  for (const line of lines) {
    const trimmed = line.trim();

    // 检测标题行 (## or ###)
    if (/^#{1,4}\s+/.test(trimmed)) {
      // 保存上一个段落
      if (inExperienceSection && currentContent.length > 0) {
        const sectionText = currentContent.join('\n').trim();
        if (sectionText.length > 30) {
          const title = currentSection.replace(/^#{1,4}\s+/, '').trim();
          if (title.length > 2 && !skipKeywords.some(k => title.includes(k))) {
            candidates.push({
              title: `[${fileDate}] ${title}`,
              solution: sectionText.slice(0, 500),
              tags: extractTagsFromText(sectionText)
            });
          }
        }
      }

      // 开始新段落
      currentSection = trimmed;
      currentContent = [];
      inExperienceSection = expKeywords.some(k =>
        trimmed.toLowerCase().includes(k.toLowerCase())
      );
    } else if (inExperienceSection) {
      currentContent.push(line);
    }
  }

  // 处理最后一个段落
  if (inExperienceSection && currentContent.length > 0) {
    const sectionText = currentContent.join('\n').trim();
    if (sectionText.length > 30) {
      const title = currentSection.replace(/^#{1,4}\s+/, '').trim();
      if (title.length > 2 && !skipKeywords.some(k => title.includes(k))) {
        candidates.push({
          title: `[${fileDate}] ${title}`,
          solution: sectionText.slice(0, 500),
          tags: extractTagsFromText(sectionText)
        });
      }
    }
  }

  return candidates;
}

/**
 * 从文本中提取标签
 */
function extractTagsFromText(text) {
  const tags = new Set();
  const tagMap = {
    'docker': 'docker', 'nginx': 'nginx', 'php': 'php', 'redis': 'redis',
    'ssh': 'ssh', 'git': 'git', 'mysql': 'mysql', 'upload': 'upload',
    '502': '502', '503': '503', 'timeout': 'timeout', 'error': 'error',
    'vps': 'infra', '服务器': 'infra', '部署': 'deploy', 'deploy': 'deploy',
    'ssl': 'ssl', 'https': 'ssl', '证书': 'ssl',
    'frp': 'frp', 'proxy': 'proxy', '代理': 'proxy',
    '微信公众号': 'wechat', '公众号': 'wechat', 'wechat': 'wechat',
    'openclaw': 'openclaw', 'hook': 'hook', 'plugin': 'plugin',
    'mac': 'macos', 'macos': 'macos', 'launchctl': 'macos',
    '宝塔': 'bt-panel'
  };

  const lowerText = text.toLowerCase();
  for (const [keyword, tag] of Object.entries(tagMap)) {
    if (lowerText.includes(keyword)) {
      tags.add(tag);
    }
  }

  return Array.from(tags).slice(0, 5);
}

// ============================================================
// 主 Handler
// ============================================================
const handler = async (event, ctx) => {
  if (!event || typeof event !== 'object') return;

  const sessionKey = event.sessionKey || ctx?.sessionKey || '';
  const env = process.env;
  const agentId = ctx?.agentId || '';

  // 跳过子 agent
  if (sessionKey.includes(':subagent:')) return;

  const eventType = event.type;
  const eventAction = event.action;

  // agent/bootstrap - 启动时注入经验提醒 + 扫描 memory 提取经验
  if (eventType === 'agent' && eventAction === 'bootstrap') {
    console.log(`[🔔 rocky-know-how][${new Date().toISOString()}] bootstrap TRIGGERED`);
    if (!event.context || typeof event.context !== 'object') return;

    const scriptsDir = findScriptsDir(sessionKey, env);
    const learningsDir = getLearningsDir(env);

    // 先扫描 memory，确保 .last-scan.json 是最新的
    try {
      await scanMemoryForExperiences(sessionKey, env, scriptsDir, event, agentId);
    } catch (e) {
      console.log(`[rocky-know-how] bootstrap: memory scan error: ${e.message}`);
    }

    // 再生成提醒（含最新扫描统计）
    const reminder = generateReminder(scriptsDir, learningsDir);

    if (event.context.systemPrompt !== undefined) {
      event.context.systemPrompt += reminder;
    } else if (Array.isArray(event.context.messages)) {
      event.context.messages.push({ role: 'system', content: reminder });
    }

    return;
  }
};

// 直接导出为对象，handler 和 default 都是函数本身
const h = handler;
module.exports = {
  handler: h,
  default: h,
  processMemoryDir,
  findScriptsDirByWorkspace,
  getLearningsDir,
  getWorkspace,
  resolveProviderInfo,
  generateReminder,
  callLLMJudge,
  decideCreateOrAppend,
  processCandidate
};
