/**
 * Odoo JSON-RPC API 客户端 — v1.1
 *
 * 支持 Odoo 19 Enterprise 的 JSON-RPC 接口。
 * 覆盖模块：Session、Project、CRM、Sale、Purchase、
 *           Helpdesk、Accounting、HR、Stock、Mail/Activity
 */

import type { OdooConfig, OdooSession, OdooRecord, OdooError } from '../types/index.js';
import { today, tomorrow } from '../utils/date-utils.js';

type DomainItem = string | [string, string, unknown];
type Domain = DomainItem[];

function isOdooError(result: unknown): result is { error: OdooError } {
  return typeof result === 'object' && result !== null && 'error' in result;
}

export class OdooClient {
  private url: string;
  private db: string;
  private username: string;
  private password: string;
  private uid: number | null = null;
  private session_id: string | null = null;
  private user_context: Record<string, unknown> = {};

  constructor(config: OdooConfig) {
    this.url = config.url.replace(/\/$/, '');
    this.db = config.db;
    this.username = config.username;
    this.password = config.password;
  }

  // ==================== 会话管理 ====================

  async authenticate(): Promise<OdooSession> {
    const result = await this.rpc('/web/session/authenticate', {
      db: this.db,
      login: this.username,
      password: this.password,
    });

    if (isOdooError(result)) {
      throw new Error(`认证失败: ${JSON.stringify(result.error)}`);
    }

    const session = result as OdooSession;
    if (!session.uid) throw new Error('认证失败：用户名或密码错误');

    this.uid = session.uid;
    this.session_id = (session as unknown as Record<string, unknown>).session_id as string | null ?? null;
    this.user_context = session.user_context || {};
    return session;
  }

  async checkSession(): Promise<boolean> {
    try {
      const result = await this.rpc('/web/session/get_session_info', {});
      const r = result as Record<string, unknown>;
      return 'uid' in r && r['uid'] !== false && r['uid'] !== null;
    } catch {
      return false;
    }
  }

  async ensureAuthenticated(): Promise<void> {
    if (!this.isAuthenticated() || !(await this.checkSession())) {
      await this.authenticate();
    }
  }

  async destroy(): Promise<void> {
    try { await this.rpc('/web/session/destroy', {}); } finally {
      this.uid = null; this.session_id = null; this.user_context = {};
    }
  }

  isAuthenticated(): boolean { return this.uid !== null; }
  getUid(): number | null { return this.uid; }

  /**
   * 查询 Odoo 实例可用的数据库列表（无需认证）
   * Odoo 19 端点: POST /web/database/list
   */
  static async listDatabases(url: string): Promise<string[]> {
    const endpoint = `${url.replace(/\/$/, '')}/web/database/list`;
    const payload = { jsonrpc: '2.0', method: 'call', id: Date.now(), params: {} };
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const data = await response.json() as { result?: string[]; error?: unknown };
    if (data.error) throw new Error(`获取数据库列表失败: ${JSON.stringify(data.error)}`);
    return data.result ?? [];
  }
  getSessionInfo(): { uid: number | null; username: string; url: string } {
    return { uid: this.uid, username: this.username, url: this.url };
  }

  // ==================== 通用 ORM ====================

  async searchRead(
    model: string, domain: Domain, fields: string[] = ['id', 'name'],
    options: { limit?: number; offset?: number; order?: string } = {},
  ): Promise<{ length: number; records: OdooRecord[] }> {
    const { limit = 100, offset = 0, order = '' } = options;
    const result = await this.rpc('/web/dataset/call_kw', {
      model, method: 'search_read', args: [domain],
      kwargs: { fields, domain, limit, offset, order },
    });
    if (isOdooError(result)) throw new Error(`查询 ${model} 失败: ${JSON.stringify(result.error)}`);
    const records = Array.isArray(result) ? result as OdooRecord[] : [];
    return { length: records.length, records };
  }

  async read(model: string, ids: number[], fields: string[] = ['id', 'name']): Promise<OdooRecord[]> {
    const result = await this.rpc('/web/dataset/call_kw', { model, method: 'read', args: [ids], kwargs: { fields } });
    if (isOdooError(result)) throw new Error(`读取 ${model} 失败: ${JSON.stringify(result.error)}`);
    return result as OdooRecord[];
  }

  async create(model: string, values: Record<string, unknown>): Promise<number> {
    const result = await this.rpc('/web/dataset/call_kw', { model, method: 'create', args: [values], kwargs: {} });
    if (isOdooError(result)) throw new Error(`创建 ${model} 失败: ${JSON.stringify(result.error)}`);
    return result as number;
  }

  async write(model: string, ids: number[], values: Record<string, unknown>): Promise<boolean> {
    const result = await this.rpc('/web/dataset/call_kw', { model, method: 'write', args: [ids, values], kwargs: {} });
    if (isOdooError(result)) throw new Error(`更新 ${model} 失败: ${JSON.stringify(result.error)}`);
    return result === true;
  }

  async unlink(model: string, ids: number[]): Promise<boolean> {
    const result = await this.rpc('/web/dataset/call_kw', { model, method: 'unlink', args: [ids], kwargs: {} });
    if (isOdooError(result)) throw new Error(`删除 ${model} 失败: ${JSON.stringify(result.error)}`);
    return result === true;
  }

  async searchCount(model: string, domain: Domain): Promise<number> {
    const result = await this.rpc('/web/dataset/call_kw', { model, method: 'search_count', args: [domain], kwargs: {} });
    if (isOdooError(result)) throw new Error(`计数 ${model} 失败: ${JSON.stringify(result.error)}`);
    return result as number;
  }

  async call(model: string, method: string, args: unknown[] = [], kwargs: Record<string, unknown> = {}): Promise<unknown> {
    const result = await this.rpc('/web/dataset/call_kw', { model, method, args, kwargs });
    if (isOdooError(result)) throw new Error(`调用 ${model}.${method} 失败: ${JSON.stringify(result.error)}`);
    return result;
  }

