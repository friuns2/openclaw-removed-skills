#!/usr/bin/env node
/**
 * 邮件周报发送脚本
 * 用于在代码质量分析完成后发送邮件报告
 * 
 * 用法：
 *   在 backend 目录运行: node ../scripts/notify-email.js 20260402
 *   或: cd code-quality-backend && node ../scripts/notify-email.js 20260402
 * 
 * 配置文件：~/.openclaw/workspace/.email-config.json
 */

const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');

// 配置文件路径
const CONFIG_PATH = path.join(process.env.HOME, '.openclaw/workspace/.email-config.json');

/**
 * 读取邮件配置
 */
function loadEmailConfig() {
  try {
    const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
    return config;
  } catch (err) {
    console.error('❌ 邮件配置文件不存在或格式错误');
    console.error('请创建配置文件:', CONFIG_PATH);
    process.exit(1);
  }
}

/**
 * 创建邮件传输器
 */
function createTransporter(config) {
  // 兼容两种配置格式
  const smtpConfig = config.smtp || {};
  const user = smtpConfig.user || config.from;
  const pass = smtpConfig.pass || config.authCode;
  
  return nodemailer.createTransport({
    host: smtpConfig.host || 'smtp.qq.com',
    port: smtpConfig.port || 465,
    secure: smtpConfig.secure !== false,
    auth: { user, pass }
  });
}

/**
 * 获取发件人信息
 */
function getSenderInfo(config) {
  return {
    email: config.sender?.email || config.from,
    name: config.sender?.name || config.fromName || '代码质量分析系统'
  };
}

/**
 * 获取收件人列表
 */
function getRecipients(config) {
  return config.recipients || config.to || ['772744815@qq.com'];
}

/**
 * 格式化日期
 */
function formatDate(periodValue) {
  if (periodValue.length === 8) {
    const year = periodValue.substring(0, 4);
    const month = periodValue.substring(4, 6);
    const day = periodValue.substring(6, 8);
    return `${year}年${month}月${day}日`;
  }
  return periodValue;
}

/**
 * 生成 HTML 邮件内容
 */
