/**
 * 火一五·辉火云企业套件插件 v1.9
 *
 * 品牌口径：对外统一称"辉火云企业套件"。代码内部的类名/文件名/tool 名沿用
 * 历史标识符（OdooClient/odoo-client.ts/odoo_*），因为改动会破坏 agent
 * 历史 memory 与已部署配置；它们仅作为技术 id 存在，不进入用户可见文案。
 *
 * v1.9 品牌化：
 * - 所有用户可见文案（tool description、prompt hint、错误消息、通知文案）
 *   统一使用"辉火云企业套件"/"辉火云"
 * - 加入 prompt 硬规则：对外沟通时不得透露第三方商标
 *
 * v1.8：Project/Ticket/Chatter 闭环（+13 tools）
 * v1.7：Daily Inbox 闭环（活动/日历/邮件/附件/关注者/批量/撤销）
 * v1.6：跨渠道通知基座（企微/钉钉/飞书）+ per-agent 偏好 + 入站回复 + 知识库
 * v1.2：per-agent 凭据隔离
 */

import { definePluginEntry } from 'openclaw/plugin-sdk/plugin-entry';
import type { OpenClawPluginApi } from 'openclaw/plugin-sdk';
import { OdooClient } from './src/modules/odoo-client.js';
import { NotificationPoller } from './src/modules/notification-poller.js';
import { ConfigManager } from './src/modules/config-manager.js';
import { notificationBus } from './src/modules/notification-bus.js';
import { toEnvelope } from './src/modules/notification-router.js';
import { PrefsManager, shouldDeliver, DEFAULT_PREFS } from './src/modules/notification-prefs.js';
import { EnvelopeCache } from './src/modules/envelope-cache.js';
import { mutationLog } from './src/modules/mutation-log.js';
import { mdToHtml } from './src/utils/md-to-html.js';
import { readFileSync, statSync } from 'node:fs';
import { basename } from 'node:path';
import type {
  OdooPluginConfig,
  SyncUpdate,
  NotificationEnvelope,
  NotificationPreferences,
  NotificationKind,
  NotificationPriority,
  InboundReply,
} from './src/types/index.js';
import { today, tomorrow } from './src/utils/date-utils.js';

const odooClients = new Map<string, OdooClient>();
const pollers = new Map<string, NotificationPoller>();
const configManager = new ConfigManager();
const prefsManager = new PrefsManager();
const envelopeCache = new EnvelopeCache();
let replyUnsubscribe: (() => void) | null = null;

export default definePluginEntry({
  id: 'odoo',
  name: '火一五·辉火云企业套件插件',
  description: '自然语言操作辉火云企业套件，实施经理助手，per-agent 凭据隔离',

  register(api: OpenClawPluginApi) {
    // 不在启动时全局连接。每个 agent 的连接在 before_prompt_build 或 odoo_connect 时按需恢复。
    registerTools(api);
    registerHooks(api);

    // 订阅入站回复 —— 渠道收到用户回复后调用 bus.reply()，这里把文字写回 辉火云内部动态
    replyUnsubscribe?.();
    replyUnsubscribe = notificationBus.onReply(async (reply) => {
      await handleInboundReply(api, reply);
    });

    api.logger.info('[odoo] 辉火云企业套件插件 v1.9 已加载（per-agent 隔离 + 跨渠道通知基座 + 入站回复 + 品牌化）');
  },
});

// ── 公共 API：供企微 / 钉钉 / 飞书等渠道插件作为依赖引入 ────────────────────
// 方式 A（推荐）：
//   import { notificationBus } from '@huo15/huo15-huihuoyun-odoo';
//   notificationBus.subscribe(env => { ... });
// 方式 B（无依赖解耦）：
//   const bus = (globalThis as any)[Symbol.for('openclaw.huo15.notification-bus.v1')];
export { notificationBus } from './src/modules/notification-bus.js';
export type {
  NotificationEnvelope,
  NotificationKind,
  NotificationPriority,
  ChannelTarget,
  ChannelTransport,
  DeliveryResult,
} from './src/types/index.js';

// ── 初始化客户端（per-agent）─────────────────────────────────────────────────
async function initOdooClient(
  api: OpenClawPluginApi,
  odooConfig: NonNullable<OdooPluginConfig['odoo']>,
  agentId: string = 'default',
): Promise<OdooClient> {
  const client = new OdooClient(odooConfig);
  await client.authenticate();
  odooClients.set(agentId, client);

  const syncConfig = ((api.pluginConfig ?? {}) as OdooPluginConfig).sync ?? {
    enabled: true, intervalSeconds: 30, channels: ['todo', 'activity', 'message'],
  };

  if (syncConfig.enabled !== false) {
    pollers.get(agentId)?.stop();
    const poller = new NotificationPoller(client);
    pollers.set(agentId, poller);
    poller.start((updates: SyncUpdate[]) => handleOdooUpdates(api, updates, agentId),
      { intervalSeconds: syncConfig.intervalSeconds, channels: syncConfig.channels });
  }

  api.logger.info(`[odoo] agent=${agentId} 已连接 ${odooConfig.url}，uid=${client.getUid()}`);
  return client;
}

/**
 * 尝试恢复 agent 连接 —— 走 fallback 链，静默失败。
 *
 * 查找顺序（v1.10 共享凭据模型）：
 *   1) `{agentId}.json`          该 agent 的独立凭据（private）
 *   2) `default.json`            共享凭据（首次 connect 默认写这里）
 *   3) legacy `odoo-config.json` 向下兼容
 *   4) `api.pluginConfig.odoo`   manifest 预填的静态凭据（零配置部署）
 *
 * 1-3 由 ConfigManager.load 内部处理；4 在这里兜底。
 * 只要任一层命中，就 init client 缓存在 odooClients[agentId] 下 —— 不同 agent
 * 命中同一份凭据时各自持有独立的 OdooClient 实例，session 隔离。
 */
async function tryRestoreAgent(api: OpenClawPluginApi, agentId: string): Promise<OdooClient | undefined> {
  if (odooClients.get(agentId)?.isAuthenticated()) return odooClients.get(agentId);

  // 1-3: ConfigManager 内置 fallback
  let saved = configManager.load(agentId);

  // 4: pluginConfig 兜底
  let sourceLabel: string;
  if (!saved?.odoo) {
    const fromManifest = (api.pluginConfig as OdooPluginConfig | undefined)?.odoo;
    if (!fromManifest) return undefined;
    saved = { odoo: fromManifest };
    sourceLabel = 'pluginConfig';
  } else {
    sourceLabel = configManager.getActiveSource(agentId);
  }

  try {
    api.logger.info(`[odoo] 恢复 agent=${agentId} 的连接（来源: ${sourceLabel}）...`);
    return await initOdooClient(api, saved.odoo!, agentId);
  } catch (err) {
    api.logger.error(`[odoo] agent=${agentId} 恢复失败（来源 ${sourceLabel}）: ${err instanceof Error ? err.message : String(err)}`);
    return undefined;
  }
}

// ── 工具辅助 ──────────────────────────────────────────────────────────────────
function getClient(ctx: Record<string, unknown>): OdooClient | undefined {
  const aid = getAgentId(ctx);
  const client = odooClients.get(aid);
  return client?.isAuthenticated() ? client : undefined;
}
function notConnected() {
  return { success: false, message: '未连接到辉火云企业套件，请先提供系统地址、用户名和密码进行连接。' };
}
function getAgentId(ctx: Record<string, unknown>) {
  return (ctx['agentId'] as string | undefined)?.trim() || 'default';
}
function stripHtml(html: string) {
  return String(html ?? '').replace(/<[^>]+>/g, '').trim().substring(0, 300);
}

/**
 * 把后端 read() 返回的字段值归一化为 write() 可接受的形式。
 *   - null / undefined / false → false
 *   - many2one: [id, "名称"]    → id（write 只收 id）
 *   - many2many: [id1, id2, …]  → [[6, false, [id1, id2, …]]]（write 要求 command tuple）
 *   - 其它标量：原样保留
 */
function normalizeFieldSnapshot(v: unknown): unknown {
  if (v === null || v === undefined || v === false) return false;
  if (Array.isArray(v)) {
    if (v.length === 2 && typeof v[0] === 'number' && typeof v[1] === 'string') {
      return v[0]; // many2one
    }
    if (v.every(x => typeof x === 'number')) {
      return [[6, false, v]]; // many2many
    }
  }
  return v;
}

/**
 * 有审计的 write：先读旧值快照，再 write，再把变更写入 mutation-log。
 * 用于所有用户触发的单/多记录更新，让"撤销上一步"可用。
 */
async function loggedWrite(
  client: OdooClient,
  ctx: Record<string, unknown>,
  args: {
    tool: string;
    model: string;
    ids: number[];
    values: Record<string, unknown>;
    summary: string;
  },
): Promise<void> {
  const fields = Object.keys(args.values);
  let before: Record<string, unknown>[] = [];
  if (fields.length > 0) {
    try {
      const recs = await client.read(args.model, args.ids, fields);
      before = args.ids.map(id => {
        const r = (recs.find(rr => rr['id'] === id) ?? {}) as Record<string, unknown>;
        const snap: Record<string, unknown> = { id };
        for (const f of fields) {
          snap[f] = normalizeFieldSnapshot(r[f]);
        }
        return snap;
      });
    } catch {
      before = []; // 快照失败 → 不可逆但不阻断 write
    }
  }
  await client.write(args.model, args.ids, args.values);
  mutationLog.append(getAgentId(ctx), {
    tool: args.tool,
    model: args.model,
    ids: args.ids,
    before,
    after: args.values,
    reversible: before.length === args.ids.length && before.length > 0,
    summary: args.summary,
  });
}

