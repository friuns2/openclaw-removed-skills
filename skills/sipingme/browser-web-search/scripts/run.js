#!/usr/bin/env node

const { spawnSync } = require('node:child_process');

// 所需版本（与 config.json 中 dependencies.npm 保持一致）
const REQUIRED_VERSION = '0.3.8';

const command = process.argv[2];
const args = process.argv.slice(3);

if (!command) {
  showHelp();
  process.exit(0);
}

const run = (cmd, cmdArgs) => {
  const result = spawnSync(cmd, cmdArgs, { stdio: 'inherit' });
  if (result.error) {
    console.error(JSON.stringify({ success: false, error: result.error.message }));
    process.exit(1);
  }
  process.exit(result.status ?? 1);
};

/**
 * 使用全局安装的 bws CLI 执行命令
 */
const runBws = (cliArgs) => {
  run('bws', cliArgs);
};

function showHelp() {
  console.log(`
browser-web-search-skill v${REQUIRED_VERSION}
把任何网站变成命令行 API，专为 OpenClaw 设计

用法: 
  通过 scripts/run.js <command> [选项]
  或直接: bws [选项]

命令:
  list                列出所有可用 adapter
  search <query>      搜索 adapter
  info <name>         查看 adapter 详情
  run <name> [args]   运行 adapter
  help                显示帮助信息

安装:
  npm install -g browser-web-search@${REQUIRED_VERSION}

示例:
  bws site list
  bws zhihu/hot
  bws xiaohongshu/search "旅行"
  bws bilibili/popular --json

选项:
  --json              JSON 格式输出
  --jq <expr>         对 JSON 输出应用 jq 过滤

内置平台:
  知乎、小红书、B站、今日头条、36kr、澎湃、腾讯、网易、
  新浪、微博、微信公众号、百度、Bing、Google、CSDN、博客园、BOSS直聘

前提条件:
  需要 OpenClaw 环境运行（openclaw 命令可用）
`);
}

switch (command) {
  case 'list':
    runBws(['site', 'list', ...args]);
    break;
  case 'search':
    if (!args[0]) {
      console.error(JSON.stringify({ success: false, error: 'Missing argument: query' }));
      process.exit(1);
    }
    runBws(['site', 'search', ...args]);
    break;
  case 'info':
    if (!args[0]) {
      console.error(JSON.stringify({ success: false, error: 'Missing argument: name' }));
      process.exit(1);
    }
    runBws(['site', 'info', ...args]);
    break;
  case 'run':
    if (!args[0]) {
      console.error(JSON.stringify({ success: false, error: 'Missing argument: adapter name' }));
      process.exit(1);
    }
    runBws(['site', ...args]);
    break;
  case 'help':
    showHelp();
    break;
  default:
    // 如果命令包含 /，当作 adapter 名称直接运行
    if (command.includes('/')) {
      runBws([command, ...args]);
    } else {
      console.error(JSON.stringify({ success: false, error: `Unknown command: ${command}` }));
      process.exit(1);
    }
}