function generateEmailHtml(analyses, periodValue) {
  if (!analyses || analyses.length === 0) {
    return `<p>本周暂无代码提交数据。</p>`;
  }
  
  // 计算统计数据
  const totalCommits = analyses.reduce((sum, a) => sum + a.commitCount, 0);
  const totalInsertions = analyses.reduce((sum, a) => sum + a.insertions, 0);
  const totalDeletions = analyses.reduce((sum, a) => sum + a.deletions, 0);
  const totalNet = totalInsertions - totalDeletions;
  const projectCount = new Set(analyses.map(a => a.project?.id || a.projectId)).size;
  const userCount = new Set(analyses.map(a => a.user?.id || a.userId)).size;
  
  // 用户贡献统计
  const userStats = new Map();
  for (const a of analyses) {
    const name = a.user?.username || a.username;
    if (!name) continue;
    
    if (!userStats.has(name)) {
      userStats.set(name, { 
        username: name, 
        commits: 0, 
        insertions: 0, 
        deletions: 0,
        projects: new Set(),
        score: a.aiQualityScore || null
      });
    }
    const s = userStats.get(name);
    s.commits += a.commitCount;
    s.insertions += a.insertions;
    s.deletions += a.deletions;
    const projectName = a.project?.name || a.projectName;
    if (projectName) s.projects.add(projectName);
    if (a.aiQualityScore && (!s.score || a.aiQualityScore > s.score)) {
      s.score = a.aiQualityScore;
    }
  }
  
  const sortedUsers = Array.from(userStats.values())
    .sort((a, b) => b.commits - a.commits);
  
  // 项目统计
  const projectStats = new Map();
  for (const a of analyses) {
    const name = a.project?.name || a.projectName;
    if (!name) continue;
    
    if (!projectStats.has(name)) {
      projectStats.set(name, { name, commits: 0, insertions: 0, deletions: 0, users: new Set() });
    }
    const p = projectStats.get(name);
    p.commits += a.commitCount;
    p.insertions += a.insertions;
    p.deletions += a.deletions;
    p.users.add(a.user?.username || a.username);
  }
  
  const sortedProjects = Array.from(projectStats.values())
    .sort((a, b) => b.commits - a.commits);
  
  // 生成 HTML
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
    h1 { color: #1890ff; border-bottom: 2px solid #1890ff; padding-bottom: 10px; }
    h2 { color: #333; margin-top: 24px; }
    .summary { background: #f5f5f5; padding: 16px; border-radius: 8px; margin: 16px 0; }
    .summary-item { display: inline-block; margin: 8px 16px; }
    .summary-value { font-size: 24px; font-weight: bold; color: #1890ff; }
    .summary-label { color: #666; font-size: 14px; }
    table { width: 100%; border-collapse: collapse; margin: 16px 0; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
    th { background: #fafafa; font-weight: 600; }
    .positive { color: #52c41a; }
    .negative { color: #f5222d; }
    .medal { font-size: 20px; }
    .score { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .score-high { background: #52c41a; color: white; }
    .score-mid { background: #faad14; color: white; }
    .score-low { background: #f5222d; color: white; }
    .score-default { background: #d9d9d9; color: #666; }
    .footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee; color: #999; font-size: 12px; }
  </style>
</head>
<body>
  <h1>📊 代码质量周报告</h1>
  <p style="color: #666;">报告周期：${formatDate(periodValue)} 所在周</p>
  
  <div class="summary">
    <div class="summary-item">
      <div class="summary-value">${totalCommits}</div>
      <div class="summary-label">总提交数</div>
    </div>
    <div class="summary-item">
      <div class="summary-value" class="positive">+${totalInsertions.toLocaleString()}</div>
      <div class="summary-label">新增代码行</div>
    </div>
    <div class="summary-item">
      <div class="summary-value" class="negative">-${totalDeletions.toLocaleString()}</div>
      <div class="summary-label">删除代码行</div>
    </div>
    <div class="summary-item">
      <div class="summary-value">${projectCount}</div>
      <div class="summary-label">涉及项目</div>
    </div>
    <div class="summary-item">
      <div class="summary-value">${userCount}</div>
      <div class="summary-label">活跃成员</div>
    </div>
  </div>
  
  <h2>🏆 贡献者排名</h2>
  <table>
    <tr>
      <th>排名</th>
      <th>成员</th>
      <th>提交数</th>
      <th>新增行</th>
      <th>删除行</th>
      <th>净增长</th>
      <th>AI评分</th>
    </tr>
    ${sortedUsers.map((u, i) => `
    <tr>
      <td>${i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}</td>
      <td>${u.username}</td>
      <td>${u.commits}</td>
      <td class="positive">+${u.insertions.toLocaleString()}</td>
      <td class="negative">-${u.deletions.toLocaleString()}</td>
      <td>${u.insertions - u.deletions > 0 ? '+' + (u.insertions - u.deletions).toLocaleString() : (u.insertions - u.deletions).toLocaleString()}</td>
      <td>${u.score ? `<span class="score ${u.score >= 8 ? 'score-high' : u.score >= 6 ? 'score-mid' : 'score-low'}">${u.score}</span>` : '<span class="score score-default">待评</span>'}</td>
    </tr>
    `).join('')}
  </table>
  
  <h2>📁 项目分布</h2>
  <table>
    <tr>
      <th>项目</th>
      <th>提交数</th>
      <th>新增行</th>
      <th>删除行</th>
      <th>贡献者</th>
    </tr>
    ${sortedProjects.map(p => `
    <tr>
      <td>${p.name}</td>
      <td>${p.commits}</td>
      <td class="positive">+${p.insertions.toLocaleString()}</td>
      <td class="negative">-${p.deletions.toLocaleString()}</td>
      <td>${p.users.size} 人</td>
    </tr>
    `).join('')}
  </table>
  
  <div class="footer">
    <p>📊 数据来源：代码质量分析系统</p>
    <p>🤖 报告生成：质检君</p>
    <p>📧 如需调整收件人，请联系系统管理员</p>
  </div>
</body>
</html>
`;
}

/**
 * 使用 Prisma 获取分析数据
 */
async function getAnalysesFromPrisma(periodValue) {
  try {
    const { PrismaClient } = require('@prisma/client');
    const prisma = new PrismaClient();
    
    const analyses = await prisma.codeAnalysis.findMany({
      where: { 
        periodType: 'week',
        periodValue: periodValue
      },
      include: {
        user: { select: { id: true, username: true, email: true } },
        project: { select: { id: true, name: true } }
      },
      orderBy: { commitCount: 'desc' }
    });
    
    await prisma.$disconnect();
    return analyses;
  } catch (err) {
    console.error('❌ Prisma 查询失败:', err.message);
    return null;
  }
}

/**
 * 主函数
 */
async function main() {
  const periodValue = process.argv[2];
  
  if (!periodValue) {
    console.error('用法: node notify-email.js <period-value>');
    console.error('示例: node notify-email.js 20260402');
    console.error('');
    console.error('注意: 此脚本需要在 code-quality-backend 目录下运行');
    process.exit(1);
  }
  
  console.log('============================================================');
  console.log('发送代码质量周报邮件');
  console.log('============================================================');
  console.log(`周期值: ${periodValue}`);
  
  // 加载配置
  const config = loadEmailConfig();
  const sender = getSenderInfo(config);
  const recipients = getRecipients(config);
  
  console.log(`SMTP: ${config.smtp?.host || 'smtp.qq.com'}:${config.smtp?.port || 465}`);
  console.log(`发件人: ${sender.name} <${sender.email}>`);
  
  // 获取分析数据
  console.log('\n正在获取分析数据...');
  const analyses = await getAnalysesFromPrisma(periodValue);
  
  if (!analyses || analyses.length === 0) {
    console.log('⚠️ 本周暂无数据，跳过邮件发送');
    return;
  }
  
  console.log(`找到 ${analyses.length} 条分析记录`);
  
  // 计算统计
  const userCount = new Set(analyses.map(a => a.userId)).size;
  const projectCount = new Set(analyses.map(a => a.projectId)).size;
  const totalCommits = analyses.reduce((sum, a) => sum + a.commitCount, 0);
  console.log(`涉及 ${userCount} 人，${projectCount} 项目，${totalCommits} 次提交`);
  
  // 生成邮件内容
  console.log('\n生成邮件内容...');
  const html = generateEmailHtml(analyses, periodValue);
  const subject = `📊 代码质量周报告 - ${formatDate(periodValue)}周报`;
  
  // 创建传输器
  const transporter = createTransporter(config);
  
  // 收件人列表
  console.log(`收件人: ${recipients.join(', ')}`);
  
  // 发送邮件
  console.log('\n发送邮件...');
  try {
    const result = await transporter.sendMail({
      from: `${sender.name} <${sender.email}>`,
      to: recipients.join(','),
      subject: subject,
      html: html
    });
    
    console.log('✅ 邮件发送成功！');
    console.log(`   Message ID: ${result.messageId}`);
  } catch (err) {
    console.error('❌ 邮件发送失败:', err.message);
    process.exit(1);
  }
  
  console.log('\n============================================================');
  console.log('邮件发送完成');
  console.log('============================================================');
}

main();