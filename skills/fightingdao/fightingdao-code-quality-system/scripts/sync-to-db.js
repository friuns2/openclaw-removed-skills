#!/usr/bin/env node
/**
 * 同步本周分析数据到数据库
 * 用法：node sync-to-db.js 20260402
 * 
 * 配置文件：
 *   默认从技能目录或 workspace 目录读取 config.json
 */

const fs = require('fs');
const path = require('path');

// 加载配置
function loadConfig() {
  const configPaths = [
    path.join(__dirname, '../config.json'),
    path.join(process.env.HOME, '.openclaw/workspace/code-quality-config.json'),
    path.join(process.env.HOME, '.openclaw/skills/code-quality-system/config.json')
  ];
  
  for (const configPath of configPaths) {
    if (fs.existsSync(configPath)) {
      console.log(`加载配置文件: ${configPath}`);
      return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    }
  }
  
  // 默认配置
  console.log('未找到配置文件，使用默认配置');
  return {
    apiBaseUrl: 'http://localhost:3000/api/v1',
    teamId: 'default-team'
  };
}

const CONFIG = loadConfig();

const API_BASE_URL = CONFIG.apiBaseUrl || 'http://localhost:3000/api/v1';
const TEAM_ID = CONFIG.teamId || 'default-team';

// 解析命令行参数
const periodValue = process.argv[2];
const periodType = periodValue.length === 8 ? 'week' : 'month';

// 读取分析数据
const analysisFile = `/Users/zhangdi/work/codeCap/代码质量分析系统/analysis-output/analysis-${periodValue}.json`;
const analysisData = JSON.parse(fs.readFileSync(analysisFile, 'utf-8'));

console.log('============================================================');
console.log('同步分析数据到数据库');
console.log('============================================================');
console.log(`周期: ${periodType} ${periodValue}`);
console.log(`用户数: ${analysisData.users.length}`);
console.log(`项目数: ${analysisData.projects.length}`);
console.log(`分析记录数: ${analysisData.analyses.length}`);

// 获取用户ID映射
async function getUserMap() {
  const { PrismaClient } = require('@prisma/client');
  const prisma = new PrismaClient();
  
  const users = await prisma.user.findMany({
    where: { teamId: TEAM_ID },
    select: { id: true, username: true, email: true }
  });
  
  const userMap = new Map();
  for (const user of users) {
    userMap.set(user.username, user.id);
    if (user.email) {
      const emailPrefix = user.email.split('@')[0];
      userMap.set(emailPrefix, user.id);
    }
  }
  
  await prisma.$disconnect();
  return userMap;
}

// 获取项目ID映射
async function getProjectMap() {
  const { PrismaClient } = require('@prisma/client');
  const prisma = new PrismaClient();
  
  const projects = await prisma.project.findMany({
    select: { id: true, name: true }
  });
  
  const projectMap = new Map();
  for (const project of projects) {
    projectMap.set(project.name, project.id);
  }
  
  await prisma.$disconnect();
  return projectMap;
}

// 创建或获取项目
async function ensureProject(projectName, repository, branch) {
  const { PrismaClient } = require('@prisma/client');
  const prisma = new PrismaClient();
  
  let project = await prisma.project.findFirst({
    where: { name: projectName }
  });
  
  if (!project) {
    project = await prisma.project.create({
      data: {
        name: projectName,
        repository: repository || '',
        defaultBranch: branch || 'master',
        teamId: TEAM_ID
      }
    });
    console.log(`  ✨ 创建项目: ${projectName}`);
  }
  
  await prisma.$disconnect();
  return project;
}

// 删除本周期的旧数据
async function clearOldData() {
  const { PrismaClient } = require('@prisma/client');
  const prisma = new PrismaClient();
  
  console.log('\n1. 清理本周期的旧数据...');
  
  // 删除 code_issues
  await prisma.$executeRaw`DELETE FROM code_issues WHERE analysis_id IN (SELECT id FROM code_analyses WHERE period_type = ${periodType} AND period_value = ${periodValue})`;
  
  // 删除 code_reviews
  await prisma.$executeRaw`DELETE FROM code_reviews WHERE analysis_id IN (SELECT id FROM code_analyses WHERE period_type = ${periodType} AND period_value = ${periodValue})`;
  
  // 删除 code_analyses
  const deletedAnalyses = await prisma.codeAnalysis.deleteMany({
    where: { periodType, periodValue }
  });
  console.log(`  ✓ 删除 code_analyses: ${deletedAnalyses.count} 条`);
  
  // 删除 project_statistics
  await prisma.projectStatistic.deleteMany({
    where: { periodType, periodValue }
  });
  
  // 删除 team_statistics
  await prisma.teamStatistic.deleteMany({
    where: { periodType, periodValue }
  });
  
  await prisma.$disconnect();
}

// 获取提交类型
function getCommitType(message) {
  if (!message) return 'other';
  if (message.startsWith('feat')) return 'feat';
  if (message.startsWith('fix')) return 'fix';
  if (message.startsWith('refactor')) return 'refactor';
  if (message.startsWith('style')) return 'style';
  if (message.startsWith('test')) return 'test';
  if (message.startsWith('docs')) return 'docs';
  if (message.startsWith('chore')) return 'chore';
  if (message.startsWith('perf')) return 'perf';
  return 'other';
}

