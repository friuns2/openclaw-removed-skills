#!/usr/bin/env node

// 本 CLI 不依赖任何第三方 npm 包，全部走 HTTP 调用：
//   - tools.siping.me（账号 / 公众号绑定）
//   - pipeline API（文章抓取 + 改写 + 发布，全部由服务端完成）
// 因此无需注入 NODE_PATH，无需安装本地依赖。

const fs = require('fs');
const os = require('os');
const path = require('path');

const POLL_INTERVAL_MS = 5000;
const MAX_POLL_ATTEMPTS = 120; // 最长等待 10 分钟，避免假超时导致 AI 重试产生重复草稿
const DEFAULT_TOOLS_URL = process.env.WEB_PUBLISHER_TOOLS_URL || 'https://tools.siping.me/api';

const CREDENTIALS_DIR = path.join(os.homedir(), '.web-publisher');
const CREDENTIALS_PATH = path.join(CREDENTIALS_DIR, 'credentials.json');

// ----------------------------------------------------------------------------
// Credential layer: env > local file
// ----------------------------------------------------------------------------

function readCredentialsFile() {
  try {
    if (!fs.existsSync(CREDENTIALS_PATH)) return null;
    const raw = fs.readFileSync(CREDENTIALS_PATH, 'utf8');
    const data = JSON.parse(raw);
    if (!data || typeof data !== 'object') return null;
    if (!data.userId || !data.apiKey) return null;
    return data;
  } catch (err) {
    process.stderr.write(`[warn] 读取本地凭证失败: ${err.message}\n`);
    return null;
  }
}

function writeCredentialsFile(creds) {
  fs.mkdirSync(CREDENTIALS_DIR, { recursive: true, mode: 0o700 });
  try {
    fs.chmodSync(CREDENTIALS_DIR, 0o700);
  } catch (_) {
    // best-effort on platforms (e.g. Windows) without POSIX permissions
  }
  const payload = JSON.stringify({ version: 1, ...creds }, null, 2);
  fs.writeFileSync(CREDENTIALS_PATH, payload, { mode: 0o600 });
  try {
    fs.chmodSync(CREDENTIALS_PATH, 0o600);
  } catch (_) {
    // best-effort
  }
}

function deleteCredentialsFile() {
  try {
    if (fs.existsSync(CREDENTIALS_PATH)) fs.unlinkSync(CREDENTIALS_PATH);
  } catch (err) {
    process.stderr.write(`[warn] 删除本地凭证失败: ${err.message}\n`);
  }
}

function loadCredentials() {
  const envUserId = process.env.WEB_PUBLISHER_USER_ID;
  const envApiKey = process.env.WEB_PUBLISHER_API_KEY;
  const envApiUrl = process.env.WEB_PUBLISHER_API_URL;

  if (envUserId && envApiKey) {
    return {
      source: 'env',
      userId: envUserId,
      apiKey: envApiKey,
      apiUrl: envApiUrl || '',
      toolsUrl: process.env.WEB_PUBLISHER_TOOLS_URL || DEFAULT_TOOLS_URL
    };
  }

  const fileCreds = readCredentialsFile();
  if (fileCreds) {
    return {
      source: 'file',
      userId: fileCreds.userId,
      apiKey: fileCreds.apiKey,
      apiUrl: fileCreds.apiUrl || envApiUrl || '',
      toolsUrl: fileCreds.toolsUrl || DEFAULT_TOOLS_URL,
      boundAt: fileCreds.boundAt
    };
  }

  return null;
}

function maskApiKey(key) {
  if (!key) return '';
  if (key.length <= 8) return '****';
  return `${key.slice(0, 4)}****${key.slice(-4)}`;
}

function requireCredentials() {
  const creds = loadCredentials();
  if (!creds) {
    console.error(JSON.stringify({
      success: false,
      error: '尚未登录，请先运行：web-publisher login'
    }));
    process.exit(1);
  }
  return creds;
}

function requirePipelineApi(creds) {
  if (!creds.apiUrl) {
    console.error(JSON.stringify({
      success: false,
      error: '未配置 pipeline API 地址，请联系服务方或设置 WEB_PUBLISHER_API_URL'
    }));
    process.exit(1);
  }
}

// ----------------------------------------------------------------------------
// Networking
// ----------------------------------------------------------------------------

