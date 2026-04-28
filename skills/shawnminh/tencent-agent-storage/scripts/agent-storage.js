#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

// ==================== 加载 smh-node-sdk ====================

function loadSMHClient() {
  // 按优先级从项目本地和全局 node_modules 加载 smh-node-sdk
  const candidates = [
    () => require('smh-node-sdk'),
    () => {
      // 尝试全局 node_modules
      const { execSync } = require('child_process');
      const globalPath = execSync('npm root -g 2>/dev/null').toString().trim();
      return require(path.join(globalPath, 'smh-node-sdk'));
    },
  ];
  for (const load of candidates) {
    try { return load(); } catch (e) { /* 继续尝试下一个 */ }
  }
  throw new Error(
    'smh-node-sdk 未安装，请先运行：\n' +
    '  npm install -g smh-node-sdk\n' +
    '或：\n' +
    '  npm install smh-node-sdk'
  );
}

const { SMHClient } = loadSMHClient();

// ==================== 凭证加载 ====================

// 凭证加载优先级（先找到者优先）：
// 1. ~/.tencentAgentStorage/.env（通用配置）
// 2. ~/.openclaw/openclaw.json 的 env 字段（OpenClaw）
// 3. ~/.hermes/.env（Hermes）
function loadEnvConfig() {
  const envVars = {};

  // 辅助函数：从 .env 格式文件中解析 key=value
  const parseDotEnv = (filePath) => {
    if (!fs.existsSync(filePath)) return;
    const lines = fs.readFileSync(filePath, 'utf8').split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx = trimmed.indexOf('=');
      if (eqIdx === -1) continue;
      const key = trimmed.slice(0, eqIdx).trim();
      const val = trimmed.slice(eqIdx + 1).trim().replace(/^["']|["']$/g, '');
      if (!(key in envVars)) envVars[key] = val;
    }
  };

  // 优先级 2：通用配置（~/.tencentAgentStorage/.env）
  parseDotEnv(path.join(os.homedir(), '.tencentAgentStorage', '.env'));

  // 优先级 3：OpenClaw（~/.openclaw/openclaw.json 的 env 字段）
  const cfgPath = path.join(os.homedir(), '.openclaw', 'openclaw.json');
  if (fs.existsSync(cfgPath)) {
    try {
      const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
      const envSection = cfg.env || {};
      for (const [k, v] of Object.entries(envSection)) {
        if (!(k in envVars)) envVars[k] = v;
      }
    } catch (e) { /* 解析失败忽略 */ }
  }

  // 优先级 4：Hermes（~/.hermes/.env）
  parseDotEnv(path.join(os.homedir(), '.hermes', '.env'));
  return {
    basePath: envVars['smh_basePath'] || envVars['SMH_BASE_PATH'],
    libraryId: envVars['smh_libraryId'] || envVars['SMH_LIBRARY_ID'],
    spaceId: envVars['smh_spaceId'] || envVars['SMH_SPACE_ID'],
    accessToken: envVars['smh_accessToken'] || envVars['SMH_ACCESS_TOKEN'],
  };
}

async function resolveCredentials() {
  const smh = loadEnvConfig();
  const host = smh.basePath || 'https://api.tencentsmh.cn';
  const { libraryId, spaceId, accessToken } = smh;

  if (!libraryId) {
    throw new Error('缺少 SMH 凭证，请在 ~/.tencentAgentStorage/.env、~/.openclaw/openclaw.json 的 env 字段或 ~/.hermes/.env 中配置 smh_libraryId');
  }
  if (!spaceId || !accessToken) {
    throw new Error('缺少 SMH 凭证，请配置 smh_spaceId 和 smh_accessToken');
  }

  return { host, libraryId, spaceId, accessToken };
}

async function getDefaultSpaceId(client, libraryId, adminToken) {
  const res = await client.space.listSpace({
    libraryId,
    accessToken: adminToken,
    userId: '9527',
    page: 1,
    pageSize: 10,
  });
  const list = (res.data && res.data.list) || [];
  if (list.length === 0) throw new Error('没有可用的云存储空间，请先在管理后台创建空间');
  return list[0].spaceId;
}

// ==================== 工具函数 ====================

function expandHome(p) {
  if (!p) return p;
  if (p.startsWith('~/') || p === '~') return path.join(os.homedir(), p.slice(1));
  return p;
}

function formatSize(bytes) {
  if (!bytes) return '0 B';
  const u = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${u[i]}`;
}

function out(obj) { process.stdout.write(JSON.stringify(obj) + '\n'); }

// ==================== 命令处理 ====================

async function cmdUpload(args) {
  const { localPath, remotePath, conflictStrategy = 'rename' } = args;
  if (!localPath) return out({ success: false, error: '缺少必填参数 localPath' });

  const absLocal = expandHome(localPath);
  if (!fs.existsSync(absLocal)) return out({ success: false, error: `本地文件不存在: ${absLocal}` });
  const stat = fs.statSync(absLocal);
  if (!stat.isFile()) return out({ success: false, error: `路径不是文件: ${absLocal}` });

  const fileSize = stat.size;
  const fileName = path.basename(absLocal);
  const cloudPath = remotePath || fileName;

  const startTime = Date.now();
  const { host, libraryId, spaceId, accessToken } = await resolveCredentials();

  // 使用 SMHClient 创建上传任务（支持秒传、简单上传、分片上传）
  const client = new SMHClient({ basePath: host });
  let rapidUpload = false;

  try {
    const task = await client.createUploadTask({
      libraryId,
      spaceId,
      accessToken,
      filePath: cloudPath,
      localPath: absLocal,
      conflictResolutionStrategy: conflictStrategy,
      onProgress: (state, progress) => {
        if (progress > 0 && progress < 100) {
          process.stderr.write(`[上传进度] ${fileName}: ${progress}%\n`);
        }
      },
      onComplete: (response) => {
        rapidUpload = !!(response && response.rapidUpload);
      },
    });
    await task.start();
  } catch (err) {
    // 409 冲突
    const status = err && err.response && err.response.status;
    if (status === 409) {
      return out({ success: false, conflict: true, fileName, error: `云端已存在同名文件 "${fileName}"` });
    }
    return out({ success: false, error: `Upload failed: ${err.message}` });
  }

  const uploadTime = ((Date.now() - startTime) / 1000).toFixed(1) + 's';

  // 通过 SDK 获取带签名的 COS 下载直链（参考 space-drive getPreview 实现）
  let downloadUrl = '';
  try {
    const infoRes = await client.file.infoFile({
      libraryId,
      spaceId,
      filePath: cloudPath,
      info: 1,
      purpose: 'download',
      accessToken,
    });
    downloadUrl = (infoRes.data && infoRes.data.cosUrl) || '';
  } catch (e) {
    // 获取下载链接失败时回退到手动拼接
    const encodedCloudPath = cloudPath.split('/').map(encodeURIComponent).join('/');
    downloadUrl = `${host}/api/v1/file/${libraryId}/${spaceId}/${encodedCloudPath}?access_token=${encodeURIComponent(accessToken)}&ContentDisposition=attachment&Purpose=download`;
  }

  out({
    success: true,
    upload: { localFile: absLocal, remotePath: cloudPath, fileSize, fileSizeHuman: formatSize(fileSize), uploadTime, rapidUpload },
    downloadUrl,
  });
}

async function cmdInfo(args) {
  const { remotePath } = args;
  if (!remotePath) return out({ success: false, error: '缺少必填参数 remotePath' });

  const { host, libraryId, spaceId, accessToken } = await resolveCredentials();
  const client = new SMHClient({ basePath: host });

  let info;
  try {
    const res = await client.file.infoFile({
      libraryId,
      spaceId,
      filePath: remotePath,
      info: 1,
      purpose: 'download',
      accessToken,
    });
    info = res.data;
  } catch (e) {
    const status = e && e.response && e.response.status;
    if (status === 404) return out({ success: false, error: `云端文件不存在: ${remotePath}` });
    return out({ success: false, error: e.message });
  }

  // 优先使用 SDK 返回的 cosUrl（带签名的 COS 直链）
  const downloadUrl = (info && info.cosUrl) || '';

  out({
    success: true, remotePath,
    downloadUrl,
    fileInfo: {
      name: path.basename(remotePath),
      size: info && info.size ? parseInt(info.size, 10) : null,
      type: (info && info.contentType) || '',
      creationTime: (info && info.creationTime) || null,
      modificationTime: (info && info.modificationTime) || null,
    },
  });
}

async function cmdList(args) {
  const { dirPath = '/', limit = 50 } = args;
  const { host, libraryId, spaceId, accessToken } = await resolveCredentials();
  const client = new SMHClient({ basePath: host });

  // 目录路径：根目录传空字符串
  const normalized = dirPath === '/' || dirPath === '' ? '' : dirPath.replace(/^\//, '');

  let data;
  try {
    const res = await client.directory.listDirectoryByPage({
      libraryId,
      spaceId,
      filePath: normalized,
      byPage: 1,
      page: 1,
      pageSize: Math.min(limit, 200),
      accessToken,
    });
    data = res.data;
  } catch (e) { return out({ success: false, error: e.message }); }

  const files = ((data && data.contents) || []).map((item) => ({
    name: item.name || '',
    type: item.type || 'file',
    size: item.size ? parseInt(item.size, 10) : null,
    sizeHuman: item.size ? formatSize(parseInt(item.size, 10)) : null,
    creationTime: item.creationTime || null,
    modificationTime: item.modificationTime || null,
    path: normalized ? `${normalized}/${item.name}` : item.name,
  }));

  out({ success: true, dirPath, total: (data && data.totalNum) || files.length, files });
}

// ==================== 入口 ====================

const [,, cmd, argsStr] = process.argv;
let args = {};
try { if (argsStr) args = JSON.parse(argsStr); } catch (e) { out({ success: false, error: `参数解析失败: ${e.message}` }); process.exit(1); }

const cmds = { upload: cmdUpload, info: cmdInfo, list: cmdList };
if (!cmds[cmd]) { out({ success: false, error: `未知命令: ${cmd}，支持: upload / info / list` }); process.exit(1); }

cmds[cmd](args).catch((e) => { out({ success: false, error: e.message }); process.exit(1); });