// 主函数
async function main() {
  const userMap = await getUserMap();
  const projectMap = await getProjectMap();
  
  console.log(`\n已加载 ${userMap.size} 个用户映射`);
  console.log(`已加载 ${projectMap.size} 个项目映射`);
  
  // 清理旧数据
  await clearOldData();

  // 同步项目
  console.log('\n2. 同步项目...');
  for (const project of analysisData.projects) {
    if (!projectMap.has(project.name)) {
      const newProject = await ensureProject(project.name, project.repository, project.branch);
      projectMap.set(project.name, newProject.id);
    }
  }
  
  // 准备分析数据
  console.log('\n3. 准备分析数据...');
  const analyses = [];
  let skipCount = 0;
  
  for (const analysis of analysisData.analyses) {
    // 匹配用户
    let userId = null;
    const username = analysis.user.username;
    
    if (userMap.has(username)) {
      userId = userMap.get(username);
    } else {
      for (const [dbUsername, dbId] of userMap.entries()) {
        if (username === dbUsername || username.endsWith(dbUsername) || dbUsername.endsWith(username)) {
          userId = dbId;
          break;
        }
      }
    }
    
    let projectId = projectMap.get(analysis.projectName);
    
    if (!userId) {
      console.log(`  ⏭️  跳过用户: ${username} (未在小组管理中添加)`);
      skipCount++;
      continue;
    }
    
    if (!projectId) {
      console.log(`  ⏭️  跳过项目: ${analysis.projectName} (项目不存在)`);
      skipCount++;
      continue;
    }
    
    analyses.push({
      userId,
      projectId,
      periodType,
      periodValue,
      commitCount: analysis.stats.commitCount,
      insertions: analysis.stats.insertions,
      deletions: analysis.stats.deletions,
      filesChanged: analysis.stats.filesChanged,
      totalLines: analysis.codeLines?.totalLines || 0,
      codeLines: analysis.codeLines?.codeLines || 0,
      commentLines: analysis.codeLines?.commentLines || 0,
      blankLines: analysis.codeLines?.blankLines || 0,
      languages: analysis.codeLines?.languages || {},
      fileChanges: analysis.fileChanges || [],
      taskCount: analysis.stats.taskCount || 0,
      branch: analysis.branch,
      currentVersion: analysis.branch,
      compareVersion: analysis.sourceBranch,
      commits: analysis.commits || [],
      username: analysis.user.username
    });
  }
  
  console.log(`  ✓ 准备了 ${analyses.length} 条分析数据`);
  if (skipCount > 0) {
    console.log(`  ⚠️  跳过 ${skipCount} 条`);
  }
  
  // 写入数据库
  console.log('\n4. 写入数据库...');
  
  const { PrismaClient } = require('@prisma/client');
  const prisma = new PrismaClient();
  
  let successCount = 0;
  
  for (const analysis of analyses) {
    try {
      const created = await prisma.codeAnalysis.create({
        data: {
          userId: analysis.userId,
          projectId: analysis.projectId,
          periodType: analysis.periodType,
          periodValue: analysis.periodValue,
          commitCount: analysis.commitCount,
          insertions: analysis.insertions,
          deletions: analysis.deletions,
          filesChanged: analysis.filesChanged,
          totalLines: analysis.totalLines,
          codeLines: analysis.codeLines,
          commentLines: analysis.commentLines,
          blankLines: analysis.blankLines,
          languages: analysis.languages,
          fileChanges: analysis.fileChanges,
          taskCount: analysis.taskCount,
          branch: analysis.branch,
          currentVersion: analysis.currentVersion,
          compareVersion: analysis.compareVersion
        }
      });
      
      // 创建 code_reviews 记录
      if (analysis.commits && analysis.commits.length > 0) {
        for (const commit of analysis.commits) {
          await prisma.codeReview.create({
            data: {
              analysisId: created.id,
              commitHash: commit.hash,
              commitMessage: commit.message,
              commitBranch: analysis.branch,
              commitDate: new Date(commit.date),
              committerId: analysis.userId,
              committerName: analysis.username,
              status: 'pending',
              reviewResult: JSON.stringify({
                type: getCommitType(commit.message),
                insertions: commit.insertions || 0,
                deletions: commit.deletions || 0
              })
            }
          });
        }
      }
      
      successCount++;
    } catch (error) {
      console.log(`  ✗ 写入失败: ${error.message}`);
    }
  }
  
  await prisma.$disconnect();
  
  console.log(`  ✓ 成功写入 ${successCount} 条分析记录`);
  
  // 触发统计计算
  console.log('\n5. 触发统计计算...');
  try {
    const statsResponse = await fetch(`${API_BASE_URL}/data/calculate-statistics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ periodType, periodValue })
    });
    const statsResult = await statsResponse.json();
    console.log(`  ✓ 统计计算: ${statsResult.success ? '成功' : '失败'}`);
  } catch (e) {
    console.log(`  ⚠️ 统计计算失败: ${e.message}`);
  }
  
  console.log('\n============================================================');
  console.log('✅ 同步完成！');
  console.log('============================================================');
}

main().catch(console.error);