async function callJson(method, url, headers, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', ...headers }
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  let data = null;
  try {
    data = await res.json();
  } catch (_) {
    // tolerate empty body
    data = null;
  }
  return { res, data };
}

async function pipelineRequest(method, p, body, creds) {
  requirePipelineApi(creds);
  const { res, data } = await callJson(method, `${creds.apiUrl}${p}`, {
    'X-User-Id': creds.userId,
    'X-Api-Key': creds.apiKey
  }, body);
  if (!res.ok && !data?.jobId) {
    throw new Error((data && data.error) || `API error: ${res.status}`);
  }
  return data;
}

async function toolsRequest(method, p, body, creds) {
  const url = `${(creds.toolsUrl || DEFAULT_TOOLS_URL).replace(/\/$/, '')}${p}`;
  const headers = creds && creds.userId ? {
    'X-User-Id': creds.userId,
    'X-Api-Key': creds.apiKey
  } : {};
  return callJson(method, url, headers, body);
}

// ----------------------------------------------------------------------------
// Pipeline (publish / draft)
// ----------------------------------------------------------------------------

async function pollJob(jobId, creds) {
  for (let i = 0; i < MAX_POLL_ATTEMPTS; i++) {
    await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
    const job = await pipelineRequest('GET', `/jobs/${jobId}`, null, creds);
    if (job.status === 'completed') return job;
    if (job.status === 'failed') throw new Error(job.error || 'Job failed');
    const progress = job.progress || 0;
    const step = job.currentStep || '';
    process.stderr.write(`\r[${progress}%] ${step}...`);
  }
  throw new Error('Job timed out');
}

function parsePublishArgs(argList) {
  const opts = {};
  for (let i = 0; i < argList.length; i++) {
    if (argList[i] === '--theme' && argList[i + 1]) {
      opts.theme = argList[++i];
    } else if (argList[i] === '--rewrite') {
      opts.rewrite = true;
    } else if (argList[i] === '--style' && argList[i + 1]) {
      opts.style = argList[++i];
    } else if (argList[i] === '--prompt' && argList[i + 1]) {
      opts.prompt = argList[++i];
    } else if (!argList[i].startsWith('--')) {
      opts.url = opts.url || argList[i];
    }
  }
  return opts;
}

