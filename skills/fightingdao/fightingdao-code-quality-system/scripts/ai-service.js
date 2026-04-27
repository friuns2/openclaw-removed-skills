/**
 * AI 服务调用模块
 * 从 openclaw.json 读取配置，调用 AI API
 */

const https = require('https');
const http = require('http');

// 从 openclaw.json 加载配置
function loadAIConfig() {
  const fs = require('fs');
  const path = require('path');
  
  const configPath = path.join(process.env.HOME, '.openclaw/openclaw.json');
  
  if (!fs.existsSync(configPath)) {
    throw new Error('openclaw.json 配置文件不存在');
  }
  
  const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  const providers = config.models?.providers || {};
  
  // 优先使用 bailian 提供商
  const bailian = providers.bailian;
  if (!bailian) {
    throw new Error('未找到 bailian 提供商配置');
  }
  
  return {
    baseUrl: bailian.baseUrl,
    apiKey: bailian.apiKey,
    // 默认使用 glm-5（与当前主模型一致）
    // 代码审查可以用 kimi-k2.5（更大的上下文窗口）
    models: {
      default: 'glm-5',
      codeReview: 'kimi-k2.5',  // 代码审查用更大的上下文
      scoring: 'glm-5'
    }
  };
}

/**
 * 调用 AI API
 * @param {string} prompt 提示词
 * @param {string} model 模型 ID
 * @returns {Promise<string>} AI 响应
 */
async function callAI(prompt, model = 'glm-5') {
  const config = loadAIConfig();
  
  const url = new URL('/chat/completions', config.baseUrl);
  const isHttps = url.protocol === 'https:';
  const client = isHttps ? https : http;
  
  const requestBody = JSON.stringify({
    model: model,
    messages: [
      {
        role: 'user',
        content: prompt
      }
    ],
    temperature: 0.7,
    max_tokens: 4096
  });
  
  return new Promise((resolve, reject) => {
    const req = client.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.apiKey}`
      }
    }, (res) => {
      let data = '';
      
      res.on('data', chunk => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (json.error) {
            reject(new Error(`AI API 错误: ${json.error.message || JSON.stringify(json.error)}`));
          } else {
            resolve(json.choices[0]?.message?.content || '');
          }
        } catch (err) {
          reject(new Error(`解析响应失败: ${err.message}\n响应: ${data}`));
        }
      });
    });
    
    req.on('error', reject);
    req.write(requestBody);
    req.end();
  });
}

/**
 * AI 代码审查
 * @param {Object} params 参数
 * @param {string} params.projectName 项目名
 * @param {string} params.branch 分支名
 * @param {Array} params.fileChanges 文件变更列表
 * @param {Object} params.stats 统计数据
 * @returns {Promise<Array>} 问题列表
 */
async function reviewCode(params) {
  const { projectName, branch, fileChanges, stats } = params;
  
  const prompt = `你是一位资深代码审查专家。请审查以下代码变更，找出潜在问题。

## 项目信息
- 项目名：${projectName}
- 分支：${branch}
- 变更文件数：${fileChanges.length}
- 新增行数：${stats.insertions}
- 删除行数：${stats.deletions}

## 文件变更列表
${fileChanges.slice(0, 20).map(f => `- ${f.path}: +${f.insertions}/-${f.deletions}`).join('\n')}

## 审查要求
请按以下维度审查，每个问题包含：
1. filePath: 文件路径
2. lineStart: 行号（可空）
3. type: 问题类型（maintainability/performance/security/error_handling/code_quality/best_practice）
4. severity: 严重程度（P0/P1/P2）
5. description: 问题描述
6. suggestion: 修改建议
7. committerName: 提交人（可填"未知"）

## 输出格式
请输出 JSON 数组，每个元素代表一个问题：
[
  {
    "filePath": "src/example.ts",
    "lineStart": null,
    "type": "maintainability",
    "severity": "P2",
    "description": "问题描述",
    "suggestion": "修改建议",
    "committerName": "未知"
  }
]

注意：
- 只输出 JSON 数组，不要有其他文字
- 问题数量控制在 3-10 个
- 关注真正重要的问题，不要吹毛求疵`;

  try {
    const response = await callAI(prompt, 'kimi-k2.5');
    
    // 解析 JSON
    const jsonMatch = response.match(/\[[\s\S]*\]/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    
    console.error('AI 响应格式错误，无法解析 JSON');
    return [];
  } catch (err) {
    console.error('AI 代码审查失败:', err.message);
    return [];
  }
}

/**
 * AI 质量评分
 * @param {Object} params 参数
 * @param {string} params.username 用户名
 * @param {string} params.projectName 项目名
 * @param {Object} params.stats 统计数据
 * @returns {Promise<Object>} 评分结果
 */
async function scoreQuality(params) {
  const { username, projectName, stats } = params;
  
  const prompt = `你是一位代码质量评审专家。请根据以下数据给出代码质量评分。

## 开发者信息
- 用户名：${username}
- 项目：${projectName}

## 本周数据
- 提交数：${stats.commitCount}
- 新增行数：${stats.insertions}
- 删除行数：${stats.deletions}
- 净增长：${stats.insertions - stats.deletions}
- 变更文件数：${stats.filesChanged}
- 任务数：${stats.taskCount || 0}

## 提交类型分布
${Object.entries(stats.commitTypes || {}).map(([type, count]) => `- ${type}: ${count}`).join('\n')}

## 评分标准（满分 10 分）
- 代码规范（20%）：Commit message 规范性
- 可维护性（25%）：重构意识、代码结构
- 代码质量（25%）：功能实现、错误处理
- 提交质量（15%）：提交粒度、类型分布
- 工作量（15%）：代码产出量

## 输出格式
请输出 JSON：
{
  "score": 8.5,
  "evaluation": "良好",
  "issues": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"],
  "advantages": ["亮点1", "亮点2"]
}

注意：只输出 JSON，不要有其他文字`;

  try {
    const response = await callAI(prompt, 'glm-5');
    
    // 解析 JSON
    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const result = JSON.parse(jsonMatch[0]);
      return {
        score: result.score || 7.0,
        evaluation: result.evaluation || '良好',
        issues: result.issues || [],
        suggestions: result.suggestions || [],
        advantages: result.advantages || []
      };
    }
    
    return getDefaultScore();
  } catch (err) {
    console.error('AI 评分失败:', err.message);
    return getDefaultScore();
  }
}

/**
 * 获取默认评分
 */
function getDefaultScore() {
  return {
    score: 7.0,
    evaluation: '良好',
    issues: [],
    suggestions: ['继续保持代码质量'],
    advantages: ['按时完成开发任务']
  };
}

/**
 * 生成 AI 质量报告文本
 */
function generateQualityReport(result) {
  return `## 代码质量报告

### 总体评价：${result.evaluation}

### 评分：${result.score}/10

### 主要问题
${result.issues.length > 0 ? result.issues.map((i, idx) => `${idx + 1}. ${i}`).join('\n') : '暂无主要问题'}

### 改进建议
${result.suggestions.length > 0 ? result.suggestions.map((s, idx) => `${idx + 1}. ${s}`).join('\n') : '暂无改进建议'}

### 亮点
${result.advantages.length > 0 ? result.advantages.map((a, idx) => `${idx + 1}. ${a}`).join('\n') : '暂无亮点'}`;
}

module.exports = {
  loadAIConfig,
  callAI,
  reviewCode,
  scoreQuality,
  generateQualityReport
};