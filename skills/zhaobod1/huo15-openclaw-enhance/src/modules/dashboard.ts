/**
 * 模块5: 增强仪表盘（多 Agent 隔离版）
 *
 * registerHttpRoute handler 签名:
 *   (req: IncomingMessage, res: ServerResponse) => Promise<boolean | void>
 *
 * 这是 Node.js 原生 HTTP handler，不是 Web Fetch API。
 */
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import type { IncomingMessage, ServerResponse } from "node:http";
import type Database from "better-sqlite3";
import {
  getDb,
  getMemoryStats,
  getSafetyStats,
  getRecentMemories,
  getRecentSafetyEvents,
  getAllAgentIds,
  getOrCreatePet,
  getLatestTodos,
  listTodos,
  listChapters,
  listScheduledBindings,
  searchMemories,
} from "../utils/sqlite-store.js";
import { resolveOpenClawHome } from "../utils/resolve-home.js";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { DEFAULT_AGENT_ID, type DashboardConfig, type Workflow, type NotificationQueue } from "../types.js";
import { buildSnapshot } from "./statusline.js";

function loadAllWorkflows(openclawDir: string): Workflow[] {
  const path = join(openclawDir, "memory", "enhance-workflows.json");
  if (!existsSync(path)) return [];
  try {
    return JSON.parse(readFileSync(path, "utf-8"));
  } catch {
    return [];
  }
}

function parseUrl(req: IncomingMessage): URL {
  return new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);
}