  // ==================== Project / Task ====================

  async createTask(values: {
    name: string; description?: string; project_id?: number;
    date_deadline?: string; user_ids?: number[]; priority?: '0' | '1' | '2' | '3';
  }): Promise<number> {
    return this.create('project.task', {
      name: values.name,
      description: values.description || '',
      project_id: values.project_id || false,
      date_deadline: values.date_deadline || false,
      user_ids: values.user_ids ? [[6, false, values.user_ids]] : [[6, false, [this.uid ?? 1]]],
      priority: values.priority || '0',
      active: true,
    });
  }

  /**
   * 获取我的任务（待办）
   *
   * Odoo 待办应用（To-Do）基于 project.task 模型，
   * 过滤条件：project_id=False（无项目=私人任务）
   * 项目任务在「项目」应用中管理，不在待办里。
   *
   * Odoo project.task 状态机制：
   * - state 字段：01_in_progress / 04_waiting_normal / 1_done / 1_canceled 等
   * - is_closed = state in ['1_done', '1_canceled']
   *
   * stage_state 选项：
   *   'in_progress' — 进行中（未关闭，默认）
   *   'done'        — 已完成
   *   'all'         — 全部
   *
   * include_project — 是否包含项目任务（默认 false，待办应用模式）
   */
  async getMyTasks(options: {
    limit?: number;
    project_id?: number;
    today_only?: boolean;
    stage_state?: 'in_progress' | 'done' | 'all';
    state_filter?: string;
    stage_id?: number;
    include_project?: boolean;
  } = {}): Promise<OdooRecord[]> {
    // 待办应用过滤：project_id=False（私人任务），排除子任务
    // 项目任务（project_id 有值）属于「项目」应用，不在待办里
    const domain: Domain = [['user_ids', 'in', [this.uid ?? 0]], ['active', '=', true], ['project_id', '=', false], ['parent_id', '=', false]];
    if (options.project_id) {
      // 如果指定了 project_id，则切换到项目任务模式
      domain.length = 0;
      domain.push(['user_ids', 'in', [this.uid ?? 0]], ['active', '=', true], ['project_id', '=', options.project_id]);
    }
    if (options.today_only) domain.push(['date_deadline', '<=', today()]);

    const stageState = options.stage_state ?? 'in_progress';
    if (stageState === 'in_progress') {
      domain.push(['state', 'not in', ['1_done', '1_canceled']]);
    } else if (stageState === 'done') {
      domain.push(['state', 'in', ['1_done', '1_canceled']]);
    }

    if (options.state_filter) {
      domain.length = domain.filter(d => !Array.isArray(d) || d[0] !== 'state').length;
      domain.push(['state', '=', options.state_filter]);
    }

    if (options.stage_id) domain.push(['stage_id', '=', options.stage_id]);

    const result = await this.searchRead('project.task', domain,
      ['id', 'name', 'description', 'date_deadline', 'stage_id', 'project_id', 'priority', 'user_ids', 'milestone_id', 'state'],
      { limit: options.limit ?? 50 });
    return result.records;
  }

