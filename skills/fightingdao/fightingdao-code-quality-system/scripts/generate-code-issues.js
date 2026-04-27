#!/usr/bin/env node
/**
 * 代码审查问题生成脚本
 * 从分析结果生成 code_issues 数据
 * 
 * 用法：
 *   在 backend 目录运行: node ../scripts/generate-code-issues.js 20260402
 *   或: cd code-quality-backend && node ../scripts/generate-code-issues.js 20260402
 * 
 * 输出：
 *   写入 code_issues 表
 */

const fs = require('fs');
const path = require('path');

// 配置文件路径
const CONFIG_PATH = path.join(process.env.HOME, '.openclaw/workspace/code-quality-config.json');

// 加载配置
function loadConfig() {
  const configPaths = [
    path.join(__dirname, '../config.json'),
    path.join(process.env.HOME, '.openclaw/workspace/code-quality-config.json'),
  ];
  
  for (const configPath of configPaths) {
    if (fs.existsSync(configPath)) {
      return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    }
  }
  
  return {};
}

const CONFIG = loadConfig();
const OUTPUT_DIR = CONFIG.outputDir || path.join(__dirname, '../analysis-output');

/**
 * 问题类型中文映射
 */
const ISSUE_TYPE_MAP = {
  'maintainability': '代码可维护性',
  'performance': '性能问题',
  'security': '安全问题',
  'error_handling': '错误处理',
  'type_definition': '类型定义',
  'hardcoded_value': '硬编码常量',
  'code_quality': '代码质量',
  'best_practice': '最佳实践',
  'testing': '测试覆盖',
  'correctness': '代码正确性',
};

/**
 * 获取文件的具体提交者
 */
function getFileCommitter(projectPath, filePath, branch, sourceBranch = 'develop') {
  try {
    const { execSync } = require('child_process');
    const cmd = `cd "${projectPath}" && git log --oneline --format="%an" origin/${sourceBranch}..origin/${branch} -- "${filePath}" | head -1`;
    const result = execSync(cmd, { encoding: 'utf-8' }).trim();
    return result || null;
  } catch {
    return null;
  }
}

/**
 * 审查单个文件的变更
 * @returns {Array} 问题列表
 */
function reviewFileChange(fileChange, projectPath, branch, sourceBranch, username) {
  const issues = [];
  const filePath = fileChange.path || fileChange.file;
  const insertions = fileChange.insertions || 0;
  const deletions = fileChange.deletions || 0;
  
  if (!filePath) return issues;
  
  // 获取文件的具体提交者
  const committer = getFileCommitter(projectPath, filePath, branch, sourceBranch) || username;
  
  // 大文件变更检测
  if (insertions > 300) {
    issues.push({
      filePath,
      lineStart: null,
      lineEnd: null,
      type: 'maintainability',
      severity: 'P2',
      description: '组件文件变更行数较多，建议拆分',
      suggestion: '考虑将大文件拆分为更小的模块，提高可维护性',
      committerName: committer,
    });
  }
  
  // 净删除检测
  if (deletions > insertions * 2 && deletions > 50) {
    issues.push({
      filePath,
      lineStart: null,
      lineEnd: null,
      type: 'code_quality',
      severity: 'P2',
      description: '代码净删除较多，确认是否为重构或清理',
      suggestion: '确认删除的代码是否已迁移到其他地方，避免功能丢失',
      committerName: committer,
    });
  }
  
  // 根据文件类型添加特定检查
  const ext = path.extname(filePath).toLowerCase();
  
  if (ext === '.vue' || ext === '.tsx' || ext === '.jsx') {
    // 前端组件检查
    if (insertions > 100) {
      issues.push({
        filePath,
        lineStart: null,
        lineEnd: null,
        type: 'maintainability',
        severity: 'P2',
        description: '组件变更较大，建议检查是否需要拆分',
        suggestion: '大型组件应拆分为更小的子组件，提高复用性',
        committerName: committer,
      });
    }
  }
  
  if (ext === '.ts' || ext === '.js') {
    // TypeScript/JavaScript 检查
    if (filePath.includes('.test.') || filePath.includes('.spec.')) {
      // 测试文件
      if (insertions > 0 && insertions < 10) {
        issues.push({
          filePath,
          lineStart: null,
          lineEnd: null,
          type: 'testing',
          severity: 'P2',
          description: '测试文件变更较少，确认测试覆盖是否充分',
          suggestion: '确保新增代码有对应的测试用例',
          committerName: committer,
        });
      }
    }
  }
  
  // API 相关文件检查
  if (filePath.includes('api') || filePath.includes('service')) {
    if (insertions > 0) {
      issues.push({
        filePath,
        lineStart: null,
        lineEnd: null,
        type: 'error_handling',
        severity: 'P2',
        description: 'API/Service 层有变更，请确认错误处理是否完善',
        suggestion: '确保 API 有适当的错误处理和日志记录',
        committerName: committer,
      });
    }
  }
  
  return issues;
}

/**
 * 审查所有文件变更
 * @param {Array} fileChanges 文件变更列表
 * @param {Array} commits 提交列表
 * @param {string} username 用户名
 * @param {string} projectPath 项目路径
 * @param {string} branch 分支名
 * @param {string} sourceBranch 源分支
 * @returns {Array} 问题列表（已去重）
 */
