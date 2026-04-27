#!/usr/bin/env node
/**
 * 代码质量分析脚本 v2
 * 支持周维度和月维度分析
 * 
 * 周维度：找版本分支，统计从源分支切出后的所有提交
 * 月维度：找目标分支，统计该月的所有提交（时间范围）
 * 
 * 用法：
 *   node analyze-code-v2.js 20260326  # 周维度（YYYYMMDD）
 *   node analyze-code-v2.js 202603   # 月维度（YYYYMM）
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
    apiBaseUrl: 'http://localhost:3000/api/v1',
    teamId: 'default-team'
  };
}

const CONFIG = loadConfig();

// 配置
const CODEBASE_DIR = CONFIG.codebaseDir || './codebase';
const API_BASE_URL = CONFIG.apiBaseUrl || 'http://localhost:3000/api/v1';
const TEAM_ID = CONFIG.teamId || 'default-team';

// 解析周期值
const parsePeriodValue = (periodValue) => {
  if (periodValue.length === 8) {
    return { type: 'week', value: periodValue };
  } else if (periodValue.length === 6) {
    return { type: 'month', value: periodValue };
  }
  throw new Error(`Invalid periodValue: ${periodValue}, expected YYYYMMDD (week) or YYYYMM (month)`);
};

// 计算本周四的日期
const getThisThursday = () => {
  const now = new Date();
  const dayOfWeek = now.getDay();
  const daysToThursday = 4 - dayOfWeek;
  const thursday = new Date(now);
  thursday.setDate(now.getDate() + daysToThursday);
  return thursday.toISOString().slice(0, 10).replace(/-/g, '');
};

// 计算周维度的日期范围
const getWeekDateRange = (periodValue) => {
  const year = parseInt(periodValue.substring(0, 4));
  const month = parseInt(periodValue.substring(4, 6)) - 1;
  const day = parseInt(periodValue.substring(6, 8));
  const thursday = new Date(year, month, day);
  
  // 周一到周四
  const monday = new Date(thursday);
  monday.setDate(monday.getDate() - 3);
  
  const friday = new Date(thursday);
  friday.setDate(friday.getDate() + 1);
  
  const formatDate = (d) => d.toISOString().split('T')[0];
  return {
    start: formatDate(monday),
    end: formatDate(friday)
  };
};

// 计算月维度的日期范围
const getMonthDateRange = (periodValue) => {
  const year = parseInt(periodValue.substring(0, 4));
  const month = parseInt(periodValue.substring(4, 6));
  
  // 月初到月末
  const start = `${year}-${String(month).padStart(2, '0')}-01`;
  
  // 下个月第一天
  const nextMonth = month === 12 ? 1 : month + 1;
  const nextYear = month === 12 ? year + 1 : year;
  const end = `${nextYear}-${String(nextMonth).padStart(2, '0')}-01`;
  
  return { start, end };
};

// 生成本周所有日期（用于分支匹配）
const getWeekDates = (periodValue) => {
  const year = parseInt(periodValue.substring(0, 4));
  const month = parseInt(periodValue.substring(4, 6)) - 1;
  const day = parseInt(periodValue.substring(6, 8));
  const thursday = new Date(year, month, day);
  
  const monday = new Date(thursday);
  monday.setDate(monday.getDate() - 3);
  
  const dates = [];
  for (let i = 0; i < 5; i++) {
    const d = new Date(monday);
    d.setDate(d.getDate() + i);
    dates.push(d.toISOString().slice(0, 10).replace(/-/g, ''));
  }
  return dates;
};

// 生成本月所有日期（用于分支匹配）
const getMonthDates = (periodValue) => {
  const year = parseInt(periodValue.substring(0, 4));
  const month = parseInt(periodValue.substring(4, 6));
  
  const dates = [];
  // 生成本月所有可能的日期格式（YYYYMMDD 中的 DD 部分）
  for (let day = 1; day <= 31; day++) {
    dates.push(periodValue + String(day).padStart(2, '0'));
  }
  return dates;
};

// 查找匹配的分支
const findMatchingBranch = (projectPath, periodValue, periodType) => {
  try {
    execSync(`cd "${projectPath}" && git fetch origin --quiet`, { encoding: 'utf-8', timeout: 60000 });
  } catch (e) {}
  
  try {
    const branches = execSync(`cd "${projectPath}" && git branch -r`, { encoding: 'utf-8' })
      .split('\n')
      .map(b => b.trim().replace('origin/', ''))
      .filter(b => b && !b.startsWith('HEAD'));
    
    // 根据周期类型生成匹配日期
    const matchDates = periodType === 'week' ? getWeekDates(periodValue) : getMonthDates(periodValue);
    
    // 精确匹配
    for (const date of matchDates) {
      const matched = branches.find(b => b.includes(date));
      if (matched) {
        return { branch: matched, found: true };
      }
    }
    
    // 模糊匹配（包含周期值）
    const matched = branches.find(b => b.includes(periodValue));
    if (matched) {
      return { branch: matched, found: true };
    }
    
    // 月维度：如果没有匹配的分支，使用默认分支
    if (periodType === 'month') {
      const defaultBranch = getDefaultBranch(projectPath);
      return { branch: defaultBranch, found: false };
    }
    
    return null;
  } catch (e) {
    return null;
  }
};

// 找源分支
const findSourceBranch = (projectPath, branch) => {
  const possibleSources = ['develop', 'master', 'main', 'release', 'staging'];
  
  for (const source of possibleSources) {
    try {
      execSync(`cd "${projectPath}" && git rev-parse origin/${source}`, { encoding: 'utf-8', stdio: 'pipe' });
      return source;
    } catch (e) {}
  }
  
  return 'develop';
};

// 获取默认分支
const getDefaultBranch = (projectPath) => {
  try {
    const result = execSync(`cd "${projectPath}" && git remote show origin | grep "HEAD branch"`, { encoding: 'utf-8' });
    const match = result.match(/HEAD branch: (.+)/);
    return match ? match[1].trim() : 'master';
  } catch (e) {
    return 'master';
  }
};

// 获取仓库地址
const getRepository = (projectPath) => {
  try {
    return execSync(`cd "${projectPath}" && git remote get-url origin`, { encoding: 'utf-8' }).trim();
  } catch (e) {
    return '';
  }
};

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

// 获取提交类型（中文）
const getCommitType = (message) => {
  if (!message) return '其他';
  if (message.startsWith('feat')) return '新功能';
  if (message.startsWith('fix')) return 'Bug修复';
  if (message.startsWith('refactor')) return '重构';
  if (message.startsWith('style')) return '样式';
  if (message.startsWith('test')) return '测试';
  if (message.startsWith('docs')) return '文档';
  if (message.startsWith('chore')) return '杂项';
  if (message.startsWith('perf')) return '性能优化';
  return '其他';
};

// 提取任务号
const extractTaskIds = (commits) => {
  const taskIds = new Set();
  for (const commit of commits) {
    const match = commit.message.match(/\(([A-Z]+-\d+)\)/);
    if (match) {
      taskIds.add(match[1]);
    }
  }
  return Array.from(taskIds);
};

// ============================================================
// 核心函数：获取用户和提交统计
// ============================================================

// 周维度：统计版本分支从源分支切出后的提交
const getCommitUsersForWeek = (projectPath, branch, sourceBranch) => {
  try {
    // 1. 先尝试分支差异
    let result = execSync(
      `cd "${projectPath}" && git shortlog -sne origin/${sourceBranch}..origin/${branch}`,
      { encoding: 'utf-8' }
    ).trim();
    
    // 2. 如果差异为空，找版本分支的开发提交
    if (!result) {
      try {
        const lastMerge = execSync(
          `cd "${projectPath}" && git log origin/${branch} --merges --format="%H" --grep="release\\|Merge" 2>/dev/null | head -1`,
          { encoding: 'utf-8' }
        ).trim();
        
        if (lastMerge) {
          result = execSync(
            `cd "${projectPath}" && git shortlog -sne ${lastMerge}..origin/${branch}`,
            { encoding: 'utf-8' }
          ).trim();
        }
      } catch (e) {}
      
      // 3. 尝试 sourceBranch^1
      if (!result) {
        try {
          result = execSync(
            `cd "${projectPath}" && git shortlog -sne origin/${sourceBranch}^1..origin/${branch}`,
            { encoding: 'utf-8' }
          ).trim();
        } catch (e) {}
      }
    }
    
    if (!result) return [];
    
    return result.split('\n').map(line => {
      const match = line.trim().match(/^\d+\s+(.+?)\s+<(.+?)>$/);
      if (match) {
        return { username: match[1], email: match[2] };
      }
      return null;
    }).filter(Boolean);
  } catch {
    return [];
  }
};

// 月维度：统计该月的所有提交（所有分支，不需要找目标分支）
const getCommitUsersForMonth = (projectPath, dateRange) => {
  try {
    // 使用 --all 统计所有分支在该月的提交
    const result = execSync(
      `cd "${projectPath}" && git shortlog -sne --all --since="${dateRange.start}" --until="${dateRange.end}"`,
      { encoding: 'utf-8' }
    ).trim();
    
    if (!result) return [];
    
    return result.split('\n').map(line => {
      const match = line.trim().match(/^\d+\s+(.+?)\s+<(.+?)>$/);
      if (match) {
        return { username: match[1], email: match[2] };
      }
      return null;
    }).filter(Boolean);
  } catch {
    return [];
  }
};

// 获取用户的提交统计（周维度）
const getUserCommitStatsForWeek = (projectPath, branch, sourceBranch, userEmail) => {
  try {
    let commitCount = 0;
    let statsResult = '';
    
    // 1. 先尝试分支差异
    commitCount = parseInt(execSync(
      `cd "${projectPath}" && git log --author="${userEmail}" origin/${sourceBranch}..origin/${branch} --oneline | wc -l`,
      { encoding: 'utf-8' }
    ).trim()) || 0;
    
    if (commitCount > 0) {
      statsResult = execSync(
        `cd "${projectPath}" && git log --author="${userEmail}" origin/${sourceBranch}..origin/${branch} --numstat --pretty=format:`,
        { encoding: 'utf-8' }
      ).trim();
    } else {
      // 2. 找版本分支的开发提交
      try {
        const lastMerge = execSync(
          `cd "${projectPath}" && git log origin/${branch} --merges --format="%H" --grep="release\\|Merge" 2>/dev/null | head -1`,
          { encoding: 'utf-8' }
        ).trim();
        
        if (lastMerge) {
          statsResult = execSync(
            `cd "${projectPath}" && git log --author="${userEmail}" ${lastMerge}..origin/${branch} --numstat --pretty=format:`,
            { encoding: 'utf-8' }
          ).trim();
          commitCount = parseInt(execSync(
            `cd "${projectPath}" && git log --author="${userEmail}" ${lastMerge}..origin/${branch} --oneline | wc -l`,
            { encoding: 'utf-8' }
          ).trim()) || 0;
        }
      } catch (e) {}
      
      // 3. 尝试 sourceBranch^1
      if (!statsResult) {
        try {
          statsResult = execSync(
            `cd "${projectPath}" && git log --author="${userEmail}" origin/${sourceBranch}^1..origin/${branch} --numstat --pretty=format:`,
            { encoding: 'utf-8' }
          ).trim();
          commitCount = parseInt(execSync(
            `cd "${projectPath}" && git log --author="${userEmail}" origin/${sourceBranch}^1..origin/${branch} --oneline | wc -l`,
            { encoding: 'utf-8' }
          ).trim()) || 0;
        } catch (e) {}
      }
    }

    let insertions = 0;
    let deletions = 0;
    let filesChanged = new Set();
    const fileChangesList = []; // 新增：收集具体文件变更

    if (statsResult) {
      statsResult.split('\n').forEach(line => {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 3) {
          const ins = parseInt(parts[0]);
          const del = parseInt(parts[1]);
          const file = parts[2];
          if (!isNaN(ins) && !isNaN(del) && !shouldExclude(file)) {
            insertions += ins;
            deletions += del;
            filesChanged.add(file);
            // 收集文件变更详情（使用 path 字段，和历史数据结构一致）
            const ext = file.split('.').pop() || 'unknown';
            const langMap = {
              'vue': 'Vue', 'js': 'JavaScript', 'ts': 'TypeScript', 'tsx': 'TypeScript',
              'jsx': 'JavaScript', 'html': 'HTML', 'css': 'CSS', 'less': 'Less', 'scss': 'SCSS',
              'json': 'JSON', 'java': 'Java', 'py': 'Python', 'go': 'Go'
            };
            fileChangesList.push({
              path: file,
              language: langMap[ext] || ext.toUpperCase(),
              insertions: ins,
              deletions: del
            });
          }
        }
      });
    }

    return { commitCount, insertions, deletions, filesChanged: filesChanged.size, fileChangesList };
  } catch {
    return { commitCount: 0, insertions: 0, deletions: 0, filesChanged: 0, fileChangesList: [] };
  }
};

// 获取用户的提交统计（月维度）
const getUserCommitStatsForMonth = (projectPath, userEmail, dateRange) => {
  try {
    // 使用 --all 统计所有分支在该月的提交
    const commitCount = parseInt(execSync(
      `cd "${projectPath}" && git log --author="${userEmail}" --all --since="${dateRange.start}" --until="${dateRange.end}" --oneline | wc -l`,
      { encoding: 'utf-8' }
    ).trim()) || 0;

    const statsResult = execSync(
      `cd "${projectPath}" && git log --author="${userEmail}" --all --since="${dateRange.start}" --until="${dateRange.end}" --numstat --pretty=format:`,
      { encoding: 'utf-8' }
    ).trim();

    let insertions = 0;
    let deletions = 0;
    let filesChanged = new Set();
    const fileChangesList = []; // 新增：收集具体文件变更

    if (statsResult) {
      statsResult.split('\n').forEach(line => {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 3) {
          const ins = parseInt(parts[0]);
          const del = parseInt(parts[1]);
          const file = parts[2];
          if (!isNaN(ins) && !isNaN(del) && !shouldExclude(file)) {
            insertions += ins;
            deletions += del;
            filesChanged.add(file);
            // 收集文件变更详情（使用 path 字段，和历史数据结构一致）
            const ext = file.split('.').pop() || 'unknown';
            const langMap = {
              'vue': 'Vue', 'js': 'JavaScript', 'ts': 'TypeScript', 'tsx': 'TypeScript',
              'jsx': 'JavaScript', 'html': 'HTML', 'css': 'CSS', 'less': 'Less', 'scss': 'SCSS',
              'json': 'JSON', 'java': 'Java', 'py': 'Python', 'go': 'Go'
            };
            fileChangesList.push({
              path: file,
              language: langMap[ext] || ext.toUpperCase(),
              insertions: ins,
              deletions: del
            });
          }
        }
      });
    }

    return { commitCount, insertions, deletions, filesChanged: filesChanged.size, fileChangesList };
  } catch {
    return { commitCount: 0, insertions: 0, deletions: 0, filesChanged: 0, fileChangesList: [] };
  }
};

// 获取提交记录详情（周维度）
const getCommitMessagesForWeek = (projectPath, branch, sourceBranch, userEmail) => {
  try {
    let result = '';
    
    // 1. 先尝试分支差异
    result = execSync(
      `cd "${projectPath}" && git log --author="${userEmail}" origin/${sourceBranch}..origin/${branch} --pretty=format:"%h|%ai|%s"`,
      { encoding: 'utf-8' }
    ).trim();
    
    // 2. 如果为空，找版本分支的开发提交
    if (!result) {
      try {
        const lastMerge = execSync(
          `cd "${projectPath}" && git log origin/${branch} --merges --format="%H" --grep="release\\|Merge" 2>/dev/null | head -1`,
          { encoding: 'utf-8' }
        ).trim();
        
        if (lastMerge) {
          result = execSync(
            `cd "${projectPath}" && git log --author="${userEmail}" ${lastMerge}..origin/${branch} --pretty=format:"%h|%ai|%s"`,
            { encoding: 'utf-8' }
          ).trim();
        }
      } catch (e) {}
      
      // 3. 尝试 sourceBranch^1
      if (!result) {
        try {
          result = execSync(
            `cd "${projectPath}" && git log --author="${userEmail}" origin/${sourceBranch}^1..origin/${branch} --pretty=format:"%h|%ai|%s"`,
            { encoding: 'utf-8' }
          ).trim();
        } catch (e) {}
      }
    }

    if (!result) return [];

    const commits = result.split('\n').map(line => {
      const [hash, datetime, message] = line.split('|');
      return { hash, date: datetime, message };
    });

    // 为每个提交获取真实的增删数据
    return commits.map(commit => {
      try {
        const statsResult = execSync(
          `cd "${projectPath}" && git show ${commit.hash} --numstat --format=""`,
          { encoding: 'utf-8' }
        ).trim();
        
        let insertions = 0;
        let deletions = 0;
        
        if (statsResult) {
          statsResult.split('\n').forEach(line => {
            const parts = line.trim().split(/\s+/);
            if (parts.length >= 2) {
              const ins = parseInt(parts[0]);
              const del = parseInt(parts[1]);
              const file = parts[2];
              if (!isNaN(ins) && !isNaN(del) && !shouldExclude(file)) {
                insertions += ins;
                deletions += del;
              }
            }
          });
        }
        
        return {
          hash: commit.hash,
          date: commit.date,
          message: commit.message,
          insertions,
          deletions,
          type: getCommitType(commit.message)
        };
      } catch (e) {
        return {
          hash: commit.hash,
          date: commit.date,
          message: commit.message,
          insertions: 0,
          deletions: 0,
          type: getCommitType(commit.message)
        };
      }
    });
  } catch {
    return [];
  }
};

// 获取提交记录详情（月维度）
const getCommitMessagesForMonth = (projectPath, userEmail, dateRange) => {
  try {
    // 使用 --all 统计所有分支在该月的提交
    const result = execSync(
      `cd "${projectPath}" && git log --author="${userEmail}" --all --since="${dateRange.start}" --until="${dateRange.end}" --pretty=format:"%h|%ai|%s"`,
      { encoding: 'utf-8' }
    ).trim();

    if (!result) return [];

    const commits = result.split('\n').map(line => {
      const [hash, datetime, message] = line.split('|');
      return { hash, date: datetime, message };
    });

    return commits.map(commit => {
      try {
        const statsResult = execSync(
          `cd "${projectPath}" && git show ${commit.hash} --numstat --format=""`,
          { encoding: 'utf-8' }
        ).trim();
        
        let insertions = 0;
        let deletions = 0;
        
        if (statsResult) {
          statsResult.split('\n').forEach(line => {
            const parts = line.trim().split(/\s+/);
            if (parts.length >= 2) {
              const ins = parseInt(parts[0]);
              const del = parseInt(parts[1]);
              const file = parts[2];
              if (!isNaN(ins) && !isNaN(del) && !shouldExclude(file)) {
                insertions += ins;
                deletions += del;
              }
            }
          });
        }
        
        return {
          hash: commit.hash,
          date: commit.date,
          message: commit.message,
          insertions,
          deletions,
          type: getCommitType(commit.message)
        };
      } catch (e) {
        return {
          hash: commit.hash,
          date: commit.date,
          message: commit.message,
          insertions: 0,
          deletions: 0,
          type: getCommitType(commit.message)
        };
      }
    });
  } catch {
    return [];
  }
};

// 获取代码行数
const getCodeLines = (projectPath) => {
  return { totalLines: 0, codeLines: 0, commentLines: 0, blankLines: 0, languages: {} };
};

// 获取项目列表
const getProjects = () => {
  return fs.readdirSync(CODEBASE_DIR)
    .filter(name => {
      const projectPath = path.join(CODEBASE_DIR, name);
      return fs.statSync(projectPath).isDirectory() && fs.existsSync(path.join(projectPath, '.git'));
    });
};

// ============================================================
// 主函数
// ============================================================

const main = async () => {
  const PERIOD_VALUE = process.argv[2] || getThisThursday();
  const PERIOD_INFO = parsePeriodValue(PERIOD_VALUE);
  const PERIOD_TYPE = PERIOD_INFO.type;
  
  console.log('='.repeat(60));
  console.log('代码质量分析系统');
  console.log(`分析周期: ${PERIOD_VALUE} (${PERIOD_TYPE === 'week' ? '周维度' : '月维度'})`);
  console.log('='.repeat(60));
  
  const dateRange = PERIOD_TYPE === 'week' 
    ? getWeekDateRange(PERIOD_VALUE)
    : getMonthDateRange(PERIOD_VALUE);
  
  console.log(`日期范围: ${dateRange.start} ~ ${dateRange.end}`);
  
  const projects = getProjects();
  console.log(`发现 ${projects.length} 个项目\n`);

  const allAnalyses = [];
  const allUsers = new Map();

  // 分析每个项目
  for (const projectName of projects) {
    const projectPath = path.join(CODEBASE_DIR, projectName);
    console.log(`\n📁 分析项目: ${projectName}`);
    
    const defaultBranch = getDefaultBranch(projectPath);
    const repository = getRepository(projectPath);
    
    // 周维度：查找匹配的分支
    // 月维度：不需要找分支，直接统计该月所有提交
    let users = [];
    let branch = defaultBranch;
    
    if (PERIOD_TYPE === 'week') {
      const branchResult = findMatchingBranch(projectPath, PERIOD_VALUE, PERIOD_TYPE);
      
      if (!branchResult) {
        console.log(`  ⏭️  无匹配分支，跳过`);
        continue;
      }
      
      branch = branchResult.branch;
      const sourceBranch = findSourceBranch(projectPath, branch);
      
      users = getCommitUsersForWeek(projectPath, branch, sourceBranch);
      
      if (users.length === 0) {
        console.log(`  ⏭️  本周期无提交，跳过`);
        continue;
      }
      
      console.log(`  🎯 匹配分支: ${branch}`);
      console.log(`  🌿 源分支: ${sourceBranch}`);
      console.log(`  👥 提交用户: ${users.length} 人`);
      
    } else {
      // 月维度：直接统计该月所有提交
      users = getCommitUsersForMonth(projectPath, dateRange);
      
      if (users.length === 0) {
        console.log(`  ⏭️  本月无提交，跳过`);
        continue;
      }
      
      console.log(`  📅 统计该月所有提交（所有分支）`);
      console.log(`  👥 提交用户: ${users.length} 人`);
    }
    
    // 收集用户
    users.forEach(user => {
      if (!allUsers.has(user.email)) {
        allUsers.set(user.email, user);
      }
    });

    const codeLines = getCodeLines(projectPath);
    
    // 分析每个用户
    for (const user of users) {
      const stats = PERIOD_TYPE === 'week'
        ? getUserCommitStatsForWeek(projectPath, branch, findSourceBranch(projectPath, branch), user.email)
        : getUserCommitStatsForMonth(projectPath, user.email, dateRange);
      
      if (stats.commitCount > 0) {
        const commits = PERIOD_TYPE === 'week'
          ? getCommitMessagesForWeek(projectPath, branch, findSourceBranch(projectPath, branch), user.email)
          : getCommitMessagesForMonth(projectPath, user.email, dateRange);
        
        const taskIds = extractTaskIds(commits);

        console.log(`  - ${user.username}: ${stats.commitCount} 提交, ${taskIds.length} 任务, +${stats.insertions}/-${stats.deletions} 行`);

        allAnalyses.push({
          user,
          projectName,
          repository,
          branch: PERIOD_TYPE === 'week' ? branch : '月度汇总',
          sourceBranch: PERIOD_TYPE === 'week' ? findSourceBranch(projectPath, branch) : '',
          stats: {
            commitCount: stats.commitCount,
            insertions: stats.insertions,
            deletions: stats.deletions,
            filesChanged: stats.filesChanged,
            taskCount: taskIds.length
          },
          commits,
          taskIds,
          codeLines,
          fileChanges: stats.fileChangesList || [] // 使用收集的文件变更数据
        });
      }
    }
  }

  // 汇总
  console.log('\n' + '='.repeat(60));
  console.log('📊 分析汇总');
  console.log('='.repeat(60));
  
  const totalCommits = allAnalyses.reduce((sum, a) => sum + a.stats.commitCount, 0);
  const totalInsertions = allAnalyses.reduce((sum, a) => sum + a.stats.insertions, 0);
  const totalDeletions = allAnalyses.reduce((sum, a) => sum + a.stats.deletions, 0);

  console.log(`有效项目: ${new Set(allAnalyses.map(a => a.projectName)).size} 个`);
  console.log(`涉及用户: ${allUsers.size} 人`);
  console.log(`总提交数: ${totalCommits} 次`);
  console.log(`总新增行: ${totalInsertions} 行`);
  console.log(`总删除行: ${totalDeletions} 行`);

  // 保存结果
  const outputPath = path.join(path.dirname(__filename), '../analysis-output', `analysis-${PERIOD_VALUE}.json`);
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const output = {
    periodType: PERIOD_TYPE,
    periodValue: PERIOD_VALUE,
    dateRange,
    generatedAt: new Date().toISOString(),
    projects: Array.from(new Set(allAnalyses.map(a => a.projectName))).map(name => ({
      name,
      repository: allAnalyses.find(a => a.projectName === name)?.repository || ''
    })),
    users: Array.from(allUsers.values()),
    analyses: allAnalyses
  };

  fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));
  console.log(`\n✅ 分析结果已保存到: ${outputPath}`);
};

main().catch(console.error);