  /** 获取项目任务阶段列表（用于查找 stage_id） */
  async getTaskStages(projectId?: number): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (projectId) domain.push(['project_ids', '=', projectId]);
    const result = await this.searchRead('project.task.type', domain,
      ['id', 'name', 'fold', 'sequence'], { order: 'sequence asc' });
    return result.records;
  }

  async getProjectOverview(projectId?: number): Promise<OdooRecord[]> {
    const domain: Domain = [['active', '=', true]];
    if (projectId) domain.push(['id', '=', projectId]);
    const result = await this.searchRead('project.project', domain,
      ['id', 'name', 'partner_id', 'user_id', 'date_start', 'date', 'task_count', 'open_task_count', 'closed_task_count'],
      { limit: 50 });
    return result.records;
  }

  async getMilestones(projectId?: number): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (projectId) domain.push(['project_id', '=', projectId]);
    const result = await this.searchRead('project.milestone', domain,
      ['id', 'name', 'project_id', 'deadline', 'is_reached', 'reached_date', 'task_count', 'done_task_count', 'is_deadline_exceeded'],
      { limit: 50 });
    return result.records;
  }

  async logTimesheet(values: {
    name: string; unit_amount: number; project_id?: number; task_id?: number; date?: string;
  }): Promise<number> {
    return this.create('account.analytic.line', {
      name: values.name,
      unit_amount: values.unit_amount,
      date: values.date || today(),
      user_id: this.uid ?? 1,
      project_id: values.project_id || false,
      task_id: values.task_id || false,
    });
  }

  // ==================== CRM ====================

  async getCrmPipeline(options: {
    limit?: number; stage_id?: number; user_id?: number;
    type?: 'lead' | 'opportunity'; won_status?: string;
  } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [['active', '=', true]];
    if (options.stage_id) domain.push(['stage_id', '=', options.stage_id]);
    if (options.user_id) domain.push(['user_id', '=', options.user_id]);
    else domain.push(['user_id', '=', this.uid ?? 0]);
    if (options.type) domain.push(['type', '=', options.type]);
    const result = await this.searchRead('crm.lead', domain,
      ['id', 'name', 'partner_id', 'stage_id', 'probability', 'expected_revenue', 'user_id', 'team_id', 'date_deadline', 'type', 'won_status', 'activity_ids', 'tag_ids'],
      { limit: options.limit ?? 50, order: 'stage_id asc, probability desc' });
    return result.records;
  }

  async createCrmLead(values: {
    name: string; type?: 'lead' | 'opportunity'; partner_id?: number;
    expected_revenue?: number; probability?: number; user_id?: number;
    stage_id?: number; date_deadline?: string; description?: string;
  }): Promise<number> {
    return this.create('crm.lead', {
      name: values.name,
      type: values.type || 'opportunity',
      partner_id: values.partner_id || false,
      expected_revenue: values.expected_revenue || 0,
      probability: values.probability || 10,
      user_id: values.user_id || this.uid || 1,
      stage_id: values.stage_id || false,
      date_deadline: values.date_deadline || false,
      description: values.description || '',
    });
  }

  async setCrmWon(leadIds: number[]): Promise<boolean> {
    await this.call('crm.lead', 'action_set_won', [leadIds]);
    return true;
  }

  async setCrmLost(leadIds: number[], lostReasonId?: number): Promise<boolean> {
    const kwargs: Record<string, unknown> = {};
    if (lostReasonId) kwargs['additional_values'] = { lost_reason_id: lostReasonId };
    await this.call('crm.lead', 'action_set_lost', [leadIds], kwargs);
    return true;
  }

  async getCrmStages(): Promise<OdooRecord[]> {
    const result = await this.searchRead('crm.stage', [],
      ['id', 'name', 'sequence', 'is_won', 'fold'], { order: 'sequence asc' });
    return result.records;
  }

  // ==================== Sales ====================

  async getSaleOrders(options: {
    limit?: number; state?: string; partner_id?: number; user_id?: number;
  } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (options.state) domain.push(['state', '=', options.state]);
    else domain.push(['state', 'not in', ['cancel']]);
    if (options.partner_id) domain.push(['partner_id', '=', options.partner_id]);
    if (options.user_id) domain.push(['user_id', '=', options.user_id]);
    const result = await this.searchRead('sale.order', domain,
      ['id', 'name', 'partner_id', 'state', 'date_order', 'amount_total', 'invoice_status', 'user_id', 'team_id', 'validity_date'],
      { limit: options.limit ?? 20, order: 'date_order desc' });
    return result.records;
  }

  async confirmSaleOrder(orderId: number): Promise<unknown> {
    return this.call('sale.order', 'action_confirm', [[orderId]]);
  }

  // ==================== Purchase ====================

  async getPurchaseOrders(options: { limit?: number; state?: string } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (options.state) domain.push(['state', '=', options.state]);
    else domain.push(['state', 'not in', ['cancel']]);
    const result = await this.searchRead('purchase.order', domain,
      ['id', 'name', 'partner_id', 'state', 'date_order', 'date_planned', 'amount_total', 'invoice_status', 'user_id'],
      { limit: options.limit ?? 20, order: 'date_order desc' });
    return result.records;
  }

  // ==================== Helpdesk ====================

  async getHelpdeskTickets(options: {
    limit?: number; stage_id?: number; user_id?: number; priority?: string;
    partner_id?: number; team_id?: number;
  } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [['active', '=', true]];
    if (options.user_id !== undefined) domain.push(['user_id', '=', options.user_id]);
    if (options.stage_id) domain.push(['stage_id', '=', options.stage_id]);
    if (options.priority) domain.push(['priority', '=', options.priority]);
    if (options.partner_id) domain.push(['partner_id', '=', options.partner_id]);
    if (options.team_id) domain.push(['team_id', '=', options.team_id]);
    const result = await this.searchRead('helpdesk.ticket', domain,
      ['id', 'name', 'ticket_ref', 'team_id', 'stage_id', 'user_id', 'partner_id', 'priority', 'kanban_state', 'sla_deadline', 'sla_fail', 'create_date', 'close_date'],
      { limit: options.limit ?? 30, order: 'priority desc, create_date desc' });
    return result.records;
  }

  async createHelpdeskTicket(values: {
    name: string; team_id?: number; partner_id?: number;
    description?: string; priority?: '0' | '1' | '2' | '3'; user_id?: number;
  }): Promise<number> {
    return this.create('helpdesk.ticket', {
      name: values.name,
      team_id: values.team_id || false,
      partner_id: values.partner_id || false,
      description: values.description || '',
      priority: values.priority || '0',
      user_id: values.user_id || false,
    });
  }

  async getHelpdeskStages(teamId?: number): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (teamId) domain.push(['team_ids', 'in', [teamId]]);
    const result = await this.searchRead('helpdesk.stage', domain,
      ['id', 'name', 'sequence', 'fold'], { order: 'sequence asc' });
    return result.records;
  }

  // ==================== Accounting ====================

  async getInvoices(options: {
    limit?: number; move_type?: string; state?: string;
    partner_id?: number; payment_state?: string;
  } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [['move_type', 'in', options.move_type
      ? [options.move_type]
      : ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']]];
    if (options.state) domain.push(['state', '=', options.state]);
    if (options.partner_id) domain.push(['partner_id', '=', options.partner_id]);
    if (options.payment_state) domain.push(['payment_state', '=', options.payment_state]);
    const result = await this.searchRead('account.move', domain,
      ['id', 'name', 'move_type', 'partner_id', 'state', 'invoice_date', 'invoice_date_due', 'amount_total', 'payment_state', 'invoice_status'],
      { limit: options.limit ?? 20, order: 'invoice_date desc' });
    return result.records;
  }

  async getOverdueInvoices(): Promise<OdooRecord[]> {
    const result = await this.searchRead('account.move', [
      ['move_type', '=', 'out_invoice'],
      ['state', '=', 'posted'],
      ['payment_state', 'not in', ['paid', 'reversed']],
      ['invoice_date_due', '<', today()],
    ],
      ['id', 'name', 'partner_id', 'invoice_date_due', 'amount_total', 'payment_state'],
      { limit: 30, order: 'invoice_date_due asc' });
    return result.records;
  }

  // ==================== 联系人 / 客户 ====================

  async getPartners(options: {
    limit?: number; is_company?: boolean; customer_rank?: boolean;
    supplier_rank?: boolean; keyword?: string;
  } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [['active', '=', true]];
    if (options.is_company !== undefined) domain.push(['is_company', '=', options.is_company]);
    if (options.customer_rank) domain.push(['customer_rank', '>', 0]);
    if (options.supplier_rank) domain.push(['supplier_rank', '>', 0]);
    if (options.keyword) domain.push(['name', 'ilike', options.keyword]);
    const result = await this.searchRead('res.partner', domain,
      ['id', 'name', 'email', 'phone', 'mobile', 'is_company', 'city', 'country_id', 'customer_rank', 'supplier_rank', 'parent_id'],
      { limit: options.limit ?? 30, order: 'name asc' });
    return result.records;
  }

  async createPartner(values: {
    name: string; email?: string; phone?: string; mobile?: string;
    is_company?: boolean; city?: string; street?: string;
    customer_rank?: number; supplier_rank?: number; parent_id?: number;
  }): Promise<number> {
    return this.create('res.partner', {
      name: values.name,
      email: values.email || false,
      phone: values.phone || false,
      mobile: values.mobile || false,
      is_company: values.is_company ?? false,
      city: values.city || false,
      street: values.street || false,
      customer_rank: values.customer_rank ?? 1,
      supplier_rank: values.supplier_rank ?? 0,
      parent_id: values.parent_id || false,
    });
  }

  // ==================== 库存 ====================

  async getStockLevels(options: {
    limit?: number; product_id?: number; location_id?: number; keyword?: string;
  } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [['quantity', '>', 0]];
    if (options.product_id) domain.push(['product_id', '=', options.product_id]);
    if (options.location_id) domain.push(['location_id', '=', options.location_id]);
    if (options.keyword) domain.push(['product_id.name', 'ilike', options.keyword]);
    const result = await this.searchRead('stock.quant', domain,
      ['id', 'product_id', 'location_id', 'lot_id', 'quantity', 'reserved_quantity', 'available_quantity'],
      { limit: options.limit ?? 50, order: 'product_id asc' });
    return result.records;
  }

  async getStockPickings(options: {
    limit?: number; state?: string; picking_type?: string;
  } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (options.state) domain.push(['state', '=', options.state]);
    else domain.push(['state', 'not in', ['done', 'cancel']]);
    if (options.picking_type) domain.push(['picking_type_code', '=', options.picking_type]);
    const result = await this.searchRead('stock.picking', domain,
      ['id', 'name', 'partner_id', 'picking_type_id', 'state', 'scheduled_date', 'date_done', 'origin'],
      { limit: options.limit ?? 20, order: 'scheduled_date asc' });
    return result.records;
  }

  // ==================== HR ====================

  async getEmployees(options: { limit?: number; department_id?: number; active?: boolean; keyword?: string } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [['active', '=', options.active !== false]];
    if (options.department_id) domain.push(['department_id', '=', options.department_id]);
    if (options.keyword) domain.push(['name', 'ilike', options.keyword]);
    const result = await this.searchRead('hr.employee', domain,
      ['id', 'name', 'department_id', 'job_id', 'work_email', 'mobile_phone', 'parent_id', 'user_id'],
      { limit: options.limit ?? 50, order: 'name asc' });
    return result.records;
  }

  async getLeaves(options: { limit?: number; state?: string; employee_id?: number } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (options.state) domain.push(['state', '=', options.state]);
    if (options.employee_id) domain.push(['employee_id', '=', options.employee_id]);
    else domain.push(['employee_id.user_id', '=', this.uid ?? 0]);
    const result = await this.searchRead('hr.leave', domain,
      ['id', 'name', 'employee_id', 'holiday_status_id', 'date_from', 'date_to', 'number_of_days', 'state'],
      { limit: options.limit ?? 20, order: 'date_from desc' });
    return result.records;
  }

  async getAttendances(options: { limit?: number; employee_id?: number } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (options.employee_id) domain.push(['employee_id', '=', options.employee_id]);
    else domain.push(['employee_id.user_id', '=', this.uid ?? 0]);
    const result = await this.searchRead('hr.attendance', domain,
      ['id', 'employee_id', 'check_in', 'check_out', 'worked_hours'],
      { limit: options.limit ?? 20, order: 'check_in desc' });
    return result.records;
  }

  // ==================== 审批 ====================

  async getApprovals(options: { limit?: number; state?: string; my_requests?: boolean } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (options.state) domain.push(['request_status', '=', options.state]);
    if (options.my_requests) domain.push(['request_owner_id.user_id', '=', this.uid ?? 0]);
    const result = await this.searchRead('approval.request', domain,
      ['id', 'name', 'category_id', 'request_owner_id', 'request_status', 'date', 'date_confirmed', 'amount', 'reason'],
      { limit: options.limit ?? 20, order: 'date desc' });
    return result.records;
  }

  // ==================== Mail / Activity ====================

  async getTodayActivities(options: { limit?: number } = {}): Promise<OdooRecord[]> {
    const result = await this.searchRead('mail.activity',
      [['user_id', '=', this.uid ?? 0], ['date_deadline', '<=', today()]],
      ['id', 'summary', 'date_deadline', 'activity_type_id', 'res_model', 'res_id', 'note', 'state'],
      { limit: options.limit ?? 50 });
    return result.records;
  }

  async createActivity(values: {
    res_model: string; res_id: number; activity_type_id: number;
    summary?: string; note?: string; date_deadline: string; user_id?: number;
  }): Promise<number> {
    return this.create('mail.activity', {
      res_model: values.res_model, res_id: values.res_id,
      activity_type_id: values.activity_type_id,
      summary: values.summary || '', note: values.note || '',
      date_deadline: values.date_deadline,
      user_id: values.user_id ?? this.uid ?? 1,
    });
  }

  async getActivityTypes(): Promise<OdooRecord[]> {
    const result = await this.searchRead('mail.activity.type', [],
      ['id', 'name', 'icon', 'category', 'delay_count', 'delay_unit'], { order: 'name asc' });
    return result.records;
  }

  /**
   * 完成活动（闭环）—— 调 mail.activity.action_feedback：
   * 活动标记为 done、写入反馈到源记录 chatter、从活动列表里移除。
   * 这是 Odoo 活动闭环的正式 API，不要直接 unlink。
   */
  async completeActivity(id: number, feedback?: string): Promise<unknown> {
    return this.call('mail.activity', 'action_feedback', [[id]], {
      feedback: feedback || '',
    });
  }

  /** 改期：把活动的 date_deadline 挪到新日期（YYYY-MM-DD） */
  async rescheduleActivity(id: number, newDeadline: string): Promise<boolean> {
    return this.write('mail.activity', [id], { date_deadline: newDeadline });
  }

  async createCalendarEvent(values: {
    name: string; start: string; stop: string;
    description?: string; partner_ids?: number[]; alarm_ids?: number[];
  }): Promise<number> {
    return this.create('calendar.event', {
      name: values.name, start: values.start, stop: values.stop,
      description: values.description || '',
      partner_ids: values.partner_ids ? [[6, false, values.partner_ids]] : [[6, false, [this.uid ?? 1]]],
      alarm_ids: values.alarm_ids ? [[6, false, values.alarm_ids]] : false,
    });
  }

  /**
   * 获取今日会议/日程 —— 覆盖 [今天 00:00, 明天 00:00) 区间里与我相关的事件。
   * 包含：我是组织者、或我是参与者（partner_ids 含 my partner_id）。
   */
  async getCalendarToday(options: { limit?: number } = {}): Promise<OdooRecord[]> {
    const t = today();
    const next = tomorrow();
    const uid = this.uid ?? 0;
    // 我的 partner_id 需要先查一次（cached on session user_context 里没有，所以 read res.users）
    let myPartnerId: number | false = false;
    try {
      const users = await this.read('res.users', [uid], ['partner_id']);
      const pid = users[0]?.['partner_id'];
      if (Array.isArray(pid) && typeof pid[0] === 'number') myPartnerId = pid[0];
    } catch { /* ignore */ }

    const domain: Domain = [
      ['start', '>=', `${t} 00:00:00`],
      ['start', '<', `${next} 00:00:00`],
    ];
    if (myPartnerId) {
      domain.unshift('|', ['user_id', '=', uid], ['partner_ids', 'in', [myPartnerId]]);
    } else {
      domain.unshift(['user_id', '=', uid]);
    }

    const result = await this.searchRead('calendar.event', domain,
      ['id', 'name', 'start', 'stop', 'duration', 'location', 'partner_ids', 'description', 'user_id', 'allday'],
      { limit: options.limit ?? 30, order: 'start asc' });
    return result.records;
  }

  /** 更新日历事件（时间、地点、标题、描述、参与者） */
  async updateCalendarEvent(id: number, values: {
    name?: string; start?: string; stop?: string; location?: string;
    description?: string; partner_ids?: number[];
  }): Promise<boolean> {
    const payload: Record<string, unknown> = {};
    if (values.name !== undefined) payload['name'] = values.name;
    if (values.start !== undefined) payload['start'] = values.start;
    if (values.stop !== undefined) payload['stop'] = values.stop;
    if (values.location !== undefined) payload['location'] = values.location;
    if (values.description !== undefined) payload['description'] = values.description;
    if (values.partner_ids !== undefined) payload['partner_ids'] = [[6, false, values.partner_ids]];
    if (Object.keys(payload).length === 0) return true;
    return this.write('calendar.event', [id], payload);
  }

  /** 取消日历事件：active=false（软删除，保留历史），而不是 unlink */
  async cancelCalendarEvent(id: number): Promise<boolean> {
    return this.write('calendar.event', [id], { active: false });
  }

  // ==================== 关注者（followers）====================
  //
  // Odoo 的 mail.thread 混入提供：
  //   - message_subscribe(partner_ids, subtype_ids?) — 添加关注者
  //   - message_unsubscribe(partner_ids)              — 移除关注者
  //   - message_follower_ids                           — 列表
  // 任何继承 mail.thread 的模型（project.task、crm.lead、helpdesk.ticket、
  // sale.order、res.partner 等）都能用。

  async followRecord(model: string, resId: number, partnerIds?: number[]): Promise<unknown> {
    // 默认关注者 = 当前用户的 partner_id
    let targets = partnerIds;
    if (!targets || targets.length === 0) {
      const uid = this.uid ?? 0;
      const users = await this.read('res.users', [uid], ['partner_id']);
      const pid = users[0]?.['partner_id'];
      if (Array.isArray(pid) && typeof pid[0] === 'number') targets = [pid[0]];
      else throw new Error('无法获取当前用户的 partner_id');
    }
    return this.call(model, 'message_subscribe', [[resId]], { partner_ids: targets });
  }

  async unfollowRecord(model: string, resId: number, partnerIds?: number[]): Promise<unknown> {
    let targets = partnerIds;
    if (!targets || targets.length === 0) {
      const uid = this.uid ?? 0;
      const users = await this.read('res.users', [uid], ['partner_id']);
      const pid = users[0]?.['partner_id'];
      if (Array.isArray(pid) && typeof pid[0] === 'number') targets = [pid[0]];
      else throw new Error('无法获取当前用户的 partner_id');
    }
    return this.call(model, 'message_unsubscribe', [[resId]], { partner_ids: targets });
  }

  // ==================== 邮件（mail.mail + mail.template）====================
  //
  // 两条路径：
  //   1) 随手发一封：用 message_post 发在某条记录的 chatter，Odoo 会自动
  //      邮件化给 followers（如果 subtype 是 comment）。这是 Odoo 原生的"发邮件"方式。
  //   2) 显式发邮件给任意地址：mail.mail create → send。适合真正"给外部发邮件"场景。
  // 模板：mail.template.send_mail(res_id, force_send=True) 是 Odoo 原生的模板发送入口。

  /**
   * 直接发送邮件（不依赖 chatter）。
   * recipients 为 email 字符串数组（逗号分隔会被 Odoo 自行拆分，但我们显式传逗号拼接）。
   * bodyHtml 建议是 HTML，纯文本会按 <br/> 保留换行。
   */
  async sendEmail(values: {
    subject: string; bodyHtml: string;
    recipients: string[]; cc?: string[]; bcc?: string[];
    res_model?: string; res_id?: number;
    attachment_ids?: number[];
  }): Promise<number> {
    const payload: Record<string, unknown> = {
      subject: values.subject,
      body_html: values.bodyHtml,
      email_to: values.recipients.join(','),
      email_from: false, // Odoo 会用当前用户的邮箱/公司邮箱
    };
    if (values.cc && values.cc.length > 0) payload['email_cc'] = values.cc.join(',');
    if (values.bcc && values.bcc.length > 0) (payload as Record<string, unknown>)['email_bcc'] = values.bcc.join(',');
    if (values.res_model) payload['model'] = values.res_model;
    if (values.res_id) payload['res_id'] = values.res_id;
    if (values.attachment_ids && values.attachment_ids.length > 0) {
      payload['attachment_ids'] = [[6, false, values.attachment_ids]];
    }
    const id = await this.create('mail.mail', payload);
    // 立即发送（否则会等到 cron）
    await this.call('mail.mail', 'send', [[id]]);
    return id;
  }

  async getEmailTemplates(options: { model?: string; keyword?: string; limit?: number } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (options.model) domain.push(['model', '=', options.model]);
    if (options.keyword) domain.push(['name', 'ilike', options.keyword]);
    const result = await this.searchRead('mail.template', domain,
      ['id', 'name', 'model', 'subject', 'email_from', 'email_to', 'use_default_to', 'lang'],
      { limit: options.limit ?? 50, order: 'name asc' });
    return result.records;
  }

  /**
   * 用模板发邮件。template_id 通过 getEmailTemplates 查。
   * res_id 是模板关联模型的记录 id（模板的 model 字段决定）。
   * force_send=true 立即入队发送。
   */
  async sendEmailFromTemplate(templateId: number, resId: number, options: {
    force_send?: boolean; email_values?: Record<string, unknown>;
  } = {}): Promise<unknown> {
    return this.call('mail.template', 'send_mail', [templateId, resId], {
      force_send: options.force_send ?? true,
      email_values: options.email_values ?? false,
    });
  }

  // ==================== 附件（ir.attachment）/ 文档（documents.document）====================
  //
  // ir.attachment 是 Odoo 通用附件表；传 datas（base64 编码）即可。
  // 挂到记录：res_model + res_id 就会在该记录的 chatter/附件面板出现。
  // documents.document 是 Enterprise 文档管理应用，可选 folder_id 归档。

  async attachFile(values: {
    res_model: string; res_id: number;
    name: string; datas_base64: string; mimetype?: string;
  }): Promise<number> {
    return this.create('ir.attachment', {
      name: values.name,
      datas: values.datas_base64,
      res_model: values.res_model,
      res_id: values.res_id,
      type: 'binary',
      mimetype: values.mimetype || 'application/octet-stream',
    });
  }

  async listAttachments(model: string, resId: number, options: { limit?: number } = {}): Promise<OdooRecord[]> {
    const result = await this.searchRead('ir.attachment',
      [['res_model', '=', model], ['res_id', '=', resId]],
      ['id', 'name', 'mimetype', 'file_size', 'create_date', 'create_uid', 'url', 'type'],
      { limit: options.limit ?? 50, order: 'create_date desc' });
    return result.records;
  }

  async uploadDocument(values: {
    name: string; datas_base64: string; mimetype?: string;
    folder_id?: number; tag_ids?: number[];
  }): Promise<number> {
    const payload: Record<string, unknown> = {
      name: values.name,
      datas: values.datas_base64,
      type: 'binary',
      mimetype: values.mimetype || 'application/octet-stream',
    };
    if (values.folder_id) payload['folder_id'] = values.folder_id;
    if (values.tag_ids && values.tag_ids.length > 0) payload['tag_ids'] = [[6, false, values.tag_ids]];
    return this.create('documents.document', payload);
  }

  async getUnreadMessages(options: { limit?: number } = {}): Promise<OdooRecord[]> {
    const result = await this.searchRead('mail.message',
      [['message_type', '!=', 'notification'], ['to_read', '=', true]],
      ['id', 'body', 'date', 'author_id', 'model', 'res_id', 'subject'],
      { limit: options.limit ?? 20 });
    return result.records;
  }

  async getInboxNotifications(options: { limit?: number } = {}): Promise<OdooRecord[]> {
    const result = await this.searchRead('mail.notification',
      [['is_read', '=', false], ['notification_type', '=', 'inbox']],
      ['id', 'mail_message_id', 'notification_status', 'is_read', 'read_date'],
      { limit: options.limit ?? 20 });
    return result.records;
  }

  // ==================== Knowledge（知识库 / knowledge.article）====================
  //
  // Odoo 19 Enterprise 的 `knowledge.article` 模型要点：
  //  - body 字段是 HTML
  //  - category 由 internal_permission 计算得出：
  //      internal_permission='write' → workspace，='none' → private（无 parent 时）
  //      子文章不需要 internal_permission，权限沿 parent 继承
  //  - DB 约束：顶层文章必须给 internal_permission；子文章必须给 parent_id
  //  - 通过 action_toggle_favorite / action_send_to_trash / move_to 等 action 操作
  //  - is_user_favorite 是 compute + search，不能直接 write

  async searchKnowledgeArticles(options: {
    keyword?: string;
    category?: 'workspace' | 'private' | 'shared';
    only_favorite?: boolean;
    only_roots?: boolean;         // 只列顶层文章
    parent_id?: number;           // 列某文章的直接子节点
    limit?: number;
    include_trashed?: boolean;
  } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [];
    if (!options.include_trashed) domain.push(['to_delete', '=', false]);
    domain.push(['active', '=', true]);
    if (options.category) domain.push(['category', '=', options.category]);
    if (options.only_favorite) domain.push(['is_user_favorite', '=', true]);
    if (options.only_roots) domain.push(['parent_id', '=', false]);
    if (options.parent_id !== undefined) domain.push(['parent_id', '=', options.parent_id]);
    if (options.keyword) {
      domain.push('|', ['name', 'ilike', options.keyword], ['body', 'ilike', options.keyword]);
    }
    const result = await this.searchRead('knowledge.article', domain,
      ['id', 'name', 'icon', 'parent_id', 'root_article_id', 'category',
       'is_user_favorite', 'favorite_count', 'last_edition_date', 'last_edition_uid',
       'has_article_children', 'sequence'],
      { limit: options.limit ?? 30, order: 'sequence asc, last_edition_date desc, id desc' });
    return result.records;
  }

  /** 读取单篇文章完整内容（含 body） */
  async readKnowledgeArticle(id: number): Promise<OdooRecord | null> {
    const records = await this.read('knowledge.article', [id],
      ['id', 'name', 'icon', 'body', 'parent_id', 'root_article_id', 'category',
       'internal_permission', 'inherited_permission',
       'is_user_favorite', 'favorite_count', 'is_locked', 'to_delete',
       'last_edition_date', 'last_edition_uid', 'sequence', 'has_article_children']);
    return records[0] ?? null;
  }

  /**
   * 创建知识库文章
   *
   * - 顶层：必须传 category='workspace'|'private'；自动映射到 internal_permission
   *     workspace → 'write'  （默认所有内部用户可编辑）
   *     private   → 'none'   （仅所有者）
   *     shared    → 'none'（通常通过加 member 实现）
   * - 子文章：传 parent_id，其余权限继承
   */
  async createKnowledgeArticle(values: {
    name?: string;
    body?: string;                // HTML
    icon?: string;                // emoji
    parent_id?: number;
    category?: 'workspace' | 'private' | 'shared';
  }): Promise<number> {
    const payload: Record<string, unknown> = {
      name: values.name || '未命名',
      body: values.body ?? false,
      icon: values.icon || false,
    };
    if (values.parent_id) {
      payload['parent_id'] = values.parent_id;
    } else {
      const cat = values.category ?? 'private';
      payload['internal_permission'] = cat === 'workspace' ? 'write' : 'none';
      if (cat === 'workspace') payload['is_article_visible_by_everyone'] = true;
    }
    return this.create('knowledge.article', payload);
  }

  async updateKnowledgeArticle(id: number, values: {
    name?: string; body?: string; icon?: string;
  }): Promise<boolean> {
    const payload: Record<string, unknown> = {};
    if (values.name !== undefined) payload['name'] = values.name;
    if (values.body !== undefined) payload['body'] = values.body;
    if (values.icon !== undefined) payload['icon'] = values.icon || false;
    if (Object.keys(payload).length === 0) return true;
    return this.write('knowledge.article', [id], payload);
  }

  /**
   * 在现有文章的 body 末尾追加一段 HTML —— 读-改-写（Odoo body 字段无原子 append）。
   * 调用者负责把 markdown 之类的输入转成合法 HTML。
   */
  async appendKnowledgeArticle(id: number, htmlSuffix: string): Promise<boolean> {
    const rec = await this.readKnowledgeArticle(id);
    if (!rec) throw new Error(`文章 ${id} 不存在`);
    const body = (rec['body'] as string | false) || '';
    const next = `${body}${htmlSuffix}`;
    return this.write('knowledge.article', [id], { body: next });
  }

  /** 移动到新 parent 或在兄弟节点中排序 */
  async moveKnowledgeArticle(id: number, options: {
    parent_id?: number | false;
    before_article_id?: number;
    category?: 'workspace' | 'private' | 'shared';
  }): Promise<unknown> {
    return this.call('knowledge.article', 'move_to', [[id]], {
      parent_id: options.parent_id ?? false,
      before_article_id: options.before_article_id ?? false,
      category: options.category ?? false,
    });
  }

  async toggleKnowledgeFavorite(id: number): Promise<unknown> {
    return this.call('knowledge.article', 'action_toggle_favorite', [[id]]);
  }

  async trashKnowledgeArticle(id: number): Promise<unknown> {
    return this.call('knowledge.article', 'action_send_to_trash', [[id]]);
  }

  async restoreKnowledgeArticle(id: number): Promise<unknown> {
    return this.call('knowledge.article', 'action_unarchive', [[id]]);
  }

  // ==================== v1.8 — Chatter / Project / Ticket / Approval ====================
  //
  // Chatter = Odoo 的内置沟通轨迹。任何 mail.thread 混入的模型（几乎所有业务模型）
  // 都有 message_post() 方法：
  //   - subtype 'mail.mt_comment'   → 评论，会 email 给 followers
  //   - subtype 'mail.mt_note'      → 内部记录，只留痕不发邮件
  // body 是 HTML；message_type 常用 'comment' / 'notification'。

  /**
   * 在任意记录 chatter 发消息（评论，会通知 followers）。
   * partner_ids 传进来会被当作额外收件人加入。
   */
  async postMessage(model: string, resId: number, values: {
    bodyHtml: string;
    subject?: string;
    partner_ids?: number[];
    attachment_ids?: number[];
    as_log?: boolean;                // true = 内部记录（mt_note），false = 评论（mt_comment）
  }): Promise<number> {
    const kwargs: Record<string, unknown> = {
      body: values.bodyHtml,
      message_type: values.as_log ? 'notification' : 'comment',
      subtype_xmlid: values.as_log ? 'mail.mt_note' : 'mail.mt_comment',
    };
    if (values.subject) kwargs['subject'] = values.subject;
    if (values.partner_ids && values.partner_ids.length > 0) {
      kwargs['partner_ids'] = values.partner_ids;
    }
    if (values.attachment_ids && values.attachment_ids.length > 0) {
      kwargs['attachment_ids'] = values.attachment_ids;
    }
    const result = await this.call(model, 'message_post', [[resId]], kwargs);
    if (typeof result === 'number') return result;
    // Odoo 19 返回的是 mail.message 记录（dict），取 id
    if (typeof result === 'object' && result !== null && 'id' in (result as Record<string, unknown>)) {
      const r = result as Record<string, unknown>;
      return typeof r['id'] === 'number' ? r['id'] : 0;
    }
    return 0;
  }

  /** 读取某条记录的 chatter 消息历史（最新在前） */
  async getMessageHistory(model: string, resId: number, options: {
    limit?: number;
    include_notifications?: boolean;   // 默认 false，过滤掉系统通知（auto-followers 之类）
  } = {}): Promise<OdooRecord[]> {
    const domain: Domain = [['model', '=', model], ['res_id', '=', resId]];
    if (!options.include_notifications) {
      domain.push(['message_type', 'in', ['comment', 'email']]);
    }
    const result = await this.searchRead('mail.message', domain,
      ['id', 'date', 'author_id', 'email_from', 'subject', 'body', 'message_type', 'subtype_id'],
      { limit: options.limit ?? 20, order: 'date desc' });
    return result.records;
  }

  // ------- Project / Milestone ------------------------------------------------

  async createProject(values: {
    name: string;
    partner_id?: number;
    user_id?: number;                   // 项目负责人
    date_start?: string;
    date?: string;                      // 结束日期
    description?: string;
    privacy_visibility?: 'followers' | 'employees' | 'portal';
  }): Promise<number> {
    return this.create('project.project', {
      name: values.name,
      partner_id: values.partner_id || false,
      user_id: values.user_id || this.uid || false,
      date_start: values.date_start || false,
      date: values.date || false,
      description: values.description || '',
      privacy_visibility: values.privacy_visibility || 'employees',
      active: true,
    });
  }

  async createMilestone(values: {
    name: string;
    project_id: number;
    deadline?: string;
  }): Promise<number> {
    return this.create('project.milestone', {
      name: values.name,
      project_id: values.project_id,
      deadline: values.deadline || false,
    });
  }

  // ------- Helpdesk ticket 更新/关闭 ----------------------------------------

  /**
   * 查找某客服团队里 fold=true 的阶段（= 关闭阶段）。
   * 不传 teamId 就找任何 fold=true 的阶段，返回最小 sequence 的那条。
   */
  async findHelpdeskClosedStage(teamId?: number): Promise<OdooRecord | null> {
    const domain: Domain = [['fold', '=', true]];
    if (teamId) domain.push(['team_ids', 'in', [teamId]]);
    const result = await this.searchRead('helpdesk.stage', domain,
      ['id', 'name', 'sequence'], { limit: 1, order: 'sequence asc' });
    return result.records[0] ?? null;
  }

  // ------- 审批 approval.request -------------------------------------------
  //
  // 审批流状态机：
  //   new → pending（action_confirm）→ approved（action_approve）
  //                                  → refused  （action_refuse）
  //                                  → cancel   （action_withdraw）
  // 我们只暴露 approve / refuse 两个最常见的审批人动作；
  // 发起人侧的 action_confirm 可以后续再加。

  async approveApprovalRequest(id: number): Promise<unknown> {
    return this.call('approval.request', 'action_approve', [[id]]);
  }

  async refuseApprovalRequest(id: number): Promise<unknown> {
    return this.call('approval.request', 'action_refuse', [[id]]);
  }

  // ==================== 实施经理每日概况 ====================

  async getDailyBriefing(): Promise<{
    todayTasks: OdooRecord[];
    overdueActivities: OdooRecord[];
    openTickets: OdooRecord[];
    overdueInvoices: OdooRecord[];
    crmFollowUps: OdooRecord[];
    unreadMessages: OdooRecord[];
  }> {
    const uid = this.uid ?? 0;
    const [todayTasks, overdueActivities, openTickets, overdueInvoices, crmFollowUps, unreadMessages] = await Promise.all([
      // 今日截止任务
      this.searchRead('project.task',
        [['user_ids', 'in', [uid]], ['active', '=', true], ['date_deadline', '<=', today()]],
        ['id', 'name', 'project_id', 'date_deadline', 'priority', 'stage_id'], { limit: 20 }),
      // 逾期活动
      this.searchRead('mail.activity',
        [['user_id', '=', uid], ['date_deadline', '<=', today()]],
        ['id', 'summary', 'date_deadline', 'activity_type_id', 'res_model', 'res_id', 'state'], { limit: 20 }),
      // 我的待处理工单
      this.searchRead('helpdesk.ticket',
        [['user_id', '=', uid], ['active', '=', true]],
        ['id', 'name', 'ticket_ref', 'priority', 'stage_id', 'sla_deadline', 'sla_fail'], { limit: 10 }).catch(() => ({ records: [] })),
      // 逾期应收发票
      this.getOverdueInvoices().then(r => ({ records: r })).catch(() => ({ records: [] })),
      // 需要跟进的商机（today activities）
      this.searchRead('crm.lead',
        [['user_id', '=', uid], ['active', '=', true], ['activity_date_deadline', '<=', today()]],
        ['id', 'name', 'partner_id', 'stage_id', 'probability', 'expected_revenue', 'activity_summary'], { limit: 10 }).catch(() => ({ records: [] })),
      // 未读消息
      this.searchRead('mail.message',
        [['message_type', '!=', 'notification'], ['to_read', '=', true]],
        ['id', 'subject', 'author_id', 'date', 'model', 'res_id'], { limit: 10 }),
    ]);

    return {
      todayTasks: todayTasks.records,
      overdueActivities: overdueActivities.records,
      openTickets: openTickets.records,
      overdueInvoices: overdueInvoices.records,
      crmFollowUps: crmFollowUps.records,
      unreadMessages: unreadMessages.records,
    };
  }

  // ==================== 私有传输层 ====================

  private async rpc(endpoint: string, params: Record<string, unknown>): Promise<unknown> {
    const url = `${this.url}${endpoint}`;
    const payload = { jsonrpc: '2.0', method: 'call', id: Date.now(), params };
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.session_id) headers['Cookie'] = `session_id=${this.session_id}`;

    const response = await fetch(url, { method: 'POST', headers, body: JSON.stringify(payload) });
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

    const data = await response.json() as { result?: unknown; error?: OdooError };
    if (data.error) return { error: data.error };
    return data.result;
  }
}