function reviewFileChanges(fileChanges, commits, username, projectPath, branch, sourceBranch) {
  const issues = [];
  const seenIssues = new Set(); // 🔴 Bug 1 修复：去重 Set
  
  for (const fileChange of fileChanges) {
    const fileIssues = reviewFileChange(fileChange, projectPath, branch, sourceBranch, username);
    
    for (const issue of fileIssues) {
      // 🔴 Bug 1 修复：使用 file_path + line_start + issue_type + description 作为唯一键
      const issueKey = `${issue.filePath}::${issue.lineStart || 0}::${issue.type}::${issue.description}`;
      
      if (seenIssues.has(issueKey)) {
        continue; // 跳过重复问题
      }
      seenIssues.add(issueKey);
      
      issues.push(issue);
    }
  }
  
  return issues;
}

/**
 * 使用 Prisma 写入数据库
 */
async function saveToDatabase(analysisId, issues) {
  try {
    const { PrismaClient } = require('@prisma/client');
    const prisma = new PrismaClient();
    
    // 先删除该分析的旧问题
    await prisma.$executeRaw`DELETE FROM code_issues WHERE analysis_id = ${analysisId}`;
    
    // 批量插入新问题
    let count = 0;
    for (const issue of issues) {
      await prisma.$executeRaw`
        INSERT INTO code_issues (
          id, analysis_id, file_path, line_start, line_end, 
          issue_type, severity, description, suggestion, committer_name,
          created_at, updated_at
        ) VALUES (
          gen_random_uuid(), ${analysisId}, ${issue.filePath}, ${issue.lineStart}, ${issue.lineEnd},
          ${issue.type}, ${issue.severity}, ${issue.description}, ${issue.suggestion}, ${issue.committerName},
          NOW(), NOW()
        )
      `;
      count++;
    }
    
    await prisma.$disconnect();
    return count;
  } catch (err) {
    console.error('❌ 数据库写入失败:', err.message);
    return 0;
  }
}

/**
 * 主函数
 */
async function main() {
  const periodValue = process.argv[2];
  
  if (!periodValue) {
    console.error('用法: node generate-code-issues.js <period-value>');
    console.error('示例: node generate-code-issues.js 20260402');
    console.error('');
    console.error('注意: 此脚本需要在 code-quality-backend 目录下运行');
    process.exit(1);
  }
  
  console.log('============================================================');
  console.log('生成代码审查问题');
  console.log('============================================================');
  console.log(`周期值: ${periodValue}`);
  
  // 读取分析结果
  const analysisFile = path.join(OUTPUT_DIR, `analysis-${periodValue}.json`);
  if (!fs.existsSync(analysisFile)) {
    console.error(`❌ 分析文件不存在: ${analysisFile}`);
    process.exit(1);
  }
  
  const analysisData = JSON.parse(fs.readFileSync(analysisFile, 'utf-8'));
  console.log(`读取到 ${analysisData.analyses.length} 条分析记录`);
  
  // 按项目分组
  const projectMap = new Map();
  for (const analysis of analysisData.analyses) {
    const projectId = analysis.projectId || analysis.project?.id;
    if (!projectId) continue;
    
    if (!projectMap.has(projectId)) {
      projectMap.set(projectId, {
        projectName: analysis.projectName || analysis.project?.name,
        projectPath: analysis.projectPath,
        branch: analysis.branch,
        sourceBranch: analysis.sourceBranch || 'develop',
        analyses: []
      });
    }
    projectMap.get(projectId).analyses.push(analysis);
  }
  
  console.log(`涉及 ${projectMap.size} 个项目`);
  
  // 统计
  let totalIssues = 0;
  let totalAnalyses = 0;
  
  // 为每个项目生成问题
  for (const [projectId, projectData] of projectMap) {
    console.log(`\n处理项目: ${projectData.projectName}`);
    
    for (const analysis of projectData.analyses) {
      const fileChanges = analysis.fileChanges || [];
      
      if (fileChanges.length === 0) {
        console.log(`  ${analysis.username}: 无文件变更，跳过`);
        continue;
      }
      
      // 🔴 Bug 1 和 Bug 2 修复：生成问题（带去重和提交人）
      const issues = reviewFileChanges(
        fileChanges,
        analysis.commits || [],
        analysis.username,
        projectData.projectPath,
        projectData.branch,
        projectData.sourceBranch
      );
      
      if (issues.length === 0) {
        // 即使没有自动检测到问题，也要生成至少1条（根据 SKILL.md 核心原则）
        const username = analysis.username;
        const mainFile = fileChanges[0];
        const filePath = mainFile?.path || mainFile?.file || 'unknown';
        const committer = getFileCommitter(
          projectData.projectPath, 
          filePath, 
          projectData.branch, 
          projectData.sourceBranch
        ) || username;
        
        issues.push({
          filePath,
          lineStart: null,
          lineEnd: null,
          type: 'best_practice',
          severity: 'P2',
          description: '建议进行代码审查，确保代码质量',
          suggestion: '请团队成员 review 本次变更，关注代码规范和可维护性',
          committerName: committer,
        });
      }
      
      // 写入数据库
      const analysisId = analysis.id;
      if (analysisId) {
        const count = await saveToDatabase(analysisId, issues);
        console.log(`  ${analysis.username}: 生成 ${issues.length} 条问题，写入 ${count} 条`);
        totalIssues += count;
        totalAnalyses++;
      } else {
        console.log(`  ${analysis.username}: 无分析 ID，跳过写入`);
      }
    }
  }
  
  console.log('\n============================================================');
  console.log('生成完成');
  console.log('============================================================');
  console.log(`总分析数: ${totalAnalyses}`);
  console.log(`总问题数: ${totalIssues}`);
}

main().catch(console.error);