function sendJson(res: ServerResponse, data: unknown): void {
  const body = JSON.stringify(data);
  res.writeHead(200, {
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

function sendHtml(res: ServerResponse, html: string): void {
  res.writeHead(200, {
    "Content-Type": "text/html; charset=utf-8",
    "Content-Length": Buffer.byteLength(html),
  });
  res.end(html);
}

const DASHBOARD_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>龙虾增强包 — 仪表盘</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0f1117;color:#e0e0e0;padding:24px;max-width:1060px;margin:0 auto}
  h1{font-size:1.8em;margin-bottom:8px;color:#ff6b35}
  .subtitle{color:#888;margin-bottom:16px;font-size:0.95em}
  .agent-bar{display:flex;align-items:center;gap:12px;margin-bottom:24px;flex-wrap:wrap}
  .agent-bar label{color:#888;font-size:0.9em}
  .agent-bar select{background:#1a1d27;color:#e0e0e0;border:1px solid #2a2d37;border-radius:6px;padding:6px 12px;font-size:0.9em}
  .agent-bar .current{color:#ff6b35;font-size:0.85em;font-weight:600}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:32px}
  .card{background:#1a1d27;border-radius:12px;padding:20px;border:1px solid #2a2d37}
  .card h3{font-size:0.8em;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
  .card .value{font-size:2em;font-weight:700;color:#ff6b35}
  .card .label{font-size:0.75em;color:#666;margin-top:4px}
  .section{margin-bottom:32px}
  .section h2{font-size:1.2em;margin-bottom:12px;color:#ccc;border-bottom:1px solid #2a2d37;padding-bottom:8px}
  table{width:100%;border-collapse:collapse}
  th,td{text-align:left;padding:8px 12px;border-bottom:1px solid #1a1d27}
  th{color:#888;font-size:0.75em;text-transform:uppercase;letter-spacing:1px}
  td{font-size:0.85em}
  .badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.75em;font-weight:600}
  .badge-block{background:#ff4444;color:#fff}
  .badge-log{background:#444;color:#ccc}
  .badge-allow{background:#2a5a2a;color:#8f8}
  .agent-tag{background:#2a2d37;color:#ff6b35;padding:1px 6px;border-radius:3px;font-size:0.75em;margin-left:4px}
  .empty{color:#555;font-style:italic;padding:16px 0}
  footer{text-align:center;color:#444;font-size:0.8em;margin-top:40px}
</style>
</head>
<body>
<div style="display:flex;align-items:center;justify-content:space-between">
  <div><h1>&#x1F99E; 龙虾增强包 <span id="petBadge" style="font-size:0.5em"></span></h1>
  <p class="subtitle">OpenClaw Enhancement Kit &mdash; Multi-Agent Dashboard</p></div>
  <div id="notifBell" style="position:relative;cursor:pointer;font-size:1.5em" onclick="toggleNotif()" title="通知">&#x1F514;<span id="notifCount" style="position:absolute;top:-4px;right:-8px;background:#ff4444;color:#fff;border-radius:50%;font-size:0.45em;padding:2px 6px;display:none"></span></div>
</div>
<div id="notifPanel" style="display:none;background:#1a1d27;border:1px solid #2a2d37;border-radius:8px;padding:12px;margin-bottom:16px;max-height:240px;overflow-y:auto"></div>

<div class="agent-bar">
  <label>Agent:</label>
  <select id="agentSelect" onchange="switchAgent(this.value)">
    <option value="">全部 (聚合)</option>
  </select>
  <span class="current" id="currentAgent"></span>
</div>

<div class="grid" id="stats"></div>

<div class="section">
  <h2>最近记忆</h2>
  <div id="memories"></div>
</div>

<div class="section">
  <h2>安全事件</h2>
  <div id="safety"></div>
</div>

<div class="section">
  <h2>当前任务 (TodoWrite)</h2>
  <div id="todos"></div>
</div>

<div class="section">
  <h2>章节时间线</h2>
  <div id="chapters"></div>
</div>

<div class="section">
  <h2>定时工作流 (openclaw cron 桥)</h2>
  <div id="loops"></div>
</div>

<div class="section">
  <h2>子任务孵化 (spawn-task)</h2>
  <div id="spawnTasks"></div>
</div>

<div class="section">
  <h2>工作流 (旧式触发词)</h2>
  <div id="workflows"></div>
</div>

<footer>龙虾增强包 v2.2.0 &mdash; 非侵入式增强 &middot; 记忆以龙虾为主 | <a href="/plugins/enhance/pet" style="color:#ff6b35">&#x1F525; 小火苗</a></footer>

<script>
// 本地仪表盘：仅请求同域 /plugins/enhance/api/status，无外部网络调用
var currentAgent = '';

function esc(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function card(title, value, label) {
  var el = document.createElement('div');
  el.className = 'card';
  el.innerHTML = '<h3>' + esc(title) + '</h3><div class="value">' + esc(String(value)) + '</div><div class="label">' + esc(label) + '</div>';
  return el.outerHTML;
}

function buildTable(headers, rows) {
  if (!rows.length) return '<p class="empty">暂无数据</p>';
  var head = '<tr>' + headers.map(function(h){ return '<th>' + esc(h) + '</th>'; }).join('') + '</tr>';
  return '<table>' + head + rows.join('') + '</table>';
}

function switchAgent(v) {
  currentAgent = v;
  var u = new URL(location.href);
  if (v) {
    u.searchParams.set('agent', v);
  } else {
    u.searchParams.delete('agent');
  }
  history.replaceState(null, '', u);
  load();
}

function load() {
  var apiPath = '/plugins/enhance/api/status';
  if (currentAgent) {
    apiPath += '?agent=' + encodeURIComponent(currentAgent);
  }

  fetch(apiPath)
    .then(function(resp) { return resp.json(); })
    .then(function(d) {
      // Agent 选择器
      var sel = document.getElementById('agentSelect');
      var opts = '<option value="">全部 (聚合)</option>';
      d.agents.forEach(function(a) {
        opts += '<option value="' + esc(a) + '"' + (a === currentAgent ? ' selected' : '') + '>' + esc(a) + '</option>';
      });
      sel.innerHTML = opts;
      document.getElementById('currentAgent').textContent = currentAgent ? '当前: ' + currentAgent : '全部 Agent 聚合视图';

      // 统计卡片
      document.getElementById('stats').innerHTML = [
        card('Agent 数', d.agents.length, '个'),
        card('记忆总数', d.memory.total, '条'),
        card('用户记忆', d.memory.user || 0, '条'),
        card('项目记忆', d.memory.project || 0, '条'),
        card('安全事件', d.safety.total, '次'),
        card('已拦截', d.safety.blocked, '次'),
        card('工作流', d.workflows.length, '个'),
      ].join('');

      // 最近记忆表
      var memRows = d.recentMemories.map(function(e) {
        return '<tr><td>#' + e.id + '</td><td><span class="agent-tag">' + esc(e.agent_id) + '</span></td><td>' + esc(e.category) + '</td><td>' + esc(e.content).slice(0, 50) + '</td><td>' + esc(e.created_at) + '</td></tr>';
      });
      document.getElementById('memories').innerHTML = buildTable(['ID','Agent','类型','内容','时间'], memRows);

      // 安全事件表
      var sfRows = d.recentSafety.map(function(e) {
        return '<tr><td><span class="badge badge-' + esc(e.action) + '">' + esc(e.action) + '</span></td><td><span class="agent-tag">' + esc(e.agent_id) + '</span></td><td>' + esc(e.tool) + '</td><td>' + esc(e.params || '').slice(0, 35) + '</td><td>' + esc(e.created_at) + '</td></tr>';
      });
      document.getElementById('safety').innerHTML = buildTable(['动作','Agent','工具','参数','时间'], sfRows);

      // 工作流表
      var wfRows = d.workflows.map(function(e) {
        return '<tr><td>' + esc(e.name) + '</td><td><span class="agent-tag">' + esc(e.agent_id || 'main') + '</span></td><td>' + esc(e.trigger) + '</td><td>' + (e.enabled ? '✅' : '⏸') + '</td></tr>';
      });
      document.getElementById('workflows').innerHTML = buildTable(['名称','Agent','触发词','状态'], wfRows);
    });
}

function statusIcon(s) {
  if (s === 'completed') return '✅';
  if (s === 'in_progress') return '▶';
  return '⭕';
}

function loadTodos() {
  var path = '/plugins/enhance/api/todos';
  if (currentAgent) path += '?agent=' + encodeURIComponent(currentAgent);
  fetch(path).then(function(r){return r.json()}).then(function(d){
    if (!d.todos || !d.todos.length) {
      document.getElementById('todos').innerHTML = '<p class="empty">暂无 todos。Agent 可调用 enhance_todo_write 登记。</p>';
      return;
    }
    var rows = d.todos.map(function(t){
      return '<tr><td>' + statusIcon(t.status) + '</td><td>' + esc(t.content) + '</td><td style="color:#666">' + esc(t.active_form || '') + '</td><td>' + esc(t.updated_at) + '</td></tr>';
    });
    document.getElementById('todos').innerHTML = buildTable(['状态','任务','进行中表述','更新'], rows);
  }).catch(function(){});
}

function loadChapters() {
  var path = '/plugins/enhance/api/chapters';
  if (currentAgent) path += '?agent=' + encodeURIComponent(currentAgent);
  fetch(path).then(function(r){return r.json()}).then(function(d){
    if (!d.chapters || !d.chapters.length) {
      document.getElementById('chapters').innerHTML = '<p class="empty">暂无章节。Agent 可调用 enhance_mark_chapter。</p>';
      return;
    }
    var rows = d.chapters.slice(0, 20).map(function(c){
      return '<tr><td>' + esc(c.created_at) + '</td><td>' + esc(c.title) + '</td><td style="color:#888">' + esc(c.summary || '') + '</td></tr>';
    });
    document.getElementById('chapters').innerHTML = buildTable(['时间','标题','摘要'], rows);
  }).catch(function(){});
}

function loadLoops() {
  var path = '/plugins/enhance/api/loops';
  if (currentAgent) path += '?agent=' + encodeURIComponent(currentAgent);
  fetch(path).then(function(r){return r.json()}).then(function(d){
    if (!d.loops || !d.loops.length) {
      document.getElementById('loops').innerHTML = '<p class="empty">暂无定时工作流。调用 enhance_loop_register 登记。</p>';
      return;
    }
    var rows = d.loops.map(function(l){
      return '<tr><td>' + (l.enabled ? '●' : '○') + '</td><td>' + esc(l.name) + '</td><td><span class="agent-tag">' + esc(l.agent_id) + '</span></td><td><code>' + esc(l.cron_ref) + '</code></td><td>' + esc(l.last_fired_at || '从未') + '</td></tr>';
    });
    document.getElementById('loops').innerHTML = buildTable(['状态','名称','Agent','cron','上次触发'], rows);
  }).catch(function(){});
}

function loadSpawnTasks() {
  var path = '/plugins/enhance/api/spawn-tasks';
  if (currentAgent) path += '?agent=' + encodeURIComponent(currentAgent);
  fetch(path).then(function(r){return r.json()}).then(function(d){
    if (!d.entries || !d.entries.length) {
      document.getElementById('spawnTasks').innerHTML = '<p class="empty">暂无孵化子任务。调用 enhance_spawn_task 登记。</p>';
      return;
    }
    var rows = d.entries.map(function(e){
      var text = esc((e.content || '').slice(0, 160));
      return '<tr><td>#' + e.id + '</td><td>' + esc(e.created_at) + '</td><td style="white-space:pre-wrap">' + text + '</td></tr>';
    });
    document.getElementById('spawnTasks').innerHTML = buildTable(['ID','时间','内容摘要'], rows);
  }).catch(function(){});
}

function toggleNotif() {
  var p = document.getElementById('notifPanel');
  p.style.display = p.style.display === 'none' ? 'block' : 'none';
}

function loadNotif() {
  var path = '/plugins/enhance/api/notifications';
  if (currentAgent) path += '?agent=' + encodeURIComponent(currentAgent);
  fetch(path).then(function(r){return r.json()}).then(function(d){
    var countEl = document.getElementById('notifCount');
    if (d.unread > 0) { countEl.textContent = d.unread; countEl.style.display = 'inline'; }
    else { countEl.style.display = 'none'; }
    var panel = document.getElementById('notifPanel');
    if (!d.recent.length) { panel.innerHTML = '<p class="empty">暂无通知</p>'; return; }
    panel.innerHTML = d.recent.map(function(n){
      var icon = n.level === 'success' ? '✅' : n.level === 'warn' ? '⚠️' : 'ℹ️';
      return '<div style="padding:4px 0;border-bottom:1px solid #2a2d37;font-size:0.85em">' + icon + ' <b>' + esc(n.title) + '</b> <span style="color:#666;font-size:0.8em">' + esc(n.created_at) + '</span></div>';
    }).join('');
  });
}

function loadPetBadge() {
  var path = '/plugins/enhance/api/pet';
  if (currentAgent) path += '?agent=' + encodeURIComponent(currentAgent);
  fetch(path).then(function(r){return r.json()}).then(function(d){
    if (d && d.name) {
      document.getElementById('petBadge').innerHTML = '&#x1F525; ' + esc(d.name) + ' Lv.' + d.level;
    }
  });
}

var params = new URLSearchParams(location.search);
currentAgent = params.get('agent') || '';
function refreshAll() {
  load();
  loadNotif();
  loadPetBadge();
  loadTodos();
  loadChapters();
  loadLoops();
  loadSpawnTasks();
}
refreshAll();
// 原 switchAgent 只触发 load()，这里扩展为全量刷新
switchAgent = function(v){
  currentAgent = v;
  var u = new URL(location.href);
  if (v) u.searchParams.set('agent', v); else u.searchParams.delete('agent');
  history.replaceState(null, '', u);
  refreshAll();
};
</script>
</body>
</html>`;

const PET_PAGE_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>小火苗 — 龙虾增强包</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0f1117;color:#e0e0e0;padding:24px;max-width:600px;margin:0 auto;text-align:center}
  h1{font-size:2em;margin-bottom:4px;color:#ff6b35}
  .subtitle{color:#888;margin-bottom:24px}
  .flame-container{position:relative;width:200px;height:200px;margin:0 auto 24px}
  .flame{width:60px;height:80px;border-radius:50% 50% 50% 50% / 60% 60% 40% 40%;position:absolute;bottom:40px;left:50%;transform:translateX(-50%);animation:flicker 1.5s ease-in-out infinite alternate}
  .flame.orange{background:linear-gradient(to top,#ff4500,#ff8c00,#ffd700);box-shadow:0 0 30px #ff4500,0 0 60px #ff8c0088}
  .flame.blue{background:linear-gradient(to top,#1e90ff,#00bfff,#87ceeb);box-shadow:0 0 30px #1e90ff,0 0 60px #00bfff88}
  .flame.purple{background:linear-gradient(to top,#8b00ff,#da70d6,#dda0dd);box-shadow:0 0 30px #8b00ff,0 0 60px #da70d688}
  .flame.green{background:linear-gradient(to top,#228b22,#32cd32,#90ee90);box-shadow:0 0 30px #228b22,0 0 60px #32cd3288}
  .flame.white{background:linear-gradient(to top,#dcdcdc,#f5f5f5,#fff);box-shadow:0 0 30px #dcdcdc,0 0 60px #ffffff88}
  .base{width:50px;height:20px;background:#555;border-radius:0 0 8px 8px;position:absolute;bottom:24px;left:50%;transform:translateX(-50%)}
  @keyframes flicker{0%{transform:translateX(-50%) scale(1) rotate(-2deg)}50%{transform:translateX(-50%) scale(1.05) rotate(1deg)}100%{transform:translateX(-50%) scale(0.97) rotate(-1deg)}}
  .info{background:#1a1d27;border-radius:12px;padding:20px;border:1px solid #2a2d37;margin-bottom:16px;text-align:left}
  .info h2{color:#ff6b35;font-size:1.1em;margin-bottom:12px}
  .stat-row{display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:0.9em}
  .stat-bar{flex:1;height:8px;background:#2a2d37;border-radius:4px;overflow:hidden}
  .stat-fill{height:100%;border-radius:4px;background:linear-gradient(90deg,#ff6b35,#ffd700)}
  .xp-bar{width:100%;height:12px;background:#2a2d37;border-radius:6px;overflow:hidden;margin:8px 0}
  .xp-fill{height:100%;border-radius:6px;background:linear-gradient(90deg,#ff6b35,#ff8c00)}
  .actions{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}
  .actions button{background:#1a1d27;color:#ff6b35;border:1px solid #ff6b35;border-radius:8px;padding:8px 16px;cursor:pointer;font-size:0.9em}
  .actions button:hover{background:#ff6b35;color:#0f1117}
  #msg{color:#888;margin-top:12px;font-size:0.9em;min-height:1.5em}
  a{color:#ff6b35}
</style>
</head>
<body>
<h1 id="petTitle">&#x1F525; 小火苗</h1>
<p class="subtitle" id="petPersonality"></p>

<div class="flame-container">
  <div class="flame orange" id="flameEl"></div>
  <div class="base"></div>
</div>

<div class="info">
  <h2>等级 <span id="lvl"></span> &mdash; <span id="sizeLabel"></span></h2>
  <div class="xp-bar"><div class="xp-fill" id="xpBar" style="width:0%"></div></div>
  <p style="font-size:0.8em;color:#888" id="xpText"></p>
</div>

<div class="info">
  <h2>属性</h2>
  <div class="stat-row">🌡️ 温暖 <span id="sWarmth">0</span><div class="stat-bar"><div class="stat-fill" id="bWarmth"></div></div></div>
  <div class="stat-row">💡 明亮 <span id="sBrightness">0</span><div class="stat-bar"><div class="stat-fill" id="bBrightness"></div></div></div>
  <div class="stat-row">🪨 稳定 <span id="sStability">0</span><div class="stat-bar"><div class="stat-fill" id="bStability"></div></div></div>
  <div class="stat-row">✨ 灵感 <span id="sSpark">0</span><div class="stat-bar"><div class="stat-fill" id="bSpark"></div></div></div>
  <div class="stat-row">🔋 耐力 <span id="sEndurance">0</span><div class="stat-bar"><div class="stat-fill" id="bEndurance"></div></div></div>
</div>

<div class="actions">
  <button onclick="interact('feed')">🍎 喂食</button>
  <button onclick="interact('pat')">🤚 拍拍</button>
</div>
<p id="msg"></p>
<p style="margin-top:24px"><a href="/plugins/enhance">&larr; 返回仪表盘</a></p>

<script>
function loadPet() {
  fetch('/plugins/enhance/api/pet')
    .then(function(r){return r.json()})
    .then(function(d) {
      document.getElementById('petTitle').innerHTML = '&#x1F525; ' + d.name;
      document.getElementById('petPersonality').textContent = d.personality;
      document.getElementById('lvl').textContent = 'Lv.' + d.level;
      document.getElementById('sizeLabel').textContent = d.size;
      var xpNeeded = 50 + d.level * 30;
      document.getElementById('xpBar').style.width = (d.xp / xpNeeded * 100) + '%';
      document.getElementById('xpText').textContent = d.xp + ' / ' + xpNeeded + ' XP (累计 ' + d.total_xp + ')';
      var fl = document.getElementById('flameEl');
      fl.className = 'flame ' + d.color;
      var scale = d.size === 'tiny' ? 0.6 : d.size === 'small' ? 0.8 : d.size === 'medium' ? 1 : 1.3;
      fl.style.transform = 'translateX(-50%) scale(' + scale + ')';
      ['warmth','brightness','stability','spark','endurance'].forEach(function(k){
        var v = d.stats[k] || 0;
        document.getElementById('s'+k.charAt(0).toUpperCase()+k.slice(1)).textContent = v;
        document.getElementById('b'+k.charAt(0).toUpperCase()+k.slice(1)).style.width = v + '%';
      });
    });
}
function interact(action) {
  fetch('/plugins/enhance/api/pet/interact', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:action})})
    .then(function(r){return r.json()})
    .then(function(d){ document.getElementById('msg').textContent = d.message; loadPet(); });
}
loadPet();
</script>
</body>
</html>`;

export function registerDashboard(api: OpenClawPluginApi, _config?: DashboardConfig, notifyQueue?: NotificationQueue, sharedDb?: Database.Database) {
  const openclawDir = resolveOpenClawHome(api);

  api.registerHttpRoute({
    path: "/plugins/enhance",
    match: "prefix",
    auth: "plugin",
    handler: async (req: IncomingMessage, res: ServerResponse) => {
      const url = parseUrl(req);
      const pathname = url.pathname;

      if (pathname === "/plugins/enhance/api/status") {
        const db = sharedDb ?? getDb(openclawDir);
        const agentFilter = url.searchParams.get("agent") || undefined;

        const agents = getAllAgentIds(db);
        const memoryStats = getMemoryStats(db, agentFilter);
        const safetyStats = getSafetyStats(db, agentFilter);

        const recentMemories = agentFilter
          ? getRecentMemories(db, agentFilter, 15)
          : (() => {
              const all: any[] = [];
              for (const aid of agents) {
                all.push(...getRecentMemories(db, aid, 5));
              }
              return all.sort((a: any, b: any) => b.created_at.localeCompare(a.created_at)).slice(0, 15);
            })();

        const recentSafety = getRecentSafetyEvents(db, agentFilter, 15);

        const allWorkflows = loadAllWorkflows(openclawDir);
        const workflows = agentFilter
          ? allWorkflows.filter((w) => w.agent_id === agentFilter)
          : allWorkflows;

        sendJson(res, { agents, memory: memoryStats, safety: safetyStats, recentMemories, recentSafety, workflows });
        return true;
      }

      // 宠物 JSON API
      if (pathname === "/plugins/enhance/api/pet") {
        const db = sharedDb ?? getDb(openclawDir);
        const agentId = url.searchParams.get("agent") || DEFAULT_AGENT_ID;
        const pet = getOrCreatePet(db, agentId);
        sendJson(res, pet);
        return true;
      }

      // 宠物互动 API
      if (pathname === "/plugins/enhance/api/pet/interact" && req.method === "POST") {
        const db = sharedDb ?? getDb(openclawDir);
        let body = "";
        for await (const chunk of req) body += chunk;
        try {
          const { action, agentId: aid } = JSON.parse(body);
          const agentId = aid || DEFAULT_AGENT_ID;
          const { addPetXp: addXp } = await import("../utils/sqlite-store.js");
          if (action === "feed") {
            const { pet, leveledUp } = addXp(db, agentId, 10, { warmth: 2 });
            let msg = `${pet.name} 开心地吃了一口！+10 XP`;
            if (leveledUp) {
              msg += ` 升级到 Lv.${pet.level}！`;
              notifyQueue?.emit(agentId, "success", "pet", `🔥 ${pet.name} 升级到 Lv.${pet.level}！`);
            }
            sendJson(res, { ok: true, message: msg });
          } else if (action === "pat") {
            const { pet, leveledUp } = addXp(db, agentId, 3, { warmth: 1 });
            let msg = `${pet.name} 开心地跳了跳！+3 XP`;
            if (leveledUp) {
              msg += ` 升级到 Lv.${pet.level}！`;
              notifyQueue?.emit(agentId, "success", "pet", `🔥 ${pet.name} 升级到 Lv.${pet.level}！`);
            }
            sendJson(res, { ok: true, message: msg });
          } else {
            sendJson(res, { ok: false, message: "未知操作" });
          }
        } catch {
          sendJson(res, { ok: false, message: "请求解析失败" });
        }
        return true;
      }

      // 通知 API
      if (pathname === "/plugins/enhance/api/notifications") {
        const agentId = url.searchParams.get("agent") || undefined;
        const limit = parseInt(url.searchParams.get("limit") ?? "20", 10);
        const recent = notifyQueue?.getRecent(agentId, limit) ?? [];
        const unread = notifyQueue?.getUnreadCount(agentId) ?? 0;
        sendJson(res, { recent, unread });
        return true;
      }

      // 状态栏快照 JSON（供 Control UI / 外部嵌入）
      if (pathname === "/plugins/enhance/api/statusline") {
        const db = sharedDb ?? getDb(openclawDir);
        const agentId = url.searchParams.get("agent") || DEFAULT_AGENT_ID;
        const sessionId = url.searchParams.get("session") || "";
        const snap = notifyQueue ? buildSnapshot(db, agentId, sessionId, notifyQueue) : null;
        sendJson(res, snap ?? { error: "notifyQueue not available" });
        return true;
      }

      // Todos 列表（最近一个 session）
      if (pathname === "/plugins/enhance/api/todos") {
        const db = sharedDb ?? getDb(openclawDir);
        const agentId = url.searchParams.get("agent") || DEFAULT_AGENT_ID;
        const todos = getLatestTodos(db, agentId);
        sendJson(res, { agentId, todos });
        return true;
      }

      // Chapter marks
      if (pathname === "/plugins/enhance/api/chapters") {
        const db = sharedDb ?? getDb(openclawDir);
        const agentId = url.searchParams.get("agent") || DEFAULT_AGENT_ID;
        const sessionId = url.searchParams.get("session") || undefined;
        const chapters = listChapters(db, agentId, sessionId, 50);
        sendJson(res, { agentId, chapters });
        return true;
      }

      // 定时工作流桥列表
      if (pathname === "/plugins/enhance/api/loops") {
        const db = sharedDb ?? getDb(openclawDir);
        const agentId = url.searchParams.get("agent") || undefined;
        const loops = listScheduledBindings(db, agentId);
        sendJson(res, { loops });
        return true;
      }

      // 子任务孵化清单（从 memory 里过滤 tag=spawn-task）
      if (pathname === "/plugins/enhance/api/spawn-tasks") {
        const db = sharedDb ?? getDb(openclawDir);
        const agentId = url.searchParams.get("agent") || DEFAULT_AGENT_ID;
        const entries = searchMemories(db, agentId, { keyword: "spawn-task", limit: 30 });
        sendJson(res, { agentId, entries });
        return true;
      }

      // 宠物独立页面
      if (pathname === "/plugins/enhance/pet") {
        sendHtml(res, PET_PAGE_HTML);
        return true;
      }

      // 默认: 仪表盘 HTML
      sendHtml(res, DASHBOARD_HTML);
      return true;
    },
  });

  api.logger.info("[enhance] 仪表盘模块已加载（v2.2.0：Todos / 章节 / 定时 / Spawn-task），访问 /plugins/enhance/");
}
