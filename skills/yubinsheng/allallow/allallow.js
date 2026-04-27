#!/usr/bin/env node
/**
 * allallow skill - 设置最大权限配置
 * 
 * 支持的 OpenClaw 版本: 2026.3.31+
 * 支持的环境: Linux, macOS, Windows(WSL)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const os = require('os');

// 版本信息
const SKILL_VERSION = '1.0.0';
const MIN_OPENCLAW_VERSION = '2026.3.31';

// 检测运行环境
const ENV = {
  platform: os.platform(),
  isWSL: os.release().includes('microsoft') || os.release().includes('WSL'),
  isWindows: os.platform() === 'win32',
  isMac: os.platform() === 'darwin',
  isLinux: os.platform() === 'linux',
  homeDir: os.homedir()
};

// 根据环境确定配置路径
function getConfigPath() {
  // Windows (非 WSL)
  if (ENV.isWindows && !ENV.isWSL) {
    return path.join(ENV.homeDir, '.openclaw', 'openclaw.json');
  }
  // WSL / Linux / macOS
  return path.join(ENV.homeDir, '.openclaw', 'openclaw.json');
}

const CONFIG_PATH = getConfigPath();
const BACKUP_PATH = `${CONFIG_PATH}.backup`;

// 检测 OpenClaw 版本
function checkOpenClawVersion() {
  try {
    const version = execSync('openclaw version', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] });
    const match = version.match(/(\d{4}\.\d+\.\d+)/);
    if (match) {
      const currentVersion = match[1];
      console.log(`📦 OpenClaw 版本: ${currentVersion}`);
      
      // 简单版本比较
      if (currentVersion < MIN_OPENCLAW_VERSION) {
        console.warn(`⚠️ 警告: 当前版本 ${currentVersion} 低于最低要求 ${MIN_OPENCLAW_VERSION}`);
        console.warn('   某些功能可能无法正常工作');
      }
      return currentVersion;
    }
  } catch (e) {
    console.warn('⚠️ 无法检测 OpenClaw 版本');
  }
  return null;
}

// 检测当前环境信息
function detectEnvironment() {
  console.log('🔍 检测运行环境:');
  console.log(`   平台: ${ENV.platform}`);
  console.log(`   WSL: ${ENV.isWSL ? '是' : '否'}`);
  console.log(`   配置路径: ${CONFIG_PATH}`);
  
  // 检测网关状态
  try {
    const status = execSync('openclaw status --json', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] });
    const parsed = JSON.parse(status);
    if (parsed.gateway) {
      console.log(`   网关状态: ${parsed.gateway.reachable ? '运行中' : '未运行'}`);
      console.log(`   网关绑定: ${parsed.gateway.bind || 'unknown'}`);
    }
  } catch (e) {
    console.log('   网关状态: 无法检测');
  }
}

// 读取配置
function readConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    throw new Error(`配置文件不存在: ${CONFIG_PATH}`);
  }
  const content = fs.readFileSync(CONFIG_PATH, 'utf8');
  return JSON.parse(content);
}

// 写入配置
function writeConfig(config) {
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf8');
}

// 备份配置
function backupConfig() {
  const config = readConfig();
  fs.copyFileSync(CONFIG_PATH, BACKUP_PATH);
  console.log('✅ 配置已备份到:', BACKUP_PATH);
  return config;
}

// 获取适合环境的 allowedOrigins
function getAllowedOrigins(config) {
  const origins = [
    'http://127.0.0.1:18789',
    'http://localhost:18789'
  ];
  
  // 尝试获取局域网 IP
  try {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
      for (const iface of interfaces[name]) {
        // 只获取 IPv4 内网地址
        if (iface.family === 'IPv4' && !iface.internal) {
          if (iface.address.startsWith('192.168.') || 
              iface.address.startsWith('10.') || 
              iface.address.startsWith('172.')) {
            origins.push(`http://${iface.address}:18789`);
          }
        }
      }
    }
  } catch (e) {
    // 忽略网络接口读取错误
  }
  
  // 如果配置中已有 origins，合并进去
  if (config.gateway?.controlUi?.allowedOrigins) {
    for (const origin of config.gateway.controlUi.allowedOrigins) {
      if (!origins.includes(origin)) {
        origins.push(origin);
      }
    }
  }
  
  return origins;
}

// 应用最大权限配置
function applyAllAllow() {
  console.log(`\n🚀 allallow skill v${SKILL_VERSION}`);
  console.log(`   最低 OpenClaw 版本: ${MIN_OPENCLAW_VERSION}\n`);
  
  // 检测环境
  detectEnvironment();
  
  // 检查版本
  checkOpenClawVersion();
  
  console.log('\n📋 开始应用配置...\n');
  
  // 读取并备份配置
  const config = backupConfig();
  
  // 确保基本结构存在
  if (!config.tools) config.tools = {};
  if (!config.agents) config.agents = {};
  if (!config.agents.defaults) config.agents.defaults = {};
  if (!config.gateway) config.gateway = {};
  if (!config.gateway.controlUi) config.gateway.controlUi = {};
  
  // 设置最大权限 - 根据 OpenClaw 2026.3.31 schema
  config.tools.profile = 'full';
  config.tools.exec = {
    host: 'auto',        // auto | sandbox | gateway | node
    security: 'full',    // deny | allowlist | full
    ask: 'off'           // off | on-miss | always
  };
  config.tools.fs = {
    workspaceOnly: false
  };
  
  // 关闭沙箱 - 使用 2026.3.31 正确路径
  config.agents.defaults.sandbox = {
    mode: 'off'          // off | auto | per-request | all
  };
  
  // 允许所有节点命令
  config.gateway.nodes = {
    denyCommands: []
  };
  
  // 设置 lan 绑定
  config.gateway.bind = 'lan';  // loopback | lan | tailnet
  
  // 配置 Control UI - 根据环境自动获取 origins
  config.gateway.controlUi.allowInsecureAuth = true;
  config.gateway.controlUi.allowedOrigins = getAllowedOrigins(config);
  
  // 写入配置
  writeConfig(config);
  console.log('\n✅ 最大权限配置已应用');
  console.log('   - tools.exec: host=auto, security=full, ask=off');
  console.log('   - tools.fs.workspaceOnly: false');
  console.log('   - agents.defaults.sandbox.mode: off');
  console.log('   - gateway.nodes.denyCommands: []');
  console.log('   - gateway.bind: lan');
  console.log(`   - Control UI origins: ${config.gateway.controlUi.allowedOrigins.length} 个`);
  
  // 重启网关
  console.log('\n🔄 重启网关...');
  try {
    execSync('openclaw gateway restart', { stdio: 'inherit' });
    console.log('\n✅ 网关已重启，配置生效！');
  } catch (e) {
    console.error('\n⚠️ 网关重启失败:', e.message);
    console.log('   请手动运行: openclaw gateway restart');
  }
  
  console.log('\n⚠️ 安全提醒:');
  console.log('   - 执行命令无需批准');
  console.log('   - 可访问任何文件');
  console.log('   - 沙箱已关闭');
  console.log('   - 允许所有节点命令');
  console.log('   仅在受信任的环境中使用！\n');
}

// 回滚配置
function rollback() {
  console.log(`\n🔄 allallow skill v${SKILL_VERSION} - 回滚模式\n`);
  
  if (!fs.existsSync(BACKUP_PATH)) {
    console.error('❌ 备份文件不存在:', BACKUP_PATH);
    console.log('   无法回滚，请手动检查配置');
    process.exit(1);
  }
  
  fs.copyFileSync(BACKUP_PATH, CONFIG_PATH);
  console.log('✅ 配置已回滚到备份版本');
  
  console.log('\n🔄 重启网关...');
  try {
    execSync('openclaw gateway restart', { stdio: 'inherit' });
    console.log('\n✅ 网关已重启，回滚生效！');
  } catch (e) {
    console.error('\n⚠️ 网关重启失败:', e.message);
    console.log('   请手动运行: openclaw gateway restart');
  }
}

// 显示信息
function showInfo() {
  console.log(`
📦 allallow skill v${SKILL_VERSION}
═══════════════════════════════════════
最低 OpenClaw 版本: ${MIN_OPENCLAW_VERSION}

支持的环境:
  ✅ Linux (原生)
  ✅ macOS
  ✅ Windows (WSL)
  ⚠️  Windows (原生) - 部分功能可能受限

功能:
  • 设置 tools.exec 为最大权限
  • 关闭沙箱 (sandbox.mode: off)
  • 允许访问整个文件系统
  • 允许所有节点命令
  • 设置网关绑定为 lan
  • 自动检测并配置 Control UI 允许来源

隐私说明:
  • 不收集任何隐私信息
  • 不打包令牌、凭证、API Key
  • 只包含通用配置模板

使用方法:
  allallow apply    - 应用最大权限配置
  allallow rollback - 回滚到备份配置
  allallow backup   - 备份当前配置
  allallow info     - 显示此信息
`);
}

// 主函数
const command = process.argv[2];

switch (command) {
  case 'apply':
  case 'run':
    applyAllAllow();
    break;
  case 'rollback':
    rollback();
    break;
  case 'backup':
    backupConfig();
    break;
  case 'info':
  case '--version':
  case '-v':
    showInfo();
    break;
  default:
    showInfo();
    process.exit(0);
}
