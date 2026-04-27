#!/usr/bin/env node
/**
 * 360Teams 消息通知脚本
 * 用于在代码质量评审完成后向群组推送消息
 * 
 * 用法：
 *   node notify-teams.js <analysis-file-path>
 *   node notify-teams.js /path/to/analysis-20260326.json
 * 
 * 配置：
 *   需要在技能目录下创建 config.json，配置 teams 部分：
 *   {
 *     "teams": {
 *       "webhookUrl": "https://your-teams-server.com/api/robot/send?access_token=xxx",
 *       "secret": "your-teams-secret"
 *     }
 *   }
 */

const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 配置文件路径
const CONFIG_PATH = path.join(__dirname, '..', 'config.json');

// 默认配置
const API_BASE_URL = 'http://localhost:3000/api/v1';
const BOT_NAME = '质检君';

// 读取配置
function loadConfig() {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
      return config;
    }
  } catch (e) {
    console.error('❌ 配置文件读取失败:', e.message);
  }
  return {};
}

/**
 * 生成加签
 */
function generateSign(timestamp, secret) {
  const stringToSign = `${timestamp}\n${secret}`;
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(stringToSign);
  const sign = encodeURIComponent(hmac.digest('base64').replace(/\+/g, '-').replace(/\//g, '_'));
  return sign;
}

/**
 * 发送消息到 360Teams
 */
function sendToTeams(message, webhookUrl, secret) {
  return new Promise((resolve, reject) => {
    const timestamp = Date.now();
    const sign = generateSign(timestamp, secret);
    
    // 在 webhookUrl 后面追加 sign 和 timestamp 参数
    const separator = webhookUrl.includes('?') ? '&' : '?';
    const fullUrl = `${webhookUrl}${separator}timestamp=${timestamp}&sign=${sign}`;
    
    const parsedUrl = new URL(fullUrl);
    
    const options = {
      hostname: parsedUrl.hostname,
      port: 443,
      path: parsedUrl.pathname + parsedUrl.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            resolve({ raw: data });
          }
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.write(JSON.stringify(message));
    req.end();
  });
}

/**
 * 从 API 获取有效用户列表
 */
function getValidUsers() {
  try {
    const result = execSync(`curl -s "${API_BASE_URL}/teams/user-names"`, { encoding: 'utf-8' });
    const data = JSON.parse(result);
    if (data.success && data.data) {
      return new Set(data.data);
    }
    return new Set();
  } catch (err) {
    console.error('获取用户列表失败:', err.message);
    return new Set();
  }
}

/**
 * 生成代码评审完成的消息
 */
function generateReviewMessage(analysisData, validUsers) {
  const periodType = analysisData.periodType === 'week' ? '周' : '月';
  const periodValue = analysisData.periodValue;
  
  // 过滤有效用户
  let analyses = analysisData.analyses || [];
  if (validUsers.size > 0) {
    analyses = analyses.filter(a => validUsers.has(a.user?.username));
  }
  
  // 计算统计数据
  const totalProjects = new Set(analyses.map(a => a.projectName)).size;
  const totalUsers = new Set(analyses.map(a => a.user?.username)).size;
  const totalCommits = analyses.reduce((sum, a) => sum + (a.stats?.commitCount || 0), 0);
  const totalInsertions = analyses.reduce((sum, a) => sum + (a.stats?.insertions || 0), 0);
  const totalDeletions = analyses.reduce((sum, a) => sum + (a.stats?.deletions || 0), 0);
  const totalTasks = analyses.reduce((sum, a) => sum + (a.stats?.taskCount || 0), 0);

  // 格式化周期值
  let periodDisplay = periodValue;
  if (periodType === '周' && periodValue.length === 8) {
    const year = periodValue.substring(0, 4);
    const month = periodValue.substring(4, 6);
    const day = periodValue.substring(6, 8);
    periodDisplay = `${year}年${month}月${day}日（周四）所在周`;
  } else if (periodType === '月' && periodValue.length === 6) {
    const year = periodValue.substring(0, 4);
    const month = periodValue.substring(4, 6);
    periodDisplay = `${year}年${month}月`;
  }

  // 生成提交排行
  const topCommitters = generateTopCommittersText(analyses);

  // 构建消息内容
  const content = `📊 代码质量评审完成

评审周期：${periodDisplay}

📈 整体统计
• 涉及项目：${totalProjects} 个
• 参与人数：${totalUsers} 人
• 提交次数：${totalCommits} 次
• 新增代码：+${totalInsertions.toLocaleString()} 行
• 删除代码：-${totalDeletions.toLocaleString()} 行
• 关联任务：${totalTasks} 个

🏆 提交排行 TOP 5
${topCommitters}

详细报告请查看：代码质量分析系统

本消息由 ${BOT_NAME} 自动发送`;

  return {
    msgId: Date.now().toString(),
    msgtype: 'text',
    text: {
      content: content
    },
    at: {
      isAtAll: true,
      userIds: []
    }
  };
}

/**
 * 生成提交排行
 */
function generateTopCommittersText(analyses) {
  const userStats = new Map();
  
  for (const a of analyses) {
    const username = a.user?.username;
    if (!username) continue;
    
    if (!userStats.has(username)) {
      userStats.set(username, { commits: 0, tasks: 0 });
    }
    const stats = userStats.get(username);
    stats.commits += a.stats?.commitCount || 0;
    stats.tasks += a.stats?.taskCount || 0;
  }

  const sorted = Array.from(userStats.entries())
    .sort((a, b) => b[1].commits - a[1].commits)
    .slice(0, 5);

  if (sorted.length === 0) {
    return '暂无数据';
  }

  return sorted.map(([name, stats], index) => {
    const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
    return `${medal} ${name}：${stats.commits} 次提交，${stats.tasks} 个任务`;
  }).join('\n');
}

/**
 * 主函数
 */
async function main() {
  const analysisFile = process.argv[2];
  
  if (!analysisFile) {
    console.error('用法: node notify-teams.js <analysis-file-path>');
    console.error('示例: node notify-teams.js ../analysis-output/analysis-20260326.json');
    process.exit(1);
  }

  if (!fs.existsSync(analysisFile)) {
    console.error(`❌ 分析文件不存在: ${analysisFile}`);
    process.exit(1);
  }

  // 加载配置
  const config = loadConfig();
  
  if (!config.teams?.webhookUrl) {
    console.error('❌ 缺少 Teams 配置！');
    console.error('请在 config.json 中配置 teams.webhookUrl');
    process.exit(1);
  }
  
  if (!config.teams?.secret) {
    console.error('❌ 缺少 Teams secret！');
    console.error('请在 config.json 中配置 teams.secret');
    process.exit(1);
  }

  const analysisData = JSON.parse(fs.readFileSync(analysisFile, 'utf-8'));
  
  console.log('📤 正在发送消息到 360Teams...');
  console.log(`   机器人: ${BOT_NAME}`);
  console.log(`   周期: ${analysisData.periodType} ${analysisData.periodValue}`);
  
  // 获取有效用户列表
  console.log('   正在获取有效用户列表...');
  const validUsers = getValidUsers();
  console.log(`   有效用户: ${validUsers.size} 人`);
  
  try {
    const message = generateReviewMessage(analysisData, validUsers);
    const result = await sendToTeams(message, config.teams.webhookUrl, config.teams.secret);
    
    if (result.success === true) {
      console.log('✅ 消息发送成功！');
    } else {
      console.log('⚠️ 消息发送返回:', JSON.stringify(result));
    }
  } catch (err) {
    console.error('❌ 消息发送失败:', err.message);
    process.exit(1);
  }
}

main();