async function runPublish(action, args) {
  const creds = requireCredentials();
  requirePipelineApi(creds);

  const opts = parsePublishArgs(args);
  if (!opts.url) {
    console.error(JSON.stringify({ success: false, error: 'Missing argument: url' }));
    process.exit(1);
  }

  const body = { url: opts.url, action, theme: opts.theme || 'blackink' };
  if (opts.rewrite) {
    body.rewrite = true;
    body.rewriteOptions = {};
    if (opts.style) body.rewriteOptions.style = opts.style;
    if (opts.prompt) body.rewriteOptions.prompt = opts.prompt;
  }

  try {
    process.stderr.write(`[server] 提交抓取任务: ${opts.url}\n`);
    const response = await pipelineRequest('POST', '/pipeline', body, creds);
    process.stderr.write(`任务已创建: ${response.jobId}\n`);
    const result = await pollJob(response.jobId, creds);
    process.stderr.write('\n');

    console.log(JSON.stringify({
      success: true,
      action: result.result?.action || action,
      title: result.result?.title || '',
      mediaId: result.result?.mediaId || undefined,
      publishId: result.result?.publishId || undefined,
      theme: result.result?.theme || body.theme,
    }, null, 2));
  } catch (err) {
    process.stderr.write('\n');
    console.error(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

async function runStatus(args) {
  const creds = requireCredentials();
  const jobId = args[0];
  if (!jobId) {
    console.error(JSON.stringify({ success: false, error: 'Missing argument: jobId' }));
    process.exit(1);
  }

  try {
    const job = await pipelineRequest('GET', `/jobs/${jobId}`, null, creds);
    console.log(JSON.stringify(job, null, 2));
  } catch (err) {
    console.error(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

// ----------------------------------------------------------------------------
// New: account onboarding
// ----------------------------------------------------------------------------

const PKG_VERSION = (() => {
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
    return pkg.version || '0.0.0';
  } catch (_) {
    return '0.0.0';
  }
})();

async function runLogin() {
  if (process.env.WEB_PUBLISHER_USER_ID && process.env.WEB_PUBLISHER_API_KEY) {
    process.stderr.write('[info] 检测到环境变量已配置，环境变量优先级最高，无需重新登录。\n');
    process.stderr.write('       如需切换账号，请清空 WEB_PUBLISHER_USER_ID / WEB_PUBLISHER_API_KEY 后重试。\n');
    return;
  }

  const toolsUrl = (process.env.WEB_PUBLISHER_TOOLS_URL || DEFAULT_TOOLS_URL).replace(/\/$/, '');

  const initResp = await callJson('POST', `${toolsUrl}/skill/device/init`, {}, {
    clientName: 'web-publisher-cli',
    clientVersion: PKG_VERSION
  });
  if (!initResp.res.ok) {
    console.error(JSON.stringify({
      success: false,
      error: initResp.data?.error || `device/init failed: ${initResp.res.status}`
    }));
    process.exit(1);
  }
  const { deviceCode, userCode, verifyUrl, expiresInSec, pollIntervalSec } = initResp.data;

  process.stderr.write('\n');
  process.stderr.write('请在浏览器中打开以下链接，确认绑定到你的账号：\n');
  process.stderr.write(`  ${verifyUrl}\n`);
  process.stderr.write(`  绑定码: ${userCode}\n`);
  process.stderr.write(`  有效期: ${Math.round(expiresInSec / 60)} 分钟\n`);
  process.stderr.write('\n等待授权…（确认后会自动写入凭证）\n');

  const intervalMs = Math.max(1000, (pollIntervalSec || 2) * 1000);
  const deadline = Date.now() + expiresInSec * 1000;

  while (Date.now() < deadline) {
    await new Promise(r => setTimeout(r, intervalMs));
    const pollResp = await callJson('POST', `${toolsUrl}/skill/device/poll`, {}, { deviceCode });
    if (pollResp.res.status === 410) {
      console.error(JSON.stringify({
        success: false,
        error: pollResp.data?.error || '绑定码已过期或已被使用'
      }));
      process.exit(1);
    }
    if (!pollResp.res.ok) {
      // Transient error, keep polling
      continue;
    }
    if (pollResp.data?.status === 'pending') continue;
    if (pollResp.data?.status === 'bound') {
      const creds = pollResp.data;
      writeCredentialsFile({
        userId: creds.userId,
        apiKey: creds.apiKey,
        apiUrl: creds.apiUrl || '',
        toolsUrl: creds.toolsUrl || toolsUrl,
        boundAt: new Date().toISOString()
      });
      process.stderr.write(`\n登录成功：${creds.name || creds.userId}\n`);
      process.stderr.write(`凭证已保存到 ${CREDENTIALS_PATH} (mode 0600)\n`);
      console.log(JSON.stringify({
        success: true,
        userId: creds.userId,
        apiKey: maskApiKey(creds.apiKey),
        name: creds.name || null
      }, null, 2));
      return;
    }
  }

  console.error(JSON.stringify({ success: false, error: '绑定超时，请重新运行 web-publisher login' }));
  process.exit(1);
}

async function runLogout() {
  const creds = loadCredentials();
  if (!creds) {
    process.stderr.write('当前未登录，无需注销。\n');
    return;
  }
  if (creds.source === 'env') {
    process.stderr.write('当前使用环境变量登录，请清除 WEB_PUBLISHER_USER_ID / WEB_PUBLISHER_API_KEY 环境变量。\n');
    return;
  }
  try {
    await toolsRequest('POST', '/skill/revoke', {}, creds);
  } catch (err) {
    process.stderr.write(`[warn] 远端撤销失败：${err.message}（仍会清理本地凭证）\n`);
  }
  deleteCredentialsFile();
  process.stderr.write('已清理本地凭证。\n');
  console.log(JSON.stringify({ success: true }, null, 2));
}

async function runWhoami() {
  const creds = requireCredentials();
  const { res, data } = await toolsRequest('GET', '/skill/whoami', null, creds);
  if (!res.ok) {
    console.error(JSON.stringify({ success: false, error: data?.error || `HTTP ${res.status}` }));
    process.exit(1);
  }
  console.log(JSON.stringify({
    success: true,
    source: creds.source,
    userId: data.userId,
    name: data.name,
    phone: data.phone,
    apiKey: data.apiKey,
    wechat: data.wechat,
    credits: data.credits
  }, null, 2));
}

async function runWechatConfig() {
  const creds = requireCredentials();
  const { res, data } = await toolsRequest('POST', '/skill/wechat/link', {}, creds);
  if (!res.ok) {
    console.error(JSON.stringify({ success: false, error: data?.error || `HTTP ${res.status}` }));
    process.exit(1);
  }
  process.stderr.write('\n请在浏览器中打开以下链接填写 AppID / AppSecret：\n');
  process.stderr.write(`  ${data.url}\n`);
  process.stderr.write(`  有效期: ${Math.round((data.expiresInSec || 600) / 60)} 分钟\n`);
  if (Array.isArray(data.serverIps) && data.serverIps.length > 0) {
    process.stderr.write('\n请把以下 IP 添加到微信公众平台 IP 白名单：\n');
    for (const ip of data.serverIps) process.stderr.write(`  ${ip}\n`);
  }
  console.log(JSON.stringify({ success: true, url: data.url, serverIps: data.serverIps || [] }, null, 2));
}

async function runWechatStatus() {
  const creds = requireCredentials();
  const { res, data } = await toolsRequest('GET', '/skill/whoami', null, creds);
  if (!res.ok) {
    console.error(JSON.stringify({ success: false, error: data?.error || `HTTP ${res.status}` }));
    process.exit(1);
  }
  console.log(JSON.stringify({
    success: true,
    configured: data.wechat?.configured ?? false,
    appId: data.wechat?.appId ?? null
  }, null, 2));
}

// ----------------------------------------------------------------------------
// Help / dispatch
// ----------------------------------------------------------------------------

function showHelp() {
  console.log(`
web-publisher v${PKG_VERSION} — 将网页文章发布到微信公众号

账号管理（首次使用）:
  login              通过浏览器一次性绑定账号，凭证写入本地
  logout             撤销当前 apiKey 并清除本地凭证
  whoami             查看当前账号、apiKey（已脱敏）与微信配置状态

公众号配置:
  wechat config      生成一次性短链，在浏览器里填写 AppID/AppSecret
  wechat status      查看是否已配置微信公众号

发布:
  draft   <url>      保存为草稿
  publish <url>      直接发布
  status  <jobId>    查询任务状态

发布选项:
  --theme <name>     主题（默认: blackink）
  --rewrite          启用 AI 改写
  --style <style>    改写风格: casual / formal / technical / creative
  --prompt <text>    自定义改写提示

环境变量（可选，优先级高于本地凭证文件）:
  WEB_PUBLISHER_TOOLS_URL  账号 API 地址（默认 https://tools.siping.me/api）
  WEB_PUBLISHER_API_URL    pipeline API 地址（登录后会自动写入凭证）
  WEB_PUBLISHER_USER_ID    用户 ID（如 usr_xxxx）
  WEB_PUBLISHER_API_KEY    API Key

凭证文件: ${CREDENTIALS_PATH} (mode 0600)
`);
}

const command = process.argv[2];
const subcommand = process.argv[3];
const args = process.argv.slice(3);

(async () => {
  try {
    switch (command) {
      case 'login':
        await runLogin();
        break;
      case 'logout':
        await runLogout();
        break;
      case 'whoami':
        await runWhoami();
        break;
      case 'wechat':
        if (subcommand === 'config') {
          await runWechatConfig();
        } else if (subcommand === 'status') {
          await runWechatStatus();
        } else {
          console.error(JSON.stringify({ success: false, error: `Unknown wechat subcommand: ${subcommand || '(none)'}\n用法：web-publisher wechat config|status` }));
          process.exit(1);
        }
        break;
      case 'publish':
        await runPublish('publish', args);
        break;
      case 'draft':
        await runPublish('draft', args);
        break;
      case 'status':
        await runStatus(args);
        break;
      case 'help':
      case '--help':
      case '-h':
      case undefined:
        showHelp();
        break;
      default:
        console.error(JSON.stringify({ success: false, error: `Unknown command: ${command}` }));
        process.exit(1);
    }
  } catch (err) {
    console.error(JSON.stringify({ success: false, error: err.message || String(err) }));
    process.exit(1);
  }
})();
