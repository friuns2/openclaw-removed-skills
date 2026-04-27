#!/usr/bin/env node
/**
 * 代码审查脚本
 * 分析 git diff 输出，生成结构化问题明细
 * 
 * 用法：
 *   node code-review.js <项目名> <周期值>
 *   node code-review.js dove_digital 20260326
 * 
 * 配置文件：
 *   默认从技能目录或 workspace 目录读取 config.json
 */

const { execSync } = require('child_process');
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
    codebaseDir: './codebase',
    outputDir: path.join(__dirname, '../analysis-output')
  };
}

const CONFIG = loadConfig();

// 配置
const CODEBASE_DIR = CONFIG.codebaseDir || './codebase';
const OUTPUT_DIR = CONFIG.outputDir || path.join(__dirname, '../analysis-output');

// 排除文件规则
const shouldExclude = (file) => {
  const excludePatterns = [
    /package-lock\.json$/,
    /yarn\.lock$/,
    /pnpm-lock\.yaml$/,
    /node_modules\//,
    /\.min\.(js|css)$/,
    /dist\//,
    /build\//,
    /\.d\.ts$/
  ];
  return excludePatterns.some(p => p.test(file));
};

// 获取变更文件列表
const getChangedFiles = (projectPath, branch, sourceBranch = 'develop') => {
  try {
    const files = execSync(
      `cd "${projectPath}" && git diff origin/${sourceBranch}..origin/${branch} --name-only`,
      { encoding: 'utf-8' }
    ).trim().split('\n').filter(f => f && !shouldExclude(f));
    return files;
  } catch {
    return [];
  }
};

// 获取文件变更内容
const getFileDiff = (projectPath, branch, filePath, sourceBranch = 'develop') => {
  try {
    const diff = execSync(
      `cd "${projectPath}" && git diff origin/${sourceBranch}..origin/${branch} -- "${filePath}"`,
      { encoding: 'utf-8', maxBuffer: 1024 * 1024 * 10 } // 10MB buffer
    );
    return diff;
  } catch {
    return '';
  }
};

// 获取当前文件内容（用于获取上下文）
const getFileContent = (projectPath, branch, filePath) => {
  try {
    const content = execSync(
      `cd "${projectPath}" && git show origin/${branch}:"${filePath}"`,
      { encoding: 'utf-8', maxBuffer: 1024 * 1024 * 10 }
    );
    return content;
  } catch {
    return '';
  }
};

// 解析 diff 输出，提取变更行
const parseDiff = (diff) => {
  const lines = diff.split('\n');
  const changes = [];
  let currentFile = null;
  let currentLine = 0;
  let inHunk = false;
  
  for (const line of lines) {
    // 文件头
    if (line.startsWith('+++ b/')) {
      currentFile = line.substring(6);
    }
    
    // hunk header: @@ -start,count +start,count @@
    const hunkMatch = line.match(/^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (hunkMatch) {
      currentLine = parseInt(hunkMatch[1]);
      inHunk = true;
      continue;
    }
    
    if (inHunk && currentFile) {
      if (line.startsWith('+') && !line.startsWith('+++')) {
        // 新增行
        changes.push({
          file: currentFile,
          line: currentLine,
          type: 'add',
          content: line.substring(1)
        });
        currentLine++;
      } else if (line.startsWith('-') && !line.startsWith('---')) {
        // 删除行
        changes.push({
          file: currentFile,
          line: currentLine,
          type: 'delete',
          content: line.substring(1)
        });
      } else if (!line.startsWith('\\')) {
        currentLine++;
      }
    }
  }
  
  return changes;
};

// 主函数
const main = async () => {
  const projectName = process.argv[2];
  const periodValue = process.argv[3]; // YYYYMMDD
  
  if (!projectName || !periodValue) {
    console.log('用法: node code-review.js <项目名> <周期值>');
    console.log('示例: node code-review.js dove_digital 20260326');
    process.exit(1);
  }
  
  console.log('='.repeat(60));
  console.log(`代码审查: ${projectName} @ ${periodValue}`);
  console.log('='.repeat(60));
  
  // 读取分析结果
  const analysisFile = path.join(OUTPUT_DIR, `analysis-${periodValue}.json`);
  if (!fs.existsSync(analysisFile)) {
    console.log(`❌ 分析文件不存在: ${analysisFile}`);
    process.exit(1);
  }
  
  const analysisData = JSON.parse(fs.readFileSync(analysisFile, 'utf-8'));
  const projectAnalyses = analysisData.analyses.filter(a => a.projectName === projectName);
  
  if (projectAnalyses.length === 0) {
    console.log(`❌ 未找到项目 ${projectName} 的分析数据`);
    process.exit(1);
  }
  
  const projectPath = path.join(CODEBASE_DIR, projectName);
  const branch = projectAnalyses[0].branch;
  const sourceBranch = projectAnalyses[0].sourceBranch || 'develop';
  
  console.log(`\n分支: ${branch}`);
  console.log(`源分支: ${sourceBranch}`);
  
  // 获取变更文件
  const changedFiles = getChangedFiles(projectPath, branch, sourceBranch);
  console.log(`\n变更文件: ${changedFiles.length} 个`);
  
  // 收集所有问题
  const allIssues = [];
  
  for (const file of changedFiles) {
    console.log(`\n分析: ${file}`);
    const diff = getFileDiff(projectPath, branch, file, sourceBranch);
    const changes = parseDiff(diff);
    
    // 这里输出变更信息，供 AI 审查
    console.log(`  变更行数: ${changes.filter(c => c.type === 'add').length} 新增, ${changes.filter(c => c.type === 'delete').length} 删除`);
  }
  
  // 输出审查数据供 AI 分析
  const reviewData = {
    projectName,
    periodValue,
    branch,
    sourceBranch,
    changedFiles: changedFiles.map(file => ({
      path: file,
      diff: getFileDiff(projectPath, branch, file, sourceBranch)
    }))
  };
  
  const reviewFile = path.join(OUTPUT_DIR, `review-${projectName}-${periodValue}.json`);
  fs.writeFileSync(reviewFile, JSON.stringify(reviewData, null, 2));
  console.log(`\n✅ 审查数据已保存: ${reviewFile}`);
  console.log('\n请让 AI 审查以上变更，生成问题明细。');
};

main().catch(console.error);