// ── 注册工具（共 32 个）──────────────────────────────────────────────────────
function registerTools(api: OpenClawPluginApi) {

  // ══════════════════════════════════════════════════════
  // 连接 & 状态
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_connect',
    description: '连接辉火云企业套件。默认保存为【共享凭据】—— 组织内所有渠道（企微/钉钉/飞书）的所有 agent 都会自动复用，无需每个人重新输入。如需给当前会话单独使用一套专属凭据，传 private=true。db 为可选，不传则自动检测（单库自动、多库返回列表）。',
    schema: {
      type: 'object',
      properties: {
        url:      { type: 'string', description: '辉火云企业套件 系统地址，如 https://www.huo15.com' },
        db:       { type: 'string', description: '数据库名称（可选，只有一个数据库时可省略）' },
        username: { type: 'string', description: '用户名（邮箱或登录名）' },
        password: { type: 'string', description: '密码' },
        private:  { type: 'boolean', description: '可选，默认 false。true = 仅保存为当前会话专属凭据（只覆盖当前 agent）；false = 保存为组织共享凭据（全员复用，推荐）' },
      },
      required: ['url', 'username', 'password'],
    },
    async handler(
      params: { url: string; db?: string; username: string; password: string; private?: boolean },
      ctx: Record<string, unknown>,
    ) {
      const aid = getAgentId(ctx);
      let db = params.db;

      // 未指定 db 时自动检测
      if (!db) {
        try {
          const dbs = await OdooClient.listDatabases(params.url);
          if (dbs.length === 0) return { success: false, message: '该辉火云实例没有可用的数据库' };
          if (dbs.length === 1) {
            db = dbs[0];
          } else {
            return { success: false, needSelectDb: true, databases: dbs, message: `检测到 ${dbs.length} 个数据库，请告诉我要连接哪一个：${dbs.join('、')}` };
          }
        } catch {
          return { success: false, message: '无法自动检测数据库列表，请手动提供数据库名称（db 参数）' };
        }
      }

      const cfg = { url: params.url, db, username: params.username, password: params.password };
      const scope: 'shared' | 'agent' = params.private ? 'agent' : 'shared';
      try {
        await initOdooClient(api, cfg, aid);
        configManager.saveOdooConfig(cfg, aid, scope);
        const scopeMsg = scope === 'shared'
          ? '已保存为【共享凭据】—— 组织内所有渠道的 @ 机器人用户都会自动使用这套凭据，无需再输入。'
          : '已保存为【当前会话专属凭据】—— 只对当前 agent 生效，不影响其他成员。';
        return {
          success: true,
          scope,
          message: `已成功连接到 ${params.url}（数据库: ${db}），欢迎使用辉火云企业套件！${scopeMsg}`,
        };
      } catch (e) { return { success: false, message: `连接失败: ${e instanceof Error ? e.message : String(e)}` }; }
    },
  });

  api.registerTool({
    name: 'odoo_status',
    description: '检查辉火云企业套件连接状态',
    schema: { type: 'object', properties: {} },
    async handler(_p: unknown, ctx: Record<string, unknown>) {
      const aid = getAgentId(ctx);
      const client = odooClients.get(aid);
      const info = client?.getSessionInfo();
      return { success: true, connected: client?.isAuthenticated() ?? false, agentId: aid, uid: info?.uid ?? null, username: info?.username ?? null, url: info?.url ?? null, polling: pollers.get(aid)?.getStatus() ?? null };
    },
  });

  api.registerTool({
    name: 'odoo_disconnect',
    description: '断开当前会话的辉火云企业套件连接。默认安全模式：只清除当前 agent 的【独立凭据】（如有），不会影响组织的【共享凭据】。如需彻底清除全员共用的共享凭据（高危，会导致所有成员断开），传 force_shared=true。',
    schema: {
      type: 'object',
      properties: {
        force_shared: { type: 'boolean', description: '可选，默认 false。true = 同时清除组织共享凭据（影响所有成员）；false = 只断开当前会话，保留共享凭据' },
      },
    },
    async handler(p: { force_shared?: boolean } | undefined, ctx: Record<string, unknown>) {
      const aid = getAgentId(ctx);
      const sourceBefore = configManager.getActiveSource(aid);

      pollers.get(aid)?.stop();
      pollers.delete(aid);
      const client = odooClients.get(aid);
      if (client) {
        try { await client.destroy(); } catch { /* ignore */ }
        odooClients.delete(aid);
      }

      const hadOwn = configManager.clearOwnConfig(aid);
      let sharedCleared = false;
      if (p?.force_shared) {
        sharedCleared = configManager.clearSharedConfig();
      }

      let message: string;
      if (sharedCleared) {
        message = '⚠️ 已断开当前会话，并清除了组织【共享凭据】。所有渠道的 @ 机器人成员都需要重新连接。';
      } else if (hadOwn) {
        message = '已断开当前会话的【专属凭据】。组织共享凭据未受影响 —— 下一次 @ 机器人会自动 fallback 到共享凭据。';
      } else if (sourceBefore === 'shared' || sourceBefore === 'legacy') {
        message = '当前会话已从内存断开，但用的是组织【共享凭据】，已为你保留 —— 不影响其他成员。下一次 @ 机器人会自动重连。如需彻底清除共享凭据，调用 odoo_disconnect(force_shared=true)。';
      } else {
        message = '当前会话已断开。';
      }
      return { success: true, sharedCleared, hadOwnConfig: hadOwn, message };
    },
  });

  api.registerTool({
    name: 'odoo_whoami',
    description: '查看当前 @ 机器人的会话使用的是哪套辉火云凭据 —— 共享凭据 / 当前会话专属 / manifest 静态预填 / 未连接。用于排查"为什么 @ 机器人时没问我密码？"或"我的连接是哪套？"等疑问。',
    schema: { type: 'object', properties: {} },
    async handler(_p: unknown, ctx: Record<string, unknown>) {
      const aid = getAgentId(ctx);
      const client = odooClients.get(aid);
      const connected = client?.isAuthenticated() ?? false;
      const source = configManager.getActiveSource(aid);
      const info = client?.getSessionInfo();
      const fromManifest = (api.pluginConfig as OdooPluginConfig | undefined)?.odoo;

      const sourceLabel: Record<string, string> = {
        agent: '当前会话专属凭据（{agentId}.json）',
        shared: '组织共享凭据（default.json，全员共用）',
        legacy: '历史遗留单文件凭据（odoo-config.json）',
        none: fromManifest ? 'manifest 静态预填（pluginConfig.odoo）' : '未连接（无任何凭据来源）',
      };

      return {
        success: true,
        connected,
        agentId: aid,
        source,
        sourceLabel: sourceLabel[source] ?? '未知',
        url: info?.url ?? null,
        username: info?.username ?? null,
        uid: info?.uid ?? null,
        sharedConfigExists: configManager.hasSharedConfig(),
        ownConfigExists: configManager.hasOwnConfig(aid),
        manifestConfigExists: !!fromManifest,
        message: connected
          ? `当前 @ 机器人会话已连接到 ${info?.url}（用户 ${info?.username}），凭据来源：${sourceLabel[source]}。`
          : `当前会话尚未连接。${configManager.hasSharedConfig() ? '组织已配共享凭据但本会话还没激活，下一次操作会自动连接。' : (fromManifest ? '插件 manifest 已预填凭据，下一次操作会自动连接。' : '需要先调用 odoo_connect 配置凭据（默认会保存为全员共享）。')}`,
      };
    },
  });

  // ══════════════════════════════════════════════════════
  // 任务 / 待办
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_create_task',
    description: '创建待办任务。用于"帮我写个待办"、"创建任务"等指令。',
    schema: {
      type: 'object',
      properties: {
        name:          { type: 'string', description: '任务名称（必填）' },
        description:   { type: 'string', description: '详细描述' },
        date_deadline: { type: 'string', description: '截止日期 YYYY-MM-DD' },
        priority:      { type: 'string', enum: ['0','1','2','3'], description: '优先级：0普通 1中 2高 3紧急' },
        project_id:    { type: 'number', description: '所属项目ID' },
        user_ids:      { type: 'array',  items: { type: 'number' }, description: '指派用户ID列表' },
      },
      required: ['name'],
    },
    async handler(p: { name: string; description?: string; date_deadline?: string; priority?: '0'|'1'|'2'|'3'; project_id?: number; user_ids?: number[] }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const taskId = await client.createTask({ name: p.name, description: p.description, date_deadline: p.date_deadline, priority: p.priority, project_id: p.project_id, user_ids: p.user_ids });
        return { success: true, taskId, message: `待办「${p.name}」已创建，ID: ${taskId}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_list_tasks',
    description: '查看我的待办任务（To-Do 应用，私人任务，无项目）。默认只看进行中。',
    schema: {
      type: 'object',
      properties: {
        limit:          { type: 'number',  description: '上限，默认50' },
        project_id:     { type: 'number',  description: '指定项目ID（指定后切换到项目任务模式）' },
        today_only:     { type: 'boolean', description: '只看今日截止' },
        stage_state:    { type: 'string',  description: "任务状态：in_progress（进行中，默认）/ done（已完成）/ all（全部）" },
        state_filter:   { type: 'string',  description: "直接指定 state 值：01_in_progress / 02_changes_requested / 03_approved / 1_done / 1_canceled / 04_waiting_normal" },
        stage_id:       { type: 'number',  description: '指定具体阶段ID' },
        include_project: { type: 'boolean', description: 'true=同时包含项目任务（默认 false，仅待办私人任务）' },
      },
    },
    async handler(p: { limit?: number; project_id?: number; today_only?: boolean; stage_state?: string; state_filter?: string; stage_id?: number; include_project?: boolean }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const tasks = await client.getMyTasks({ limit: p.limit, project_id: p.project_id, today_only: p.today_only, stage_state: p.stage_state as 'in_progress' | 'done' | 'all', state_filter: p.state_filter, stage_id: p.stage_id, include_project: p.include_project });
        return { success: true, count: tasks.length, tasks: tasks.map(t => ({ id: t['id'], name: t['name'], project: t['project_id'], deadline: t['date_deadline'], priority: t['priority'], stage_id: t['stage_id'], state: t['state'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_get_task_stages',
    description: '查看项目任务阶段列表（stage_id），用于 odoo_update_task 时指定正确的阶段ID。',
    schema: {
      type: 'object',
      properties: {
        project_id: { type: 'number', description: '项目ID（可选，不填则返回所有阶段）' },
      },
    },
    async handler(p: { project_id?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const stages = await client.getTaskStages(p.project_id);
        return { success: true, count: stages.length, stages: stages.map(s => ({ id: s['id'], name: s['name'], fold: s['fold'], is_done_stage: s['fold'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_update_task',
    description: '更新任务的阶段（状态）、截止日期、优先级等字段。通过 stage_id 改变任务的工作流状态。',
    schema: {
      type: 'object',
      properties: {
        task_id:       { type: 'number', description: '任务ID（必填）' },
        name:          { type: 'string', description: '新名称' },
        stage_id:      { type: 'number', description: '新阶段ID（stage_id），用于改变任务状态' },
        date_deadline: { type: 'string', description: '新截止日期 YYYY-MM-DD' },
        priority:      { type: 'string', enum: ['0','1','2','3'], description: '新优先级' },
        description:   { type: 'string', description: '新描述' },
        active:       { type: 'boolean', description: '任务激活状态，false=归档' },
      },
      required: ['task_id'],
    },
    async handler(p: { task_id: number; name?: string; stage_id?: number; date_deadline?: string; priority?: string; description?: string; active?: boolean }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      const values: Record<string, unknown> = {};
      if (p.name !== undefined) values['name'] = p.name;
      if (p.stage_id !== undefined) values['stage_id'] = p.stage_id;
      if (p.date_deadline !== undefined) values['date_deadline'] = p.date_deadline || false;
      if (p.priority !== undefined) values['priority'] = p.priority;
      if (p.description !== undefined) values['description'] = p.description;
      if (p.active !== undefined) values['active'] = p.active;
      if (Object.keys(values).length === 0) {
        return { success: true, message: `任务 #${p.task_id} 无需更新（未提供任何字段）` };
      }
      try {
        await loggedWrite(client, ctx, {
          tool: 'odoo_update_task',
          model: 'project.task',
          ids: [p.task_id],
          values,
          summary: `更新任务 #${p.task_id}（字段：${Object.keys(values).join(', ')}）`,
        });
        return { success: true, message: `任务 #${p.task_id} 已更新（可用 odoo_undo_last 撤销）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 活动 / 日历
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_create_activity',
    description: '创建活动提醒（关联到某条记录）。用于"提醒我明天开会"等。',
    schema: {
      type: 'object',
      properties: {
        res_model:        { type: 'string', description: '关联模型，如 project.task、crm.lead、res.partner' },
        res_id:           { type: 'number', description: '关联记录ID' },
        activity_type_id: { type: 'number', description: '活动类型ID（4=待办，1=邮件，2=电话，通过 odoo_activity_types 查询）' },
        summary:          { type: 'string', description: '活动摘要/标题' },
        note:             { type: 'string', description: '详细说明' },
        date_deadline:    { type: 'string', description: '截止日期 YYYY-MM-DD' },
        user_id:          { type: 'number', description: '负责人ID，默认当前用户' },
      },
      required: ['res_model', 'res_id', 'activity_type_id', 'date_deadline'],
    },
    async handler(p: { res_model: string; res_id: number; activity_type_id: number; summary?: string; note?: string; date_deadline: string; user_id?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.createActivity(p);
        return { success: true, activityId: id, message: `活动「${p.summary ?? ''}」已创建` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_list_activities',
    description: '查看今日及逾期活动提醒。用于"我今天有什么活动"等。',
    schema: { type: 'object', properties: { limit: { type: 'number', description: '上限，默认30' } } },
    async handler(p: { limit?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const acts = await client.getTodayActivities({ limit: p.limit ?? 30 });
        return { success: true, count: acts.length, activities: acts.map(a => ({ id: a['id'], summary: a['summary'], deadline: a['date_deadline'], type: a['activity_type_id'], model: a['res_model'], state: a['state'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_activity_types',
    description: '查询辉火云企业套件可用的活动类型列表（获取 activity_type_id）',
    schema: { type: 'object', properties: {} },
    async handler(_p: unknown, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const types = await client.getActivityTypes();
        return { success: true, types: types.map(t => ({ id: t['id'], name: t['name'], icon: t['icon'], category: t['category'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_create_event',
    description: '创建日历事件/会议。用于"安排一个会议"、"明天上午10点开产品评审"等。',
    schema: {
      type: 'object',
      properties: {
        name:        { type: 'string',                           description: '事件名称（必填）' },
        start:       { type: 'string',                           description: '开始时间 YYYY-MM-DD HH:MM:SS（必填）' },
        stop:        { type: 'string',                           description: '结束时间 YYYY-MM-DD HH:MM:SS（必填）' },
        description: { type: 'string',                           description: '描述/议程' },
        partner_ids: { type: 'array', items: { type: 'number' }, description: '参与人 partner ID 列表' },
      },
      required: ['name', 'start', 'stop'],
    },
    async handler(p: { name: string; start: string; stop: string; description?: string; partner_ids?: number[] }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.createCalendarEvent(p);
        return { success: true, eventId: id, message: `日历事件「${p.name}」已创建，ID: ${id}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 消息
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_get_messages',
    description: '查看未读消息和邮件通知。用于"查看我的消息"、"看看邮件"等。',
    schema: {
      type: 'object',
      properties: {
        type:        { type: 'string', enum: ['message','email'], description: 'message=chatter消息，email=邮件通知' },
        limit:       { type: 'number', description: '上限，默认20' },
        unread_only: { type: 'boolean', description: '只看未读，默认true' },
      },
    },
    async handler(p: { type?: 'message'|'email'; limit?: number; unread_only?: boolean }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      const limit = p.limit ?? 20;
      try {
        if (p.type === 'email') {
          const n = await client.getInboxNotifications({ limit });
          return { success: true, type: 'email', count: n.length, messages: n };
        }
        const msgs = p.unread_only !== false
          ? await client.getUnreadMessages({ limit })
          : (await client.searchRead('mail.message', [['message_type','!=','notification']], ['id','subject','body','author_id','date','model','res_id'], { limit })).records;
        return { success: true, type: 'message', count: msgs.length, messages: msgs.map(m => ({ id: m['id'], subject: m['subject'], body: stripHtml(String(m['body'] ?? '')), author: m['author_id'], date: m['date'], model: m['model'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_send_message',
    description: '向某条 辉火云记录发送 chatter 消息。',
    schema: {
      type: 'object',
      properties: {
        model:   { type: 'string', description: '目标模型，如 project.task、crm.lead、sale.order' },
        res_id:  { type: 'number', description: '目标记录ID' },
        body:    { type: 'string', description: '消息内容（支持HTML）' },
        subject: { type: 'string', description: '主题（可选）' },
      },
      required: ['model', 'res_id', 'body'],
    },
    async handler(p: { model: string; res_id: number; body: string; subject?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.call('mail.message', 'create', [{ model: p.model, res_id: p.res_id, body: p.body, subject: p.subject ?? '', message_type: 'comment', subtype_xmlid: 'mail.mt_comment' }]);
        return { success: true, messageId: id, message: `消息已发送，ID: ${id}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 通用搜索
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_search',
    description: '通用搜索辉火云企业套件任意数据模型。用于"查客户"、"查销售订单"、"查库存"等。',
    schema: {
      type: 'object',
      properties: {
        model:  { type: 'string', description: '模型名：res.partner / project.task / crm.lead / sale.order / purchase.order / stock.quant / hr.employee / account.move 等' },
        domain: { type: 'array',  description: '搜索域 [[field, op, value], ...]' },
        fields: { type: 'array',  items: { type: 'string' }, description: '返回字段' },
        limit:  { type: 'number', description: '上限，默认20' },
        order:  { type: 'string', description: '排序，如 "create_date desc"' },
      },
      required: ['model'],
    },
    async handler(p: { model: string; domain?: unknown[]; fields?: string[]; limit?: number; order?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const r = await client.searchRead(p.model, (p.domain as [string,string,unknown][]) ?? [], p.fields ?? ['id','name'], { limit: p.limit ?? 20, order: p.order });
        return { success: true, count: r.length, records: r.records };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // CRM 商机
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_crm_pipeline',
    description: '查看 CRM 商机管道。用于"查看我的商机"、"销售管道情况"等。',
    schema: {
      type: 'object',
      properties: {
        limit:     { type: 'number',  description: '上限，默认30' },
        stage_id:  { type: 'number',  description: '按阶段ID筛选' },
        user_id:   { type: 'number',  description: '按销售员筛选' },
        type:      { type: 'string',  enum: ['lead','opportunity'], description: '线索或商机' },
        all_users: { type: 'boolean', description: '查看全部用户商机（不只是自己）' },
      },
    },
    async handler(p: { limit?: number; stage_id?: number; user_id?: number; type?: 'lead'|'opportunity'; all_users?: boolean }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      const uid = client.getUid() ?? 0;
      try {
        const leads = await client.getCrmPipeline({ limit: p.limit, stage_id: p.stage_id, user_id: p.all_users ? undefined : (p.user_id ?? uid), type: p.type });
        return { success: true, count: leads.length, pipeline: leads.map(l => ({ id: l['id'], name: l['name'], partner: l['partner_id'], stage: l['stage_id'], probability: l['probability'], revenue: l['expected_revenue'], deadline: l['date_deadline'], type: l['type'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_crm_create',
    description: '创建 CRM 商机或线索。用于"新建一个商机"等。',
    schema: {
      type: 'object',
      properties: {
        name:             { type: 'string', description: '商机名称（必填）' },
        type:             { type: 'string', enum: ['lead','opportunity'], description: '类型，默认 opportunity' },
        partner_id:       { type: 'number', description: '客户ID' },
        expected_revenue: { type: 'number', description: '预计收入' },
        probability:      { type: 'number', description: '赢单概率 0-100' },
        stage_id:         { type: 'number', description: '阶段ID' },
        date_deadline:    { type: 'string', description: '预计关单日期 YYYY-MM-DD' },
        description:      { type: 'string', description: '备注' },
      },
      required: ['name'],
    },
    async handler(p: { name: string; type?: 'lead'|'opportunity'; partner_id?: number; expected_revenue?: number; probability?: number; stage_id?: number; date_deadline?: string; description?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.createCrmLead(p);
        return { success: true, leadId: id, message: `${p.type === 'lead' ? '线索' : '商机'}「${p.name}」已创建，ID: ${id}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_crm_update',
    description: '更新商机信息（阶段、金额、概率、截止日期等）。',
    schema: {
      type: 'object',
      properties: {
        lead_id:          { type: 'number', description: '商机ID（必填）' },
        name:             { type: 'string', description: '新名称' },
        stage_id:         { type: 'number', description: '新阶段ID' },
        expected_revenue: { type: 'number', description: '新预计收入' },
        probability:      { type: 'number', description: '新赢单概率 0-100' },
        date_deadline:    { type: 'string', description: '新截止日期 YYYY-MM-DD' },
        user_id:          { type: 'number', description: '新负责销售员ID' },
      },
      required: ['lead_id'],
    },
    async handler(p: { lead_id: number; name?: string; stage_id?: number; expected_revenue?: number; probability?: number; date_deadline?: string; user_id?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      const values: Record<string, unknown> = {};
      if (p.name !== undefined) values['name'] = p.name;
      if (p.stage_id !== undefined) values['stage_id'] = p.stage_id;
      if (p.expected_revenue !== undefined) values['expected_revenue'] = p.expected_revenue;
      if (p.probability !== undefined) values['probability'] = p.probability;
      if (p.date_deadline !== undefined) values['date_deadline'] = p.date_deadline;
      if (p.user_id !== undefined) values['user_id'] = p.user_id;
      if (Object.keys(values).length === 0) {
        return { success: true, message: `商机 #${p.lead_id} 无需更新（未提供任何字段）` };
      }
      try {
        await loggedWrite(client, ctx, {
          tool: 'odoo_crm_update',
          model: 'crm.lead',
          ids: [p.lead_id],
          values,
          summary: `更新商机 #${p.lead_id}（字段：${Object.keys(values).join(', ')}）`,
        });
        return { success: true, message: `商机 #${p.lead_id} 已更新（可用 odoo_undo_last 撤销）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_crm_won',
    description: '将商机标记为赢单。用于"这个商机赢了"等。',
    schema: { type: 'object', properties: { lead_id: { type: 'number', description: '商机ID（必填）' } }, required: ['lead_id'] },
    async handler(p: { lead_id: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await client.setCrmWon([p.lead_id]);
        return { success: true, message: `商机 #${p.lead_id} 已标记为赢单` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_crm_lost',
    description: '将商机标记为输单/丢失。',
    schema: {
      type: 'object',
      properties: {
        lead_id:        { type: 'number', description: '商机ID（必填）' },
        lost_reason_id: { type: 'number', description: '丢单原因ID（可选）' },
      },
      required: ['lead_id'],
    },
    async handler(p: { lead_id: number; lost_reason_id?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await client.setCrmLost([p.lead_id], p.lost_reason_id);
        return { success: true, message: `商机 #${p.lead_id} 已标记为丢单` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 项目概览 & 工时
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_project_overview',
    description: '查看项目列表和里程碑进度。用于"项目情况"、"里程碑进度"等。',
    schema: {
      type: 'object',
      properties: {
        project_id:      { type: 'number',  description: '指定某个项目ID，不填则查全部' },
        show_milestones: { type: 'boolean', description: '是否同时返回里程碑，默认true' },
      },
    },
    async handler(p: { project_id?: number; show_milestones?: boolean }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const [projects, milestones] = await Promise.all([
          client.getProjectOverview(p.project_id),
          p.show_milestones !== false ? client.getMilestones(p.project_id) : Promise.resolve([]),
        ]);
        return {
          success: true,
          projects: projects.map(pr => ({ id: pr['id'], name: pr['name'], partner: pr['partner_id'], manager: pr['user_id'], start: pr['date_start'], end: pr['date'], task_count: pr['task_count'], open_tasks: pr['open_task_count'], done_tasks: pr['closed_task_count'] })),
          milestones: milestones.map(m => ({ id: m['id'], name: m['name'], project: m['project_id'], deadline: m['deadline'], is_reached: m['is_reached'], tasks: m['task_count'], done_tasks: m['done_task_count'], overdue: m['is_deadline_exceeded'] })),
        };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_timesheet_log',
    description: '记录工时。用于"记录2小时工时"、"今天在项目A上工作了3小时"等。',
    schema: {
      type: 'object',
      properties: {
        name:       { type: 'string', description: '工作描述（必填）' },
        hours:      { type: 'number', description: '工时（小时）（必填）' },
        project_id: { type: 'number', description: '项目ID' },
        task_id:    { type: 'number', description: '任务ID' },
        date:       { type: 'string', description: '日期 YYYY-MM-DD，默认今天' },
      },
      required: ['name', 'hours'],
    },
    async handler(p: { name: string; hours: number; project_id?: number; task_id?: number; date?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.logTimesheet({ name: p.name, unit_amount: p.hours, project_id: p.project_id, task_id: p.task_id, date: p.date });
        return { success: true, timesheetId: id, message: `已记录 ${p.hours} 小时工时：「${p.name}」` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 销售 & 采购
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_sale_orders',
    description: '查看销售订单/报价单列表。用于"查看销售订单"、"报价单情况"等。',
    schema: {
      type: 'object',
      properties: {
        limit:      { type: 'number', description: '上限，默认20' },
        state:      { type: 'string', enum: ['draft','sent','sale','cancel'], description: '状态：draft=报价 sent=已发送 sale=销售订单 cancel=已取消' },
        partner_id: { type: 'number', description: '按客户筛选' },
      },
    },
    async handler(p: { limit?: number; state?: string; partner_id?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const orders = await client.getSaleOrders({ limit: p.limit, state: p.state, partner_id: p.partner_id });
        return { success: true, count: orders.length, orders: orders.map(o => ({ id: o['id'], name: o['name'], partner: o['partner_id'], state: o['state'], date: o['date_order'], amount: o['amount_total'], invoice_status: o['invoice_status'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_purchase_orders',
    description: '查看采购订单/询价单列表。用于"查看采购订单"等。',
    schema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: '上限，默认20' },
        state: { type: 'string', enum: ['draft','sent','to approve','purchase','cancel'], description: '状态：draft=RFQ sent=已发送 to approve=待审批 purchase=采购订单 cancel=已取消' },
      },
    },
    async handler(p: { limit?: number; state?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const orders = await client.getPurchaseOrders({ limit: p.limit, state: p.state });
        return { success: true, count: orders.length, orders: orders.map(o => ({ id: o['id'], name: o['name'], vendor: o['partner_id'], state: o['state'], date: o['date_order'], planned_arrival: o['date_planned'], amount: o['amount_total'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 客服工单（Helpdesk）
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_tickets',
    description: '查看客服工单列表。用于"查看工单"、"有哪些待处理问题"等。',
    schema: {
      type: 'object',
      properties: {
        limit:      { type: 'number',  description: '上限，默认30' },
        my_tickets: { type: 'boolean', description: '只看指派给我的工单，默认true' },
        priority:   { type: 'string',  enum: ['0','1','2','3'], description: '优先级筛选' },
        partner_id: { type: 'number',  description: '按客户筛选' },
        team_id:    { type: 'number',  description: '按团队筛选' },
      },
    },
    async handler(p: { limit?: number; my_tickets?: boolean; priority?: string; partner_id?: number; team_id?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      const uid = client.getUid() ?? undefined;
      try {
        const tickets = await client.getHelpdeskTickets({ limit: p.limit, user_id: p.my_tickets !== false ? uid : undefined, priority: p.priority, partner_id: p.partner_id, team_id: p.team_id });
        return { success: true, count: tickets.length, tickets: tickets.map(t => ({ id: t['id'], ref: t['ticket_ref'], name: t['name'], team: t['team_id'], stage: t['stage_id'], priority: t['priority'], partner: t['partner_id'], sla_deadline: t['sla_deadline'], sla_fail: t['sla_fail'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_ticket_create',
    description: '创建客服工单。用于"帮我提交一个问题"、"新建工单"等。',
    schema: {
      type: 'object',
      properties: {
        name:        { type: 'string', description: '工单标题（必填）' },
        description: { type: 'string', description: '问题描述' },
        partner_id:  { type: 'number', description: '客户ID' },
        team_id:     { type: 'number', description: '处理团队ID' },
        priority:    { type: 'string', enum: ['0','1','2','3'], description: '优先级：0普通 1中 2高 3紧急' },
        user_id:     { type: 'number', description: '指派人员ID' },
      },
      required: ['name'],
    },
    async handler(p: { name: string; description?: string; partner_id?: number; team_id?: number; priority?: '0'|'1'|'2'|'3'; user_id?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.createHelpdeskTicket(p);
        return { success: true, ticketId: id, message: `工单「${p.name}」已创建，ID: ${id}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 财务 / 发票
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_invoices',
    description: '查看发票/账单列表，支持查逾期应收。用于"查看发票"、"逾期未付款的"等。',
    schema: {
      type: 'object',
      properties: {
        limit:         { type: 'number',  description: '上限，默认20' },
        move_type:     { type: 'string',  enum: ['out_invoice','in_invoice','out_refund','in_refund'], description: '类型：out_invoice=客户发票 in_invoice=供应商账单' },
        payment_state: { type: 'string',  enum: ['not_paid','partial','paid','in_payment'], description: '付款状态' },
        overdue_only:  { type: 'boolean', description: '只看逾期未付发票' },
        partner_id:    { type: 'number',  description: '按客户/供应商筛选' },
      },
    },
    async handler(p: { limit?: number; move_type?: string; payment_state?: string; overdue_only?: boolean; partner_id?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const invoices = p.overdue_only
          ? await client.getOverdueInvoices()
          : await client.getInvoices({ limit: p.limit, move_type: p.move_type, payment_state: p.payment_state, partner_id: p.partner_id });
        return { success: true, count: invoices.length, invoices: invoices.map(i => ({ id: i['id'], name: i['name'], type: i['move_type'], partner: i['partner_id'], date: i['invoice_date'], due_date: i['invoice_date_due'], amount: i['amount_total'], payment_state: i['payment_state'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 联系人 / 客户（v1.2 新增）
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_contacts',
    description: '查询联系人/客户/供应商。用于"查客户"、"找供应商"、"搜索联系人"等。',
    schema: {
      type: 'object',
      properties: {
        keyword:       { type: 'string',  description: '按名称模糊搜索' },
        is_company:    { type: 'boolean', description: 'true=只看公司 false=只看个人' },
        customer_only: { type: 'boolean', description: '只看客户' },
        supplier_only: { type: 'boolean', description: '只看供应商' },
        limit:         { type: 'number',  description: '上限，默认30' },
      },
    },
    async handler(p: { keyword?: string; is_company?: boolean; customer_only?: boolean; supplier_only?: boolean; limit?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const contacts = await client.getPartners({ keyword: p.keyword, is_company: p.is_company, customer_rank: p.customer_only, supplier_rank: p.supplier_only, limit: p.limit });
        return { success: true, count: contacts.length, contacts: contacts.map(c => ({ id: c['id'], name: c['name'], email: c['email'], phone: c['phone'], mobile: c['mobile'], is_company: c['is_company'], city: c['city'], country: c['country_id'], parent: c['parent_id'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_contact_create',
    description: '创建联系人/客户/供应商。用于"添加新客户"、"创建联系人"等。',
    schema: {
      type: 'object',
      properties: {
        name:       { type: 'string',  description: '名称（必填）' },
        email:      { type: 'string',  description: '邮箱' },
        phone:      { type: 'string',  description: '电话' },
        mobile:     { type: 'string',  description: '手机' },
        is_company: { type: 'boolean', description: '是否公司，默认false' },
        city:       { type: 'string',  description: '城市' },
        street:     { type: 'string',  description: '街道/地址' },
        parent_id:  { type: 'number',  description: '所属公司ID（个人联系人时）' },
        is_customer:{ type: 'boolean', description: '标记为客户，默认true' },
        is_supplier:{ type: 'boolean', description: '标记为供应商，默认false' },
      },
      required: ['name'],
    },
    async handler(p: { name: string; email?: string; phone?: string; mobile?: string; is_company?: boolean; city?: string; street?: string; parent_id?: number; is_customer?: boolean; is_supplier?: boolean }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.createPartner({
          name: p.name, email: p.email, phone: p.phone, mobile: p.mobile,
          is_company: p.is_company, city: p.city, street: p.street, parent_id: p.parent_id,
          customer_rank: (p.is_customer !== false) ? 1 : 0,
          supplier_rank: p.is_supplier ? 1 : 0,
        });
        return { success: true, contactId: id, message: `${p.is_company ? '公司' : '联系人'}「${p.name}」已创建，ID: ${id}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 库存（v1.2 新增）
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_stock_levels',
    description: '查看库存水平。用于"查库存"、"产品XX还有多少"等。',
    schema: {
      type: 'object',
      properties: {
        keyword:     { type: 'string', description: '按产品名称模糊搜索' },
        product_id:  { type: 'number', description: '按产品ID筛选' },
        location_id: { type: 'number', description: '按库位筛选' },
        limit:       { type: 'number', description: '上限，默认50' },
      },
    },
    async handler(p: { keyword?: string; product_id?: number; location_id?: number; limit?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const stocks = await client.getStockLevels({ keyword: p.keyword, product_id: p.product_id, location_id: p.location_id, limit: p.limit });
        return { success: true, count: stocks.length, stock: stocks.map(s => ({ id: s['id'], product: s['product_id'], location: s['location_id'], lot: s['lot_id'], quantity: s['quantity'], reserved: s['reserved_quantity'], available: s['available_quantity'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_stock_pickings',
    description: '查看调拨单/出入库单。用于"查看待出库"、"调拨单情况"等。',
    schema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: '上限，默认20' },
        state: { type: 'string', enum: ['draft','waiting','confirmed','assigned','done','cancel'], description: '状态：assigned=就绪 waiting=等待 done=完成' },
        type:  { type: 'string', enum: ['incoming','outgoing','internal'], description: '类型：incoming=入库 outgoing=出库 internal=内部调拨' },
      },
    },
    async handler(p: { limit?: number; state?: string; type?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const pickings = await client.getStockPickings({ limit: p.limit, state: p.state, picking_type: p.type });
        return { success: true, count: pickings.length, pickings: pickings.map(pk => ({ id: pk['id'], name: pk['name'], partner: pk['partner_id'], type: pk['picking_type_id'], state: pk['state'], scheduled: pk['scheduled_date'], done: pk['date_done'], origin: pk['origin'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // HR 员工 / 考勤 / 请假（v1.2 新增）
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_employees',
    description: '查询员工列表。用于"查员工"、"某部门有谁"等。',
    schema: {
      type: 'object',
      properties: {
        keyword:       { type: 'string', description: '按名称模糊搜索' },
        department_id: { type: 'number', description: '按部门ID筛选' },
        limit:         { type: 'number', description: '上限，默认50' },
      },
    },
    async handler(p: { keyword?: string; department_id?: number; limit?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const emps = await client.getEmployees({ keyword: p.keyword, department_id: p.department_id, limit: p.limit });
        return { success: true, count: emps.length, employees: emps.map(e => ({ id: e['id'], name: e['name'], department: e['department_id'], job: e['job_id'], email: e['work_email'], phone: e['mobile_phone'], manager: e['parent_id'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_leaves',
    description: '查看请假记录。用于"我的请假记录"、"查看某人的请假"等。',
    schema: {
      type: 'object',
      properties: {
        employee_id: { type: 'number', description: '员工ID，不填则查当前用户' },
        state:       { type: 'string', enum: ['draft','confirm','validate1','validate','refuse'], description: '状态筛选' },
        limit:       { type: 'number', description: '上限，默认20' },
      },
    },
    async handler(p: { employee_id?: number; state?: string; limit?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const leaves = await client.getLeaves({ employee_id: p.employee_id, state: p.state, limit: p.limit });
        return { success: true, count: leaves.length, leaves: leaves.map(l => ({ id: l['id'], name: l['name'], employee: l['employee_id'], type: l['holiday_status_id'], from: l['date_from'], to: l['date_to'], days: l['number_of_days'], state: l['state'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_attendances',
    description: '查看考勤打卡记录。用于"我的考勤"、"打卡记录"等。',
    schema: {
      type: 'object',
      properties: {
        employee_id: { type: 'number', description: '员工ID，不填则查当前用户' },
        limit:       { type: 'number', description: '上限，默认20' },
      },
    },
    async handler(p: { employee_id?: number; limit?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const records = await client.getAttendances({ employee_id: p.employee_id, limit: p.limit });
        return { success: true, count: records.length, attendances: records.map(a => ({ id: a['id'], employee: a['employee_id'], check_in: a['check_in'], check_out: a['check_out'], worked_hours: a['worked_hours'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 审批（v1.2 新增）
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_approvals',
    description: '查看审批请求列表。用于"我的审批"、"待审批的"等。',
    schema: {
      type: 'object',
      properties: {
        my_requests: { type: 'boolean', description: '只看我提交的请求' },
        state:       { type: 'string', enum: ['new','pending','approved','refused','cancel'], description: '状态筛选' },
        limit:       { type: 'number', description: '上限，默认20' },
      },
    },
    async handler(p: { my_requests?: boolean; state?: string; limit?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const approvals = await client.getApprovals({ my_requests: p.my_requests, state: p.state, limit: p.limit });
        return { success: true, count: approvals.length, approvals: approvals.map(a => ({ id: a['id'], name: a['name'], category: a['category_id'], owner: a['request_owner_id'], status: a['request_status'], date: a['date'], amount: a['amount'], reason: a['reason'] })) };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 实施经理每日概况
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_daily_briefing',
    description: '实施经理每日工作概况：今日截止任务、到期活动、待处理工单、逾期发票、商机跟进、未读消息。用于"今天有什么工作"、"给我今日概况"等。',
    schema: { type: 'object', properties: {} },
    async handler(_p: unknown, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const briefing = await client.getDailyBriefing();
        const todayStr = today();
        const total = briefing.todayTasks.length + briefing.overdueActivities.length + briefing.openTickets.length;
        return {
          success: true,
          message: `${todayStr} 概况：${total} 项核心待处理`,
          briefing: {
            date: todayStr,
            today_tasks: { count: briefing.todayTasks.length, items: briefing.todayTasks.map(t => ({ id: t['id'], name: t['name'], project: t['project_id'], deadline: t['date_deadline'], priority: t['priority'] })) },
            activities:  { count: briefing.overdueActivities.length, items: briefing.overdueActivities.map(a => ({ id: a['id'], summary: a['summary'], deadline: a['date_deadline'], type: a['activity_type_id'], model: a['res_model'], state: a['state'] })) },
            tickets:     { count: briefing.openTickets.length, items: briefing.openTickets.map(t => ({ id: t['id'], ref: t['ticket_ref'], name: t['name'], priority: t['priority'], sla_fail: t['sla_fail'] })) },
            overdue_invoices: { count: briefing.overdueInvoices.length, items: briefing.overdueInvoices.map(i => ({ id: i['id'], name: i['name'], partner: i['partner_id'], due_date: i['invoice_date_due'], amount: i['amount_total'] })) },
            crm_followups:    { count: briefing.crmFollowUps.length, items: briefing.crmFollowUps.map(l => ({ id: l['id'], name: l['name'], partner: l['partner_id'], stage: l['stage_id'], revenue: l['expected_revenue'] })) },
            unread_messages:  { count: briefing.unreadMessages.length, items: briefing.unreadMessages.map(m => ({ id: m['id'], subject: m['subject'], author: m['author_id'], model: m['model'] })) },
          },
        };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // 通知基座（跨渠道）
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_notification_status',
    description: '查看辉火云企业套件通知总线状态：已注册的渠道 transport、订阅者数、最近一次 poll 时间、当前 agent 的偏好设置、信封溯源缓存大小。用于"通知推送情况"、"企微/钉钉有没有连上"等排查类问题。',
    schema: { type: 'object', properties: {} },
    async handler(_p: unknown, ctx: Record<string, unknown>) {
      const aid = getAgentId(ctx);
      const pollerStatus = pollers.get(aid)?.getStatus() ?? null;
      const prefs = prefsManager.load(aid);
      return {
        success: true,
        agentId: aid,
        bus: {
          subscribers: notificationBus.subscriberCount(),
          replySubscribers: notificationBus.replySubscriberCount(),
          transports: notificationBus.listTransports(),
        },
        poller: pollerStatus,
        prefs,
        cache: { envelopesTracked: envelopeCache.size() },
        hint: notificationBus.subscriberCount() === 0 && notificationBus.listTransports().length === 0
          ? '当前没有任何渠道插件订阅通知总线。请确认已加载企微/钉钉等插件，或检查它们的连接状态。'
          : undefined,
      };
    },
  });

  api.registerTool({
    name: 'odoo_notification_channels',
    description: '列出当前已注册到通知总线的渠道（如企微、钉钉、飞书、webhook）。仅作为信息查询，真正的连接由各渠道插件自己管理。',
    schema: { type: 'object', properties: {} },
    async handler() {
      const transports = notificationBus.listTransports();
      return {
        success: true,
        count: transports.length,
        channels: transports,
        subscribers: notificationBus.subscriberCount(),
      };
    },
  });

  api.registerTool({
    name: 'odoo_notification_test',
    description: '向通知总线发一条测试 envelope，验证企微/钉钉等渠道是否能收到。用于"测试一下通知"、"看看推送通不通"等。',
    schema: {
      type: 'object',
      properties: {
        title:   { type: 'string', description: '测试标题，默认"辉火云企业套件测试通知"' },
        summary: { type: 'string', description: '测试摘要，默认"这是一条由 odoo 插件发送的测试通知"' },
      },
    },
    async handler(p: { title?: string; summary?: string }, ctx: Record<string, unknown>) {
      const aid = getAgentId(ctx);
      const client = odooClients.get(aid);
      const odooUrl = client?.getSessionInfo().url;
      const envelope: NotificationEnvelope = {
        id: `odoo:${aid}:test:${Date.now()}`,
        source: 'odoo',
        agentId: aid,
        kind: 'message',
        action: 'test',
        priority: 'low',
        title: p.title ?? '辉火云企业套件测试通知',
        summary: p.summary ?? '这是一条由 odoo 插件发送的测试通知',
        body: p.summary ?? '如果你在企微 / 钉钉 / 飞书 里看到这条，说明渠道接通正常。',
        tags: ['odoo', 'test'],
        createdAt: Date.now(),
        origin: { url: odooUrl, model: 'test', resId: 0 },
      };
      await notificationBus.publish(envelope);
      return {
        success: true,
        dispatched: true,
        subscribers: notificationBus.subscriberCount(),
        transports: notificationBus.listTransports().map(t => t.name),
        envelopeId: envelope.id,
        message: notificationBus.subscriberCount() === 0
          ? '已发送，但当前总线没有订阅者 —— 渠道插件可能未加载。'
          : `已发送到 ${notificationBus.subscriberCount()} 个订阅者。`,
      };
    },
  });

  api.registerTool({
    name: 'odoo_notification_prefs',
    description: '查看或更新当前用户的通知偏好。支持：启停总开关、只接收某些类型（todo/activity/message/email/calendar）、优先级下限、静音时段（24h 制，跨午夜 OK）。不传任何参数只做查询。urgent 级别永远绕过静音与优先级过滤。',
    schema: {
      type: 'object',
      properties: {
        enabled:      { type: 'boolean', description: '通知总开关，false=完全停掉' },
        kinds:        { type: 'array', items: { type: 'string', enum: ['todo','activity','message','email','calendar'] }, description: '允许发的种类，空数组=全开' },
        min_priority: { type: 'string', enum: ['low','normal','high','urgent'], description: '优先级下限，低于此级别的被丢弃（urgent 永远放行）' },
        quiet_start:  { type: 'string', description: '静音起始 HH:MM（传空字符串 "" 清除静音）' },
        quiet_end:    { type: 'string', description: '静音结束 HH:MM' },
        reset:        { type: 'boolean', description: 'true=重置为默认偏好' },
      },
    },
    async handler(
      p: { enabled?: boolean; kinds?: string[]; min_priority?: string; quiet_start?: string; quiet_end?: string; reset?: boolean },
      ctx: Record<string, unknown>,
    ) {
      const aid = getAgentId(ctx);
      if (p.reset) {
        prefsManager.clear(aid);
        return { success: true, agentId: aid, prefs: DEFAULT_PREFS, message: '偏好已重置为默认。' };
      }

      const current = prefsManager.load(aid);
      const patch: Partial<NotificationPreferences> = {};
      if (p.enabled !== undefined) patch.enabled = p.enabled;
      if (Array.isArray(p.kinds)) patch.kinds = p.kinds as NotificationKind[];
      if (p.min_priority) patch.minPriority = p.min_priority as NotificationPriority;
      if (p.quiet_start === '' || p.quiet_end === '') {
        patch.quietHours = undefined;
      } else if (p.quiet_start && p.quiet_end) {
        patch.quietHours = { start: p.quiet_start, end: p.quiet_end };
      }

      if (Object.keys(patch).length === 0) {
        return { success: true, agentId: aid, prefs: current, message: '当前偏好（未变更）' };
      }
      const updated = prefsManager.patch(patch, aid);
      return { success: true, agentId: aid, prefs: updated, message: '通知偏好已更新' };
    },
  });

  api.registerTool({
    name: 'odoo_notification_reply',
    description: '手动模拟一次从渠道回到辉火云企业套件的入站回复 —— 渠道插件在收到用户回复后应调用这条逻辑（或直接 import notificationBus.reply）。给出 envelope_id + body，辉火云会在对应记录的内部动态里写一条消息。用于排查"企微回复能不能写回系统"。',
    schema: {
      type: 'object',
      properties: {
        envelope_id: { type: 'string', description: '被回复的 envelope id（从 odoo_notification_test 或实际通知里取）' },
        body:        { type: 'string', description: '回复正文（纯文本）' },
        channel:     { type: 'string', description: '渠道标识，默认 "manual"' },
        from_user:   { type: 'string', description: '回复人标识，可选' },
      },
      required: ['envelope_id', 'body'],
    },
    async handler(p: { envelope_id: string; body: string; channel?: string; from_user?: string }) {
      const reply: InboundReply = {
        envelopeId: p.envelope_id,
        channel: p.channel ?? 'manual',
        fromUser: p.from_user,
        body: p.body,
      };
      const result = await notificationBus.reply(reply);
      return { success: result.ok, handled: result.handled, errors: result.errors, message: result.ok ? `回复已分发给 ${result.handled} 个处理器。` : '回复未能成功投递，请检查辉火云企业套件是否连接、envelope_id 是否在缓存中（24h 内、500 条上限）。' };
    },
  });

  // ══════════════════════════════════════════════════════
  // 知识库（knowledge.article）
  // ══════════════════════════════════════════════════════

  api.registerTool({
    name: 'odoo_knowledge_search',
    description: '搜索 辉火云知识库文章。支持关键词（匹配标题或正文）、分类（workspace/private/shared）、仅收藏、仅顶层、指定父文章。用于"找一下关于 X 的知识库文章"、"列出我收藏的"、"列出工作区顶层文章"。',
    schema: {
      type: 'object',
      properties: {
        keyword:         { type: 'string', description: '关键词，匹配文章标题或正文' },
        category:        { type: 'string', enum: ['workspace','private','shared'], description: '分类：workspace=工作区/private=私有/shared=共享' },
        only_favorite:   { type: 'boolean', description: '只列我收藏的' },
        only_roots:      { type: 'boolean', description: '只列顶层文章（parent_id=空）' },
        parent_id:       { type: 'number', description: '指定父文章 id，列其直接子节点' },
        include_trashed: { type: 'boolean', description: '包含回收站中的文章，默认 false' },
        limit:           { type: 'number', description: '上限，默认 30' },
      },
    },
    async handler(
      p: { keyword?: string; category?: 'workspace'|'private'|'shared'; only_favorite?: boolean; only_roots?: boolean; parent_id?: number; include_trashed?: boolean; limit?: number },
      ctx: Record<string, unknown>,
    ) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const recs = await client.searchKnowledgeArticles(p);
        return {
          success: true,
          count: recs.length,
          articles: recs.map(r => ({
            id: r['id'],
            name: r['name'],
            icon: r['icon'] || null,
            category: r['category'],
            parent: r['parent_id'],
            root: r['root_article_id'],
            has_children: r['has_article_children'],
            is_favorite: r['is_user_favorite'],
            favorite_count: r['favorite_count'],
            last_edition: r['last_edition_date'],
          })),
        };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_knowledge_read',
    description: '读取单篇知识库文章的完整正文（HTML）。用于"把这篇文章读给我"、"X 文章里写了什么"。body 可能较长，渲染时建议截断。',
    schema: {
      type: 'object',
      properties: {
        id:        { type: 'number', description: '文章 id（必填）' },
        plain:     { type: 'boolean', description: 'true=同时返回纯文本摘要（去 HTML）' },
        max_chars: { type: 'number', description: '正文最大字符数，0=不截断，默认 5000' },
      },
      required: ['id'],
    },
    async handler(p: { id: number; plain?: boolean; max_chars?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const rec = await client.readKnowledgeArticle(p.id);
        if (!rec) return { success: false, message: `文章 #${p.id} 不存在` };
        const maxChars = p.max_chars ?? 5000;
        const body = String(rec['body'] ?? '');
        const bodyOut = maxChars > 0 && body.length > maxChars ? body.substring(0, maxChars) + '…' : body;
        const result: Record<string, unknown> = {
          success: true,
          article: {
            id: rec['id'],
            name: rec['name'],
            icon: rec['icon'] || null,
            category: rec['category'],
            parent: rec['parent_id'],
            is_favorite: rec['is_user_favorite'],
            favorite_count: rec['favorite_count'],
            is_locked: rec['is_locked'],
            is_trashed: rec['to_delete'],
            last_edition: rec['last_edition_date'],
            internal_permission: rec['internal_permission'],
            body: bodyOut,
            body_truncated: bodyOut !== body,
          },
        };
        if (p.plain) {
          (result['article'] as Record<string, unknown>)['plain'] = stripHtml(body);
        }
        return result;
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_knowledge_create',
    description: '创建知识库文章。顶层文章必须指定 category（workspace=工作区/private=私有）。子文章传 parent_id，权限继承。body 支持 markdown（自动转 HTML）或直接传 HTML。',
    schema: {
      type: 'object',
      properties: {
        name:      { type: 'string', description: '文章标题' },
        body:      { type: 'string', description: '正文（markdown 或 HTML 皆可，检测到 HTML 标签时原样使用）' },
        icon:      { type: 'string', description: '图标 emoji' },
        parent_id: { type: 'number', description: '父文章 id（创建子文章时必传）' },
        category:  { type: 'string', enum: ['workspace','private','shared'], description: '顶层文章的分类，默认 private' },
      },
    },
    async handler(
      p: { name?: string; body?: string; icon?: string; parent_id?: number; category?: 'workspace'|'private'|'shared' },
      ctx: Record<string, unknown>,
    ) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const htmlBody = p.body ? mdToHtml(p.body) : '';
        const id = await client.createKnowledgeArticle({
          name: p.name,
          body: htmlBody,
          icon: p.icon,
          parent_id: p.parent_id,
          category: p.category,
        });
        return { success: true, articleId: id, message: `已创建文章 #${id}${p.name ? `「${p.name}」` : ''}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_knowledge_update',
    description: '更新知识库文章的标题、图标或正文。body 支持 markdown，传 HTML 时原样保留。想追加内容请用 odoo_knowledge_append。',
    schema: {
      type: 'object',
      properties: {
        id:   { type: 'number', description: '文章 id（必填）' },
        name: { type: 'string', description: '新标题' },
        body: { type: 'string', description: '新正文（markdown/HTML），覆盖旧内容' },
        icon: { type: 'string', description: '新图标 emoji，传空字符串清除' },
      },
      required: ['id'],
    },
    async handler(p: { id: number; name?: string; body?: string; icon?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await client.updateKnowledgeArticle(p.id, {
          name: p.name,
          body: p.body !== undefined ? mdToHtml(p.body) : undefined,
          icon: p.icon,
        });
        return { success: true, message: `文章 #${p.id} 已更新` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_knowledge_append',
    description: '在现有文章末尾追加一段内容（markdown 或 HTML）。适合"把刚才讨论的结论写进 X 文章"这种追加笔记的场景，不会覆盖原有内容。',
    schema: {
      type: 'object',
      properties: {
        id:      { type: 'number', description: '文章 id（必填）' },
        content: { type: 'string', description: '要追加的内容（markdown 或 HTML）' },
        with_divider: { type: 'boolean', description: '是否在追加前插入分隔线 <hr>，默认 false' },
      },
      required: ['id', 'content'],
    },
    async handler(p: { id: number; content: string; with_divider?: boolean }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const html = (p.with_divider ? '<hr>' : '') + mdToHtml(p.content);
        await client.appendKnowledgeArticle(p.id, html);
        return { success: true, message: `已向文章 #${p.id} 追加 ${p.content.length} 字符` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_knowledge_tree',
    description: '展示知识库树结构（以 workspace/private 为根，递归最多 N 层）。用于"给我看下知识库长啥样"、"工作区里都有哪些文章"。',
    schema: {
      type: 'object',
      properties: {
        category:  { type: 'string', enum: ['workspace','private','shared'], description: '根分类，默认 workspace' },
        max_depth: { type: 'number', description: '最大深度，默认 3' },
        max_nodes: { type: 'number', description: '整棵树节点数上限，防爆炸，默认 150' },
      },
    },
    async handler(p: { category?: 'workspace'|'private'|'shared'; max_depth?: number; max_nodes?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      const maxDepth = p.max_depth ?? 3;
      const maxNodes = p.max_nodes ?? 150;
      const category = p.category ?? 'workspace';
      try {
        type Node = { id: number; name: string; icon: string | null; is_favorite: boolean; children: Node[] };
        let visited = 0;
        const walk = async (parentId: number | false, depth: number): Promise<Node[]> => {
          if (depth > maxDepth || visited >= maxNodes) return [];
          const items = await client.searchKnowledgeArticles(parentId === false
            ? { category, only_roots: true, limit: 30 }
            : { parent_id: parentId as number, limit: 30 });
          const nodes: Node[] = [];
          for (const it of items) {
            if (visited >= maxNodes) break;
            visited += 1;
            nodes.push({
              id: it['id'] as number,
              name: String(it['name'] ?? ''),
              icon: (it['icon'] as string) || null,
              is_favorite: Boolean(it['is_user_favorite']),
              children: (it['has_article_children'] && depth < maxDepth)
                ? await walk(it['id'] as number, depth + 1)
                : [],
            });
          }
          return nodes;
        };
        const tree = await walk(false, 0);
        return { success: true, category, max_depth: maxDepth, nodes_visited: visited, tree };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_knowledge_favorite',
    description: '切换知识库文章的收藏状态（已收藏→取消，未收藏→收藏）。用于"收藏这篇"、"取消收藏 X"。',
    schema: {
      type: 'object',
      properties: {
        id: { type: 'number', description: '文章 id（必填）' },
      },
      required: ['id'],
    },
    async handler(p: { id: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await client.toggleKnowledgeFavorite(p.id);
        // 回读当前状态返回给用户
        const rec = await client.readKnowledgeArticle(p.id);
        return { success: true, articleId: p.id, is_favorite: rec?.['is_user_favorite'] ?? null, message: `文章 #${p.id} 收藏状态已切换` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_knowledge_trash',
    description: '把文章送入回收站（或还原）。默认删除，restore=true 时恢复。辉火云回收站里的文章在 knowledge_article_trash_limit_days（默认 30 天）后才真正删除，所以是安全操作。',
    schema: {
      type: 'object',
      properties: {
        id:      { type: 'number',  description: '文章 id（必填）' },
        restore: { type: 'boolean', description: 'true=从回收站恢复；默认 false（送入回收站）' },
      },
      required: ['id'],
    },
    async handler(p: { id: number; restore?: boolean }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        if (p.restore) {
          await client.restoreKnowledgeArticle(p.id);
          return { success: true, message: `文章 #${p.id} 已从回收站恢复` };
        } else {
          await client.trashKnowledgeArticle(p.id);
          return { success: true, message: `文章 #${p.id} 已送入回收站（30 天后物理删除）` };
        }
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ══════════════════════════════════════════════════════
  // v1.7 — Daily Inbox 闭环（活动/关注者/日历/邮件/附件/批量/撤销）
  // ══════════════════════════════════════════════════════

  // ── 活动闭环 ──────────────────────────────────────────
  api.registerTool({
    name: 'odoo_complete_activity',
    description: '完成一条活动（闭环）。底层调用 mail.activity.action_feedback：活动从列表移除、反馈写入源记录内部动态。用于"那个催付款的活动做完了"、"把提醒 #X 标记完成，附言：客户已转账"。',
    schema: {
      type: 'object',
      properties: {
        activity_id: { type: 'number', description: '活动 id（必填，可通过 odoo_list_activities 查询）' },
        feedback:    { type: 'string', description: '完成反馈（可选，会写入源记录 chatter）' },
      },
      required: ['activity_id'],
    },
    async handler(p: { activity_id: number; feedback?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await client.completeActivity(p.activity_id, p.feedback);
        return { success: true, message: `活动 #${p.activity_id} 已完成` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_reschedule_activity',
    description: '把活动改到新日期。用于"那个提醒挪到明天"、"推迟到下周一"。需要先有活动 id。',
    schema: {
      type: 'object',
      properties: {
        activity_id:   { type: 'number', description: '活动 id（必填）' },
        date_deadline: { type: 'string', description: '新截止日期 YYYY-MM-DD（必填）' },
      },
      required: ['activity_id', 'date_deadline'],
    },
    async handler(p: { activity_id: number; date_deadline: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await loggedWrite(client, ctx, {
          tool: 'odoo_reschedule_activity',
          model: 'mail.activity',
          ids: [p.activity_id],
          values: { date_deadline: p.date_deadline },
          summary: `活动 #${p.activity_id} 改期到 ${p.date_deadline}`,
        });
        return { success: true, message: `活动 #${p.activity_id} 已改到 ${p.date_deadline}（可用 odoo_undo_last 撤销）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 关注者 ────────────────────────────────────────────
  api.registerTool({
    name: 'odoo_follow',
    description: '关注某条记录（继承 mail.thread 的任何模型：project.task / crm.lead / helpdesk.ticket / sale.order / res.partner 等）。关注后该记录的新消息、活动会出现在 Inbox。不传 partner_ids 时默认关注我自己。',
    schema: {
      type: 'object',
      properties: {
        model:       { type: 'string', description: '数据模型名，如 "project.task"、"crm.lead"（必填）' },
        res_id:      { type: 'number', description: '记录 id（必填）' },
        partner_ids: { type: 'array', items: { type: 'number' }, description: '联系人 id 列表（可选，默认=当前用户的 partner_id）' },
      },
      required: ['model', 'res_id'],
    },
    async handler(p: { model: string; res_id: number; partner_ids?: number[] }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await client.followRecord(p.model, p.res_id, p.partner_ids);
        return { success: true, message: `已关注 ${p.model} #${p.res_id}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_unfollow',
    description: '取消关注某条记录。partner_ids 可选，默认取消我自己。',
    schema: {
      type: 'object',
      properties: {
        model:       { type: 'string', description: '数据模型名（必填）' },
        res_id:      { type: 'number', description: '记录 id（必填）' },
        partner_ids: { type: 'array', items: { type: 'number' }, description: '联系人 id 列表（可选，默认=当前用户的 partner_id）' },
      },
      required: ['model', 'res_id'],
    },
    async handler(p: { model: string; res_id: number; partner_ids?: number[] }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await client.unfollowRecord(p.model, p.res_id, p.partner_ids);
        return { success: true, message: `已取消关注 ${p.model} #${p.res_id}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 日历增强 ──────────────────────────────────────────
  api.registerTool({
    name: 'odoo_calendar_today',
    description: '查今日会议/日程（覆盖 00:00–次日 00:00，含我是组织者或参与者）。用于"今天有什么会"、"今天几点开会"。',
    schema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: '上限，默认 30' },
      },
    },
    async handler(p: { limit?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const events = await client.getCalendarToday(p);
        return {
          success: true,
          count: events.length,
          events: events.map(e => ({
            id: e['id'], name: e['name'],
            start: e['start'], stop: e['stop'],
            duration: e['duration'], location: e['location'] || null,
            allday: e['allday'], organizer: e['user_id'],
          })),
        };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_update_event',
    description: '修改日历事件：改时间、地点、标题、描述、参与者。用于"会议挪到下午 3 点"、"把会议地点改到 301 会议室"。',
    schema: {
      type: 'object',
      properties: {
        event_id:    { type: 'number', description: '事件 id（必填）' },
        name:        { type: 'string', description: '新标题' },
        start:       { type: 'string', description: '新开始时间 YYYY-MM-DD HH:MM:SS' },
        stop:        { type: 'string', description: '新结束时间 YYYY-MM-DD HH:MM:SS' },
        location:    { type: 'string', description: '新地点' },
        description: { type: 'string', description: '新描述' },
        partner_ids: { type: 'array', items: { type: 'number' }, description: '新参与者 partner id 列表（整份替换）' },
      },
      required: ['event_id'],
    },
    async handler(p: { event_id: number; name?: string; start?: string; stop?: string; location?: string; description?: string; partner_ids?: number[] }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      const values: Record<string, unknown> = {};
      if (p.name !== undefined) values['name'] = p.name;
      if (p.start !== undefined) values['start'] = p.start;
      if (p.stop !== undefined) values['stop'] = p.stop;
      if (p.location !== undefined) values['location'] = p.location;
      if (p.description !== undefined) values['description'] = p.description;
      if (p.partner_ids !== undefined) values['partner_ids'] = [[6, false, p.partner_ids]];
      if (Object.keys(values).length === 0) {
        return { success: true, message: `事件 #${p.event_id} 无需更新（未提供任何字段）` };
      }
      try {
        // partner_ids 的旧值比较复杂（many2many），这里还是走 loggedWrite 让大多数字段可撤销；
        // 如果只是改 partner_ids，快照里会记录原列表的 id 数组，undo 写回也可工作。
        await loggedWrite(client, ctx, {
          tool: 'odoo_update_event',
          model: 'calendar.event',
          ids: [p.event_id],
          values,
          summary: `更新事件 #${p.event_id}（字段：${Object.keys(values).join(', ')}）`,
        });
        return { success: true, message: `事件 #${p.event_id} 已更新（可用 odoo_undo_last 撤销）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_cancel_event',
    description: '取消（归档）日历事件：active=false。数据保留在系统中不物理删除，可用 odoo_undo_last 还原。',
    schema: {
      type: 'object',
      properties: { event_id: { type: 'number', description: '事件 id（必填）' } },
      required: ['event_id'],
    },
    async handler(p: { event_id: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await loggedWrite(client, ctx, {
          tool: 'odoo_cancel_event',
          model: 'calendar.event',
          ids: [p.event_id],
          values: { active: false },
          summary: `取消事件 #${p.event_id}`,
        });
        return { success: true, message: `事件 #${p.event_id} 已取消（active=false，可用 odoo_undo_last 还原）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 邮件 ──────────────────────────────────────────────
  api.registerTool({
    name: 'odoo_send_email',
    description: '发送邮件（走 mail.mail，立即 send）。recipients 是收件人邮箱数组；body 支持 markdown（自动转 HTML）或 HTML。可选挂到某条 辉火云记录：res_model + res_id。',
    schema: {
      type: 'object',
      properties: {
        subject:        { type: 'string', description: '邮件主题（必填）' },
        body:           { type: 'string', description: '邮件正文（markdown 或 HTML，必填）' },
        recipients:     { type: 'array', items: { type: 'string' }, description: '收件人邮箱列表（必填）' },
        cc:             { type: 'array', items: { type: 'string' }, description: '抄送邮箱列表' },
        bcc:            { type: 'array', items: { type: 'string' }, description: '密送邮箱列表' },
        res_model:      { type: 'string', description: '关联模型（可选，如 "crm.lead"）' },
        res_id:         { type: 'number', description: '关联记录 id（可选）' },
        attachment_ids: { type: 'array', items: { type: 'number' }, description: 'ir.attachment id 列表（可选，先用 odoo_attach_file 或 odoo_document_upload 得到 id）' },
      },
      required: ['subject', 'body', 'recipients'],
    },
    async handler(
      p: { subject: string; body: string; recipients: string[]; cc?: string[]; bcc?: string[]; res_model?: string; res_id?: number; attachment_ids?: number[] },
      ctx: Record<string, unknown>,
    ) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      if (!p.recipients || p.recipients.length === 0) {
        return { success: false, message: '至少需要一个收件人（recipients）' };
      }
      try {
        const id = await client.sendEmail({
          subject: p.subject,
          bodyHtml: mdToHtml(p.body),
          recipients: p.recipients,
          cc: p.cc,
          bcc: p.bcc,
          res_model: p.res_model,
          res_id: p.res_id,
          attachment_ids: p.attachment_ids,
        });
        return { success: true, mail_id: id, message: `邮件已发送到 ${p.recipients.join(', ')}（mail.mail #${id}）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_email_templates',
    description: '列出邮件模板（mail.template）。可按 model 过滤，如"我有哪些商机相关的邮件模板"。',
    schema: {
      type: 'object',
      properties: {
        model:   { type: 'string', description: '限定模板的 model 字段（如 "crm.lead"）' },
        keyword: { type: 'string', description: '按模板名模糊匹配' },
        limit:   { type: 'number', description: '上限，默认 50' },
      },
    },
    async handler(p: { model?: string; keyword?: string; limit?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const templates = await client.getEmailTemplates(p);
        return {
          success: true,
          count: templates.length,
          templates: templates.map(t => ({
            id: t['id'], name: t['name'],
            model: t['model'], subject: t['subject'],
            email_to: t['email_to'] || null,
            use_default_to: t['use_default_to'],
          })),
        };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_email_from_template',
    description: '用模板发邮件（mail.template.send_mail，force_send=true）。用于"用那个报价单模板发给客户"。template_id 从 odoo_email_templates 取。',
    schema: {
      type: 'object',
      properties: {
        template_id:  { type: 'number', description: '模板 id（必填）' },
        res_id:       { type: 'number', description: '目标记录 id，模板会渲染该记录的字段（必填，模板的 model 决定类型）' },
        email_values: { type: 'object', description: '可选的字段覆盖（如 {email_to: "alt@example.com"}）' },
      },
      required: ['template_id', 'res_id'],
    },
    async handler(p: { template_id: number; res_id: number; email_values?: Record<string, unknown> }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const result = await client.sendEmailFromTemplate(p.template_id, p.res_id, {
          force_send: true,
          email_values: p.email_values,
        });
        return { success: true, result, message: `模板 #${p.template_id} 已对 res_id=${p.res_id} 发送` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 附件 / 文档 ───────────────────────────────────────
  api.registerTool({
    name: 'odoo_attach_file',
    description: '把本地文件上传为辉火云附件（ir.attachment）并挂到指定记录。用于"把这份合同 PDF 附到商机 #42"。path 传本地绝对路径，插件会读文件并 base64 编码。大文件（>5MB）请走 odoo_document_upload。',
    schema: {
      type: 'object',
      properties: {
        path:      { type: 'string', description: '本地文件绝对路径（必填）' },
        res_model: { type: 'string', description: '数据模型，如 "crm.lead"（必填）' },
        res_id:    { type: 'number', description: '记录 id（必填）' },
        name:      { type: 'string', description: '附件显示名（可选，默认=文件名）' },
        mimetype:  { type: 'string', description: 'MIME 类型（可选，默认 application/octet-stream）' },
      },
      required: ['path', 'res_model', 'res_id'],
    },
    async handler(p: { path: string; res_model: string; res_id: number; name?: string; mimetype?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const stat = statSync(p.path);
        if (stat.size > 10 * 1024 * 1024) {
          return { success: false, message: `文件 ${p.path} 大小 ${(stat.size / 1024 / 1024).toFixed(1)}MB，超过附件上限 10MB，请用 odoo_document_upload 传到文档应用` };
        }
        const buf = readFileSync(p.path);
        const datas = buf.toString('base64');
        const id = await client.attachFile({
          res_model: p.res_model,
          res_id: p.res_id,
          name: p.name || basename(p.path),
          datas_base64: datas,
          mimetype: p.mimetype,
        });
        return { success: true, attachment_id: id, size: stat.size, message: `附件 #${id} 已挂到 ${p.res_model} #${p.res_id}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_list_attachments',
    description: '列出某条记录挂着的所有附件。用于"商机 #42 有哪些附件"、"那个合同有没有上传"。',
    schema: {
      type: 'object',
      properties: {
        model:  { type: 'string', description: '数据模型名（必填）' },
        res_id: { type: 'number', description: '记录 id（必填）' },
        limit:  { type: 'number', description: '上限，默认 50' },
      },
      required: ['model', 'res_id'],
    },
    async handler(p: { model: string; res_id: number; limit?: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const atts = await client.listAttachments(p.model, p.res_id, { limit: p.limit });
        const info = client.getSessionInfo();
        return {
          success: true,
          count: atts.length,
          attachments: atts.map(a => ({
            id: a['id'], name: a['name'],
            mimetype: a['mimetype'],
            size_bytes: a['file_size'],
            created: a['create_date'],
            created_by: a['create_uid'],
            download_url: `${info.url}/web/content/${a['id']}?download=true`,
          })),
        };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_document_upload',
    description: '上传文件到辉火云文档应用（documents.document），可指定 folder_id 归档。用于"把这份交接文档归到项目资料夹"。附件上限 20MB。',
    schema: {
      type: 'object',
      properties: {
        path:      { type: 'string', description: '本地文件绝对路径（必填）' },
        name:      { type: 'string', description: '显示名（默认=文件名）' },
        folder_id: { type: 'number', description: '归档文件夹 id（可选）' },
        tag_ids:   { type: 'array', items: { type: 'number' }, description: '标签 id 列表（可选）' },
        mimetype:  { type: 'string', description: 'MIME 类型（可选）' },
      },
      required: ['path'],
    },
    async handler(p: { path: string; name?: string; folder_id?: number; tag_ids?: number[]; mimetype?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const stat = statSync(p.path);
        if (stat.size > 20 * 1024 * 1024) {
          return { success: false, message: `文件 ${p.path} 大小 ${(stat.size / 1024 / 1024).toFixed(1)}MB，超过上限 20MB` };
        }
        const buf = readFileSync(p.path);
        const datas = buf.toString('base64');
        const id = await client.uploadDocument({
          name: p.name || basename(p.path),
          datas_base64: datas,
          mimetype: p.mimetype,
          folder_id: p.folder_id,
          tag_ids: p.tag_ids,
        });
        return { success: true, document_id: id, size: stat.size, message: `文档 #${id} 已上传到 documents.document` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 批量更新（带变更日志）─────────────────────────────
  api.registerTool({
    name: 'odoo_bulk_update',
    description: '对同一模型的多条记录做同一组字段更新，写入变更日志，可用 odoo_undo_last 整体撤销。用于"把这批任务都改成已完成"、"这 10 个商机都挪到下一阶段"。谨慎：values 会对所有 ids 生效。',
    schema: {
      type: 'object',
      properties: {
        model:  { type: 'string', description: '数据模型名，如 "project.task"（必填）' },
        ids:    { type: 'array', items: { type: 'number' }, description: '记录 id 列表（必填，至少 1 条）' },
        values: { type: 'object', description: '要写入的字段对象，如 {stage_id: 5, priority: "2"}（必填，至少 1 个字段）' },
      },
      required: ['model', 'ids', 'values'],
    },
    async handler(p: { model: string; ids: number[]; values: Record<string, unknown> }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      if (!p.ids || p.ids.length === 0) return { success: false, message: 'ids 不能为空' };
      if (!p.values || Object.keys(p.values).length === 0) return { success: false, message: 'values 不能为空' };
      if (p.ids.length > 200) return { success: false, message: `一次最多 200 条，当前 ${p.ids.length} 条，拆分后再试` };
      try {
        await loggedWrite(client, ctx, {
          tool: 'odoo_bulk_update',
          model: p.model,
          ids: p.ids,
          values: p.values,
          summary: `批量更新 ${p.model} × ${p.ids.length} 条（字段：${Object.keys(p.values).join(', ')}）`,
        });
        return {
          success: true,
          updated: p.ids.length,
          model: p.model,
          message: `已更新 ${p.ids.length} 条 ${p.model}（可用 odoo_undo_last 整体撤销）`,
        };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 撤销上一步 ────────────────────────────────────────
  api.registerTool({
    name: 'odoo_undo_last',
    description: '撤销上一步可逆的 write（任务/商机/活动改期/事件更新/批量更新/…）。dry_run=true 时只预览不执行；list=true 时列出最近 10 条可撤销变更不执行。注意：只能撤销通过本插件工具做的 write，create/unlink 不在此范围。',
    schema: {
      type: 'object',
      properties: {
        dry_run: { type: 'boolean', description: 'true=只预览将撤销什么，不真正执行' },
        list:    { type: 'boolean', description: 'true=列出最近 10 条可撤销变更，不执行任何撤销' },
      },
    },
    async handler(p: { dry_run?: boolean; list?: boolean }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      const aid = getAgentId(ctx);

      if (p.list) {
        const recent = mutationLog.list(aid, { limit: 10, reversibleOnly: true });
        return {
          success: true,
          count: recent.length,
          entries: recent.map(e => ({
            id: e.id, tool: e.tool, model: e.model,
            ids: e.ids, timestamp: e.timestamp, summary: e.summary,
          })),
          message: recent.length === 0 ? '没有可撤销的变更' : `最近 ${recent.length} 条可撤销变更`,
        };
      }

      const last = mutationLog.findLastReversible(aid);
      if (!last) return { success: false, message: '没有可撤销的变更（mutation-log 为空或全部已撤销）' };

      if (p.dry_run) {
        return {
          success: true,
          preview: true,
          entry: {
            id: last.id, tool: last.tool, model: last.model, ids: last.ids,
            summary: last.summary, timestamp: last.timestamp,
            will_write_back: last.before,
          },
          message: `将撤销：${last.summary}`,
        };
      }

      // 真正撤销：按 id 把 before 快照写回
      const errors: string[] = [];
      let ok = 0;
      for (const snap of last.before) {
        const id = snap['id'] as number;
        const { id: _skip, ...values } = snap;
        void _skip;
        try {
          await client.write(last.model, [id], values);
          ok++;
        } catch (e) {
          errors.push(`#${id}: ${e instanceof Error ? e.message : String(e)}`);
        }
      }
      if (ok > 0) mutationLog.markUndone(aid, last.id);
      return {
        success: errors.length === 0,
        undone: ok,
        failed: errors.length,
        errors: errors.length > 0 ? errors : undefined,
        entry_id: last.id,
        message: errors.length === 0
          ? `已撤销：${last.summary}（${ok} 条记录还原到之前的值）`
          : `部分撤销失败：${ok}/${last.before.length} 成功，${errors.length} 失败`,
      };
    },
  });

  // ══════════════════════════════════════════════════════
  // v1.8 — Project / Ticket / Chatter 闭环
  // ══════════════════════════════════════════════════════

  // ── Chatter 沟通 ──────────────────────────────────────
  api.registerTool({
    name: 'odoo_message_post',
    description: '在任意 mail.thread 记录（任务/商机/工单/订单/客户等）的 chatter 发评论。会触发邮件通知所有关注者。body 支持 markdown 或 HTML。用于"给客户在商机下留个进度说明"、"在工单里回客户一句"。内部记录（不发邮件）请用 odoo_message_log。',
    schema: {
      type: 'object',
      properties: {
        model:          { type: 'string', description: '数据模型名（必填），如 "crm.lead"、"project.task"、"helpdesk.ticket"' },
        res_id:         { type: 'number', description: '记录 id（必填）' },
        body:           { type: 'string', description: '消息正文（markdown 或 HTML，必填）' },
        subject:        { type: 'string', description: '主题（可选，邮件通知时显示）' },
        partner_ids:    { type: 'array', items: { type: 'number' }, description: '额外 @提及 / 通知的 partner id 列表（可选）' },
        attachment_ids: { type: 'array', items: { type: 'number' }, description: 'ir.attachment id 列表（先用 odoo_attach_file 得到 id）' },
      },
      required: ['model', 'res_id', 'body'],
    },
    async handler(
      p: { model: string; res_id: number; body: string; subject?: string; partner_ids?: number[]; attachment_ids?: number[] },
      ctx: Record<string, unknown>,
    ) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.postMessage(p.model, p.res_id, {
          bodyHtml: mdToHtml(p.body),
          subject: p.subject,
          partner_ids: p.partner_ids,
          attachment_ids: p.attachment_ids,
          as_log: false,
        });
        return { success: true, message_id: id, message: `已在 ${p.model} #${p.res_id} 发评论（mail.message #${id}，followers 会收到邮件通知）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_message_log',
    description: '在记录 chatter 留内部记录（log note，不发邮件）。用于"给这条记录加个备注"、"记录一下今天的沟通要点"。与 odoo_message_post 的区别：log 不通知 followers。',
    schema: {
      type: 'object',
      properties: {
        model:          { type: 'string', description: '数据模型名（必填）' },
        res_id:         { type: 'number', description: '记录 id（必填）' },
        body:           { type: 'string', description: '备注内容（markdown 或 HTML，必填）' },
        subject:        { type: 'string', description: '标题（可选）' },
        attachment_ids: { type: 'array', items: { type: 'number' }, description: 'ir.attachment id 列表（可选）' },
      },
      required: ['model', 'res_id', 'body'],
    },
    async handler(
      p: { model: string; res_id: number; body: string; subject?: string; attachment_ids?: number[] },
      ctx: Record<string, unknown>,
    ) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.postMessage(p.model, p.res_id, {
          bodyHtml: mdToHtml(p.body),
          subject: p.subject,
          attachment_ids: p.attachment_ids,
          as_log: true,
        });
        return { success: true, message_id: id, message: `已在 ${p.model} #${p.res_id} 留内部记录（#${id}，不通知 followers）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_message_history',
    description: '读取某条记录的 chatter 沟通历史（最新在前）。用于"这个商机跟进过什么"、"看看工单 #X 有哪些往来"。默认过滤掉系统通知。',
    schema: {
      type: 'object',
      properties: {
        model:                 { type: 'string', description: '数据模型名（必填）' },
        res_id:                { type: 'number', description: '记录 id（必填）' },
        limit:                 { type: 'number', description: '上限，默认 20' },
        include_notifications: { type: 'boolean', description: 'true=包含系统通知（自动关注、阶段变更等），默认 false' },
      },
      required: ['model', 'res_id'],
    },
    async handler(p: { model: string; res_id: number; limit?: number; include_notifications?: boolean }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const msgs = await client.getMessageHistory(p.model, p.res_id, p);
        return {
          success: true,
          count: msgs.length,
          messages: msgs.map(m => ({
            id: m['id'],
            date: m['date'],
            author: m['author_id'],
            email_from: m['email_from'] || null,
            subject: m['subject'] || null,
            type: m['message_type'],
            // 只给纯文本摘要，HTML 全文前端需要再查（避免单次响应爆炸）
            summary: stripHtml(String(m['body'] ?? '')),
          })),
        };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 项目 ──────────────────────────────────────────────
  api.registerTool({
    name: 'odoo_project_create',
    description: '创建新项目。用于"开个新项目叫 XX"、"给客户 Y 建个实施项目"。privacy_visibility 决定可见范围：followers=仅关注者/employees=全体员工（默认）/portal=门户用户。',
    schema: {
      type: 'object',
      properties: {
        name:               { type: 'string', description: '项目名（必填）' },
        partner_id:         { type: 'number', description: '客户 partner id（可选）' },
        user_id:            { type: 'number', description: '项目负责人 user id（可选，默认=当前用户）' },
        date_start:         { type: 'string', description: '开始日期 YYYY-MM-DD' },
        date:               { type: 'string', description: '结束日期 YYYY-MM-DD' },
        description:        { type: 'string', description: '项目描述' },
        privacy_visibility: { type: 'string', enum: ['followers', 'employees', 'portal'], description: '可见范围' },
      },
      required: ['name'],
    },
    async handler(
      p: { name: string; partner_id?: number; user_id?: number; date_start?: string; date?: string; description?: string; privacy_visibility?: 'followers' | 'employees' | 'portal' },
      ctx: Record<string, unknown>,
    ) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.createProject(p);
        return { success: true, project_id: id, message: `项目 #${id}（${p.name}）已创建` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_project_update',
    description: '更新项目字段：名称/负责人/起止日期/描述/归档等。支持 odoo_undo_last 撤销。',
    schema: {
      type: 'object',
      properties: {
        project_id:  { type: 'number', description: '项目 id（必填）' },
        name:        { type: 'string', description: '新名称' },
        user_id:     { type: 'number', description: '新负责人 user id' },
        partner_id:  { type: 'number', description: '新客户 partner id' },
        date_start:  { type: 'string', description: '新开始日期 YYYY-MM-DD' },
        date:        { type: 'string', description: '新结束日期 YYYY-MM-DD' },
        description: { type: 'string', description: '新描述' },
        active:      { type: 'boolean', description: 'active=false 归档项目' },
      },
      required: ['project_id'],
    },
    async handler(
      p: { project_id: number; name?: string; user_id?: number; partner_id?: number; date_start?: string; date?: string; description?: string; active?: boolean },
      ctx: Record<string, unknown>,
    ) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      const values: Record<string, unknown> = {};
      if (p.name !== undefined) values['name'] = p.name;
      if (p.user_id !== undefined) values['user_id'] = p.user_id;
      if (p.partner_id !== undefined) values['partner_id'] = p.partner_id;
      if (p.date_start !== undefined) values['date_start'] = p.date_start || false;
      if (p.date !== undefined) values['date'] = p.date || false;
      if (p.description !== undefined) values['description'] = p.description;
      if (p.active !== undefined) values['active'] = p.active;
      if (Object.keys(values).length === 0) {
        return { success: true, message: `项目 #${p.project_id} 无需更新（未提供任何字段）` };
      }
      try {
        await loggedWrite(client, ctx, {
          tool: 'odoo_project_update',
          model: 'project.project',
          ids: [p.project_id],
          values,
          summary: `更新项目 #${p.project_id}（字段：${Object.keys(values).join(', ')}）`,
        });
        return { success: true, message: `项目 #${p.project_id} 已更新（可用 odoo_undo_last 撤销）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 里程碑 ────────────────────────────────────────────
  api.registerTool({
    name: 'odoo_milestone_create',
    description: '为项目新建里程碑。用于"给项目 X 加一个 9 月底的交付里程碑"。',
    schema: {
      type: 'object',
      properties: {
        name:       { type: 'string', description: '里程碑名称（必填）' },
        project_id: { type: 'number', description: '所属项目 id（必填）' },
        deadline:   { type: 'string', description: '截止日期 YYYY-MM-DD' },
      },
      required: ['name', 'project_id'],
    },
    async handler(p: { name: string; project_id: number; deadline?: string }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        const id = await client.createMilestone(p);
        return { success: true, milestone_id: id, message: `里程碑 #${id}（${p.name}）已创建于项目 #${p.project_id}` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_milestone_done',
    description: '把里程碑标记为完成（写 is_reached=true + reached_date=today）。支持 odoo_undo_last 撤销。',
    schema: {
      type: 'object',
      properties: { milestone_id: { type: 'number', description: '里程碑 id（必填）' } },
      required: ['milestone_id'],
    },
    async handler(p: { milestone_id: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await loggedWrite(client, ctx, {
          tool: 'odoo_milestone_done',
          model: 'project.milestone',
          ids: [p.milestone_id],
          values: { is_reached: true, reached_date: today() },
          summary: `里程碑 #${p.milestone_id} 标记为已完成`,
        });
        return { success: true, message: `里程碑 #${p.milestone_id} 已完成（reached_date=${today()}，可用 odoo_undo_last 撤销）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 任务指派 ──────────────────────────────────────────
  api.registerTool({
    name: 'odoo_task_assign',
    description: '指派一条或多条任务给一个/一批人（整份替换 user_ids）。用于"把这批任务都交给张三"、"加上李四一起做"。支持 odoo_undo_last 撤销。',
    schema: {
      type: 'object',
      properties: {
        task_ids: { type: 'array', items: { type: 'number' }, description: '任务 id 列表（必填，至少 1 条）' },
        user_ids: { type: 'array', items: { type: 'number' }, description: 'user id 列表（必填，整份替换）' },
      },
      required: ['task_ids', 'user_ids'],
    },
    async handler(p: { task_ids: number[]; user_ids: number[] }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      if (!p.task_ids || p.task_ids.length === 0) return { success: false, message: 'task_ids 不能为空' };
      if (!p.user_ids) return { success: false, message: 'user_ids 必填（传空数组表示清空）' };
      try {
        await loggedWrite(client, ctx, {
          tool: 'odoo_task_assign',
          model: 'project.task',
          ids: p.task_ids,
          values: { user_ids: [[6, false, p.user_ids]] },
          summary: `指派 ${p.task_ids.length} 条任务给 user(${p.user_ids.join(',')})`,
        });
        return { success: true, updated: p.task_ids.length, message: `${p.task_ids.length} 条任务已指派（可用 odoo_undo_last 撤销）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 工单闭环 ──────────────────────────────────────────
  api.registerTool({
    name: 'odoo_ticket_update',
    description: '更新工单字段：名称/阶段/优先级/负责人/看板状态/截止。支持 odoo_undo_last 撤销。',
    schema: {
      type: 'object',
      properties: {
        ticket_id:    { type: 'number', description: '工单 id（必填）' },
        name:         { type: 'string', description: '新主题' },
        stage_id:     { type: 'number', description: '新阶段 id' },
        priority:     { type: 'string', enum: ['0', '1', '2', '3'], description: '0=普通 1=中 2=高 3=紧急' },
        user_id:      { type: 'number', description: '新负责人 user id' },
        kanban_state: { type: 'string', enum: ['normal', 'done', 'blocked'], description: '看板状态' },
        sla_deadline: { type: 'string', description: '新 SLA 截止时间 YYYY-MM-DD HH:MM:SS' },
      },
      required: ['ticket_id'],
    },
    async handler(
      p: { ticket_id: number; name?: string; stage_id?: number; priority?: string; user_id?: number; kanban_state?: string; sla_deadline?: string },
      ctx: Record<string, unknown>,
    ) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      const values: Record<string, unknown> = {};
      if (p.name !== undefined) values['name'] = p.name;
      if (p.stage_id !== undefined) values['stage_id'] = p.stage_id;
      if (p.priority !== undefined) values['priority'] = p.priority;
      if (p.user_id !== undefined) values['user_id'] = p.user_id;
      if (p.kanban_state !== undefined) values['kanban_state'] = p.kanban_state;
      if (p.sla_deadline !== undefined) values['sla_deadline'] = p.sla_deadline || false;
      if (Object.keys(values).length === 0) {
        return { success: true, message: `工单 #${p.ticket_id} 无需更新（未提供任何字段）` };
      }
      try {
        await loggedWrite(client, ctx, {
          tool: 'odoo_ticket_update',
          model: 'helpdesk.ticket',
          ids: [p.ticket_id],
          values,
          summary: `更新工单 #${p.ticket_id}（字段：${Object.keys(values).join(', ')}）`,
        });
        return { success: true, message: `工单 #${p.ticket_id} 已更新（可用 odoo_undo_last 撤销）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_ticket_close',
    description: '关闭工单：把 stage_id 改到该团队 fold=true 的第一个阶段（= 关闭列）。如果找不到关闭阶段会报错让用户先建一个。支持 odoo_undo_last 撤销。',
    schema: {
      type: 'object',
      properties: {
        ticket_id: { type: 'number', description: '工单 id（必填）' },
      },
      required: ['ticket_id'],
    },
    async handler(p: { ticket_id: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        // 先读 ticket 拿 team_id，再在 team 下找 fold=true 的阶段
        const tks = await client.read('helpdesk.ticket', [p.ticket_id], ['team_id', 'stage_id']);
        const t = tks[0];
        if (!t) return { success: false, message: `工单 #${p.ticket_id} 不存在` };
        const teamRef = t['team_id'];
        const teamId = Array.isArray(teamRef) && typeof teamRef[0] === 'number' ? teamRef[0] : undefined;
        const closedStage = await client.findHelpdeskClosedStage(teamId);
        if (!closedStage) {
          return { success: false, message: `团队 ${teamId ?? '(unset)'} 下找不到 fold=true 的关闭阶段。请先到辉火云客服应用里给这个团队建一个"已完成"阶段（fold=true）。` };
        }
        await loggedWrite(client, ctx, {
          tool: 'odoo_ticket_close',
          model: 'helpdesk.ticket',
          ids: [p.ticket_id],
          values: { stage_id: closedStage['id'] as number, kanban_state: 'done' },
          summary: `关闭工单 #${p.ticket_id}（stage_id → ${String(closedStage['name'])}）`,
        });
        return { success: true, stage: closedStage['name'], message: `工单 #${p.ticket_id} 已关闭（stage=${String(closedStage['name'])}，可用 odoo_undo_last 撤销）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_ticket_assign',
    description: '指派工单给某位工程师。支持 odoo_undo_last 撤销。',
    schema: {
      type: 'object',
      properties: {
        ticket_id: { type: 'number', description: '工单 id（必填）' },
        user_id:   { type: 'number', description: '新负责人 user id（必填）' },
      },
      required: ['ticket_id', 'user_id'],
    },
    async handler(p: { ticket_id: number; user_id: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await loggedWrite(client, ctx, {
          tool: 'odoo_ticket_assign',
          model: 'helpdesk.ticket',
          ids: [p.ticket_id],
          values: { user_id: p.user_id },
          summary: `指派工单 #${p.ticket_id} 给 user #${p.user_id}`,
        });
        return { success: true, message: `工单 #${p.ticket_id} 已指派给 user #${p.user_id}（可用 odoo_undo_last 撤销）` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  // ── 审批动作 ──────────────────────────────────────────
  api.registerTool({
    name: 'odoo_approval_approve',
    description: '作为审批人批准一条审批请求（调 approval.request.action_approve）。用于"批了这条请假/采购申请"。注意：只能操作你本人是审批人的请求。',
    schema: {
      type: 'object',
      properties: { request_id: { type: 'number', description: '审批请求 id（必填）' } },
      required: ['request_id'],
    },
    async handler(p: { request_id: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await client.approveApprovalRequest(p.request_id);
        return { success: true, message: `审批请求 #${p.request_id} 已批准` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.registerTool({
    name: 'odoo_approval_refuse',
    description: '作为审批人拒绝审批请求（调 approval.request.action_refuse）。用于"驳回这条申请"。',
    schema: {
      type: 'object',
      properties: { request_id: { type: 'number', description: '审批请求 id（必填）' } },
      required: ['request_id'],
    },
    async handler(p: { request_id: number }, ctx: Record<string, unknown>) {
      const client = getClient(ctx);
      if (!client) return notConnected();
      try {
        await client.refuseApprovalRequest(p.request_id);
        return { success: true, message: `审批请求 #${p.request_id} 已拒绝` };
      } catch (e) { return { success: false, message: String(e) }; }
    },
  });

  api.logger.info('[odoo] 77 个工具已注册（v1.10 — 共享凭据 + 跨渠道复用）');
}

// ── 注册 before_prompt_build 钩子 ─────────────────────────────────────────────
function registerHooks(api: OpenClawPluginApi) {
  api.on('before_prompt_build', async (_event: unknown, ctx: unknown) => {
    const aid = (ctx as { agentId?: string } | undefined)?.agentId?.trim() ?? 'default';
    const todayStr = today();
    const tomorrowStr = tomorrow();

    // 尝试从持久化恢复连接（per-agent）
    let client = odooClients.get(aid);
    if (!client?.isAuthenticated()) {
      client = await tryRestoreAgent(api, aid) ?? undefined;
    }

    if (!client?.isAuthenticated()) {
      return {
        appendSystemContext: `
## 辉火云企业套件插件 — 未连接

> **品牌口径（硬规则）**：对外沟通时一律称"辉火云企业套件"或"辉火云"。
> 不得出现"Odoo"、"欧度"或任何第三方 ERP 商标；内部模型名（如 project.task）
> 和工具名（odoo_xxx）是技术标识符，仅在调试说明里出现，不要在面向用户的
> 正文里直接朗读。

> **共享凭据规则（v1.10）**：组织内只需有任意一个人配过一次凭据（默认会保存
> 为【组织共享凭据】），后续任何渠道（企微/钉钉/飞书）的任何成员 @ 机器人时，
> **自动复用同一套凭据，禁止再次询问 URL/用户名/密码**。本会话之所以走到
> "未连接"，是因为还没有任何人配过共享凭据，也没有 manifest 静态预填。

插件已加载，当前 agent (\`${aid}\`) 尚未连接到辉火云企业套件，且组织内也没有任何人配过共享凭据。当用户提到任何 ERP 相关操作（待办、任务、商机、客户、订单、工单、发票、会议、提醒、项目、工时、库存、员工、审批等），你应该：

1. **首先说明**："看起来咱们组织还没有人配过辉火云连接。配一次之后，所有同事 @ 我都能用，不需要再输入。"
2. 询问：
   - **公司系统地址**（URL）：例如 https://www.huo15.com
   - **用户名**（邮箱或登录名）
   - **密码**
3. **数据库名不需要主动询问** — odoo_connect 会自动检测（单库自动选、多库返列表）
4. 收集到 URL、用户名、密码后，调用 **odoo_connect**（默认 \`private=false\`，即保存为共享凭据 — 推荐）
5. 仅当用户明确说"只给我自己用"或"我不想让别人用"时，才传 \`private: true\`
6. **重要**：如果用户在群里 @ 你，更要解释清楚"配一次全员通用"，避免每个成员都被反复问凭据

示例引导话术："要使用辉火云企业套件，配一次咱们组织所有同事就都能用了。请告诉我：1) 系统地址 2) 用户名 3) 密码"`.trim(),
      };
    }

    const info = client.getSessionInfo();
    const credSource = configManager.getActiveSource(aid);
    const credSourceLabel = credSource === 'agent' ? '当前会话专属凭据'
      : credSource === 'shared' ? '组织共享凭据（全员复用）'
      : credSource === 'legacy' ? '历史遗留凭据'
      : 'manifest 静态预填';
    return {
      appendSystemContext: `
## 辉火云企业套件 已连接

> **品牌口径（硬规则）**：对外沟通时一律称"辉火云企业套件"或"辉火云"。
> 不得出现"Odoo"、"欧度"或任何第三方 ERP 商标。工具名（odoo_*）和技术模型名
> （如 project.task）仅在调试说明里出现，面向用户的正文请用中文业务术语
> （"任务"/"商机"/"工单"/"内部动态"而非"chatter"等）。

> **共享凭据规则（v1.10）**：当前会话用的凭据是【${credSourceLabel}】。
> 如果是【组织共享凭据】，意味着任何渠道（企微/钉钉/飞书）的任何成员 @ 机器人都
> 自动用这套，**绝对不要在群里再向用户询问 URL/用户名/密码**。
> 如果用户主动要换凭据，告诉他们调用 odoo_connect（默认仍是共享，private=true 则只覆盖自己）。
> 如果用户疑惑"为什么没问我密码"，调用 odoo_whoami 给他看清当前来源。

**用户：** ${info.username}（uid: ${info.uid}）| **系统：** ${info.url} | **agent：** ${aid}
**凭据来源：** ${credSourceLabel}
**今日：** ${todayStr} | **明日：** ${tomorrowStr}

### 工具速查（共 77 个）

**基础**：odoo_connect · odoo_status · odoo_disconnect · odoo_whoami
**任务**：odoo_create_task · odoo_list_tasks · odoo_update_task · odoo_get_task_stages · odoo_task_assign
**活动**：odoo_create_activity · odoo_list_activities · odoo_activity_types · odoo_complete_activity · odoo_reschedule_activity
**日历**：odoo_create_event · odoo_calendar_today · odoo_update_event · odoo_cancel_event
**消息**：odoo_get_messages · odoo_send_message · odoo_message_post · odoo_message_log · odoo_message_history
**邮件**：odoo_send_email · odoo_email_templates · odoo_email_from_template
**附件**：odoo_attach_file · odoo_list_attachments · odoo_document_upload
**关注者**：odoo_follow · odoo_unfollow
**搜索**：odoo_search
**CRM** ：odoo_crm_pipeline · odoo_crm_create · odoo_crm_update · odoo_crm_won · odoo_crm_lost
**项目**：odoo_project_overview · odoo_timesheet_log · odoo_project_create · odoo_project_update · odoo_milestone_create · odoo_milestone_done
**销售**：odoo_sale_orders · odoo_purchase_orders
**客服**：odoo_tickets · odoo_ticket_create · odoo_ticket_update · odoo_ticket_close · odoo_ticket_assign
**财务**：odoo_invoices
**联系人**：odoo_contacts · odoo_contact_create
**库存**：odoo_stock_levels · odoo_stock_pickings
**HR** ：odoo_employees · odoo_leaves · odoo_attendances
**审批**：odoo_approvals · odoo_approval_approve · odoo_approval_refuse
**助手**：odoo_daily_briefing
**通知基座**：odoo_notification_status · odoo_notification_channels · odoo_notification_test · odoo_notification_prefs · odoo_notification_reply
**知识库**：odoo_knowledge_search · odoo_knowledge_read · odoo_knowledge_create · odoo_knowledge_update · odoo_knowledge_append · odoo_knowledge_tree · odoo_knowledge_favorite · odoo_knowledge_trash
**批量/撤销**：odoo_bulk_update · odoo_undo_last

### 自然语言 → 工具映射（直接调用，无需询问）

| 用户说 | 调用工具 |
|--------|---------|
| 今天有什么工作 / 每日概况 | **odoo_daily_briefing** |
| 帮我写个待办 / 创建任务 | **odoo_create_task** |
| 今日截止任务 / 今天要做什么 | **odoo_list_tasks**(today_only=true) |
| 把任务 #X 标记完成 | **odoo_update_task**(stage_id=已完成阶段ID) |
| 提醒我… | **odoo_create_activity** |
| 安排会议 / 约个时间 | **odoo_create_event** |
| 查看商机 / 销售管道 | **odoo_crm_pipeline** |
| 新建商机 | **odoo_crm_create** |
| 这个商机赢了 / 标记赢单 | **odoo_crm_won** |
| 商机丢了 / 标记输单 | **odoo_crm_lost** |
| 项目进展 / 里程碑进度 | **odoo_project_overview** |
| 记录工时 X 小时 | **odoo_timesheet_log** |
| 查看工单 / 待处理问题 | **odoo_tickets** |
| 新建工单 / 提交问题 | **odoo_ticket_create** |
| 查发票 / 逾期应收 | **odoo_invoices**(overdue_only=true) |
| 查销售订单 | **odoo_sale_orders** |
| 查采购订单 | **odoo_purchase_orders** |
| 查客户 / 找联系人 | **odoo_contacts** |
| 添加新客户 | **odoo_contact_create** |
| 查库存 / 产品还有多少 | **odoo_stock_levels** |
| 调拨单 / 出入库 | **odoo_stock_pickings** |
| 查员工 / 某部门有谁 | **odoo_employees** |
| 请假记录 | **odoo_leaves** |
| 考勤 / 打卡 | **odoo_attendances** |
| 审批 / 待审批 | **odoo_approvals** |
| 查看消息 / 邮件通知 | **odoo_get_messages** |
| 查活动类型 | **odoo_activity_types** |
| 通知推送状态 / 企微/钉钉连上没 | **odoo_notification_status** |
| 测试一下通知推送 | **odoo_notification_test** |
| 列出已接入的渠道 | **odoo_notification_channels** |
| 关闭通知 / 别发待办了 / 夜里静音 / 只接收紧急 | **odoo_notification_prefs** |
| 模拟一次企微/钉钉回复写回系统 | **odoo_notification_reply** |
| 找一下关于 X 的知识库文章 / 搜知识库 | **odoo_knowledge_search** |
| 把这篇文章读给我 / 文章 #X 写了什么 | **odoo_knowledge_read** |
| 新建知识库文章 / 记一下这个到知识库 | **odoo_knowledge_create** |
| 改一下这篇文章的标题/正文 | **odoo_knowledge_update** |
| 追加到文章 X 末尾 / 往文章里补一段 | **odoo_knowledge_append** |
| 知识库长啥样 / 工作区里都有哪些文章 | **odoo_knowledge_tree** |
| 收藏这篇 / 取消收藏 | **odoo_knowledge_favorite** |
| 把这篇文章扔进回收站 / 删除文章 | **odoo_knowledge_trash** |
| 那个活动做完了 / 把提醒 #X 标记完成 | **odoo_complete_activity** |
| 活动挪到明天 / 提醒改到下周 | **odoo_reschedule_activity** |
| 我要关注这条任务/商机 / 加我进关注 | **odoo_follow** |
| 取消关注 / 别再给我推这条的变化 | **odoo_unfollow** |
| 今天有什么会 / 查今日日程 | **odoo_calendar_today** |
| 会议改时间 / 会议挪到 X 点 / 换会议室 | **odoo_update_event** |
| 取消这场会 / 把会议归档 | **odoo_cancel_event** |
| 发封邮件给客户 / 给 X 写封邮件 | **odoo_send_email** |
| 有哪些邮件模板 / 找商机相关的模板 | **odoo_email_templates** |
| 用模板发 / 用报价单模板发给他 | **odoo_email_from_template** |
| 把这份合同附到商机 / 上传附件 | **odoo_attach_file** |
| 这个商机/工单有哪些附件 | **odoo_list_attachments** |
| 上传到文档库 / 归档到文件夹 | **odoo_document_upload** |
| 把这批任务都改成完成 / 批量改阶段 | **odoo_bulk_update** |
| 撤销上一步 / 撤回刚才那个 / 改错了 | **odoo_undo_last** |
| 给商机/工单/任务下面留个进度说明 / 在 chatter 回一句 | **odoo_message_post** |
| 记一下备注 / 留个内部记录（不发邮件） | **odoo_message_log** |
| 这个记录都聊过什么 / 看看跟进历史 | **odoo_message_history** |
| 开个新项目 / 新建项目 | **odoo_project_create** |
| 改项目的负责人/日期/描述 | **odoo_project_update** |
| 给项目加个里程碑 / 新建里程碑 | **odoo_milestone_create** |
| 里程碑达成了 / 标记完成 | **odoo_milestone_done** |
| 把这批任务都交给张三 / 指派任务 | **odoo_task_assign** |
| 改工单的阶段/优先级/负责人 | **odoo_ticket_update** |
| 关闭工单 / 工单处理完了 | **odoo_ticket_close** |
| 把工单派给 X | **odoo_ticket_assign** |
| 批这条 / 审批通过 | **odoo_approval_approve** |
| 驳回 / 拒绝这条申请 | **odoo_approval_refuse** |
| 查看当前用什么凭据 / 我的连接是哪套 / 为什么没问我密码 | **odoo_whoami** |
| 断开连接 / 退出系统 | **odoo_disconnect** |

### 常用数据模型（技术内部标识，不在正文中朗读）
project.task · project.project · project.milestone · mail.activity · calendar.event ·
crm.lead · crm.stage · sale.order · purchase.order · helpdesk.ticket · account.move ·
res.partner · hr.employee · hr.leave · hr.attendance · stock.quant · stock.picking ·
account.analytic.line · approval.request · planning.slot · knowledge.article ·
mail.template · mail.mail · mail.followers · ir.attachment · documents.document

### 日期 & 字段规范
- date 字段：YYYY-MM-DD，今天=${todayStr}，明天=${tomorrowStr}
- datetime 字段：YYYY-MM-DD HH:MM:SS，默认上午 09:00:00，下午 14:00:00
- 优先级：0=普通 1=中 2高 3=紧急
- Many2one 读取返回 [id, "名称"]，写入时传数字 id
- 商机阶段可通过 odoo_search(model="crm.stage") 查询
- 活动类型可通过 odoo_activity_types 查询
`.trim(),
    };
  });

  api.logger.info('[odoo] before_prompt_build 钩子已注册（per-agent 隔离）');
}

// ── 处理后端更新通知 ──────────────────────────────────────────────────────────
/**
 * 辉火云企业套件事件 → NotificationEnvelope → 全局通知总线
 *
 * 流程：
 *   1. 应用 per-agent 偏好（enabled / kinds / minPriority / quietHours）
 *   2. 缓存 envelope 溯源信息（供入站回复时定位 辉火云记录）
 *   3. publish 到 bus，渠道插件决定投递细节
 *
 * 本方法不感知具体渠道。
 */
function handleOdooUpdates(api: OpenClawPluginApi, updates: SyncUpdate[], aid: string) {
  if (updates.length === 0) return;

  const prefs = prefsManager.load(aid);
  const odooUrl = odooClients.get(aid)?.getSessionInfo().url;

  let dispatched = 0;
  let filtered = 0;
  for (const u of updates) {
    const env = toEnvelope(u, aid, odooUrl);
    const decision = shouldDeliver(env, prefs);
    if (!decision.deliver) {
      filtered += 1;
      api.logger.debug?.(`[odoo] agent=${aid} 丢弃 ${env.id}: ${decision.reason}`);
      continue;
    }

    // 记录 envelope → 原记录 映射，以便回复时可以写回 chatter
    if (env.origin?.model && env.origin?.resId) {
      envelopeCache.set(env.id, {
        agentId: aid,
        model: env.origin.model,
        resId: env.origin.resId,
      });
    }

    notificationBus.publish(env).catch(err => {
      api.logger.error(`[odoo] bus publish 失败 ${env.id}: ${err instanceof Error ? err.message : String(err)}`);
    });
    dispatched += 1;
  }

  const subs = notificationBus.subscriberCount();
  const transports = notificationBus.listTransports().map(t => t.name).join(',') || '无';
  api.logger.info(
    `[odoo] agent=${aid} 发布 ${dispatched}/${updates.length} 条（过滤 ${filtered}，订阅者=${subs}，渠道=${transports}）`,
  );
}

// ── 处理入站回复（渠道 → 辉火云内部动态）──────────────────────────────────────
async function handleInboundReply(api: OpenClawPluginApi, reply: InboundReply): Promise<void> {
  const origin = envelopeCache.get(reply.envelopeId);
  if (!origin) {
    api.logger.warn?.(`[odoo] 入站回复找不到 envelope 溯源: ${reply.envelopeId}（来自 ${reply.channel}）`);
    return;
  }
  if (!origin.model || !origin.resId) {
    api.logger.warn?.(`[odoo] envelope ${reply.envelopeId} 无可写回目标（缺 model/resId）`);
    return;
  }

  const client = odooClients.get(origin.agentId);
  if (!client?.isAuthenticated()) {
    api.logger.warn?.(`[odoo] agent=${origin.agentId} 未连接，忽略回复 ${reply.envelopeId}`);
    return;
  }

  const bodyHtml = reply.html
    ? reply.html
    : `<p>${escapeHtml(reply.body)}</p>`;
  const subject = `来自 ${reply.channel}${reply.fromUser ? ` / ${reply.fromUser}` : ''} 的回复`;

  try {
    const id = await client.call('mail.message', 'create', [{
      model: origin.model,
      res_id: origin.resId,
      body: bodyHtml,
      subject,
      message_type: 'comment',
      subtype_xmlid: 'mail.mt_comment',
    }]);
    api.logger.info(`[odoo] 入站回复已写入 ${origin.model}#${origin.resId}（mail.message ${String(id)}）`);
  } catch (e) {
    api.logger.error(`[odoo] 写回辉火云内部动态失败: ${e instanceof Error ? e.message : String(e)}`);
  }
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
