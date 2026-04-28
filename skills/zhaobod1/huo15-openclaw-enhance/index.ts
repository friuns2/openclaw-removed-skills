/**
 * 龙虾增强包 (OpenClaw Enhancement Kit)
 *
 * 非侵入式增强插件（v1.2.3 — 多 Agent 隔离）：
 * - 模块1: 结构化记忆系统（按 agentId 隔离，借鉴 Claude Code auto-memory）
 * - 模块2: 工具安全守卫（按 agentId 记录日志，借鉴 Claude Code 权限系统）
 * - 模块3: 提示词增强（按 agentId 注入上下文，借鉴 Claude Code systemPromptSections）
 * - 模块4: 工作流自动化（按 agentId 隔离工作流，借鉴 Claude Code hooks 事件驱动）
 * - 模块5: 增强仪表盘（支持按 Agent 筛选）
 *
 * 完全适配 WeCom 插件的动态 Agent 功能：
 * - 工具使用 OpenClawPluginToolFactory 模式，从 ctx.agentId 获取当前 Agent
 * - 钩子从 ctx.agentId 获取当前 Agent
 * - 每个企微用户/群组的数据完全隔离
 */
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { registerStructuredMemory } from "./src/modules/structured-memory.js";
import { registerTaskPlanner } from "./src/modules/task-planner.js";
import { registerToolSafety } from "./src/modules/tool-safety.js";
import { registerPromptEnhancer } from "./src/modules/prompt-enhancer.js";
import { registerWorkflowHooks } from "./src/modules/workflow-hooks.js";
import { registerDashboard } from "./src/modules/dashboard.js";

import { registerSelfCheck } from "./src/modules/self-check.js";
import { registerMemoryIntegrator } from "./src/modules/memory-integrator.js";
import { registerTodoTracker } from "./src/modules/todo-tracker.js";
import { registerChapterMarks } from "./src/modules/chapter-marks.js";
import { registerModeGate } from "./src/modules/mode-gate.js";
import { registerStatusline } from "./src/modules/statusline.js";
import { registerSpawnTask } from "./src/modules/spawn-task.js";
import { registerSkillDoctor } from "./src/modules/skill-doctor.js";
import { registerScheduledTasksBridge } from "./src/modules/scheduled-tasks-bridge.js";
import { registerSkillInstaller, CLAW_HUB_SKILLS } from "./src/modules/skill-installer.js";
import { registerKbCorpus } from "./src/modules/kb-corpus.js";
import { registerSessionRecap } from "./src/modules/session-recap.js";
import { registerTranscriptSearch } from "./src/modules/transcript-search.js";
import { registerConfigDoctor } from "./src/modules/config-doctor.js";
import { registerSkillRecommender } from "./src/modules/skill-recommender.js";
import { registerSessionLifecycle } from "./src/modules/session-lifecycle.js";
import { registerNativeMemorySurfacer } from "./src/modules/native-memory-surfacer.js";
import { createNotificationQueue } from "./src/modules/notification-queue.js";
import { resolveOpenClawHome } from "./src/utils/resolve-home.js";
import { getDb } from "./src/utils/sqlite-store.js";
import type { EnhancePluginConfig, ToolTier } from "./src/types.js";
import { existsSync } from "node:fs";
import { join } from "node:path";

/**
 * 工具分层映射（v5.6）：
 * - L1 minimal: 记忆核心 / 状态栏 / spawn / 模式 / 章节 / installer / integrator
 * - L2 balanced (default): +todo / 定时任务桥
 * - L3 full: +workflow / safety / task-planner / session-recap / skill-doctor
 *
 * 只会载入 tier 内的模块，其他模块整个不 register（省下 tool schema 全部重量）。
 */
type Tier = 1 | 2 | 3;
const TIER_MAX: Record<ToolTier, Tier> = {
  minimal: 1,
  balanced: 2,
  full: 3,
};

export default definePluginEntry({
  id: "enhance",
  name: "龙虾增强包 (OpenClaw Enhancement Kit)",
  description: "结构化记忆、工具安全守卫、提示词增强、工作流自动化、仪表盘",

  register(api) {
    const config = (api.pluginConfig ?? {}) as EnhancePluginConfig;
    const toolTier: ToolTier = config.toolTier ?? "balanced";
    const maxTier: Tier = TIER_MAX[toolTier];

    // 初始化共享数据库和通知队列
    const openclawHome = resolveOpenClawHome(api);
    const db = getDb(openclawHome);
    const notifyQueue = createNotificationQueue(db, config.notifications);

    // 模块清单（v5.6 新增 tier 字段）：
    // tier 1 = 常驻层（最高 ROI，任何时候都暴露）
    // tier 2 = 均衡层（常用但非必须，默认启用）
    // tier 3 = 完整层（专业场景，minimal/balanced 下不暴露）
    // 非工具类模块（仪表盘、通知、自检、prompt-enhancer、kb-corpus）标 tier 1：它们不占工具 schema，不影响 per-turn 成本。
    const modules: Array<{ name: string; tier: Tier; enabled: boolean; load: () => void }> = [
      // ── 工具模块（占 tool schema）──
      {
        name: "结构化记忆",
        tier: 1,
        enabled: config.memory?.enabled !== false,
        load: () => registerStructuredMemory(api, config.memory),
      },
      {
        name: "状态栏",
        tier: 1,
        enabled: config.statusline?.enabled !== false,
        load: () => registerStatusline(api, db, notifyQueue),
      },
      {
        name: "子任务派发",
        tier: 1,
        enabled: true,
        load: () => registerSpawnTask(api),
      },
      {
        name: "模式闸门",
        tier: 1,
        enabled: config.mode?.enabled === true,
        load: () => registerModeGate(api, config.mode, notifyQueue),
      },
      {
        name: "技能安装器",
        tier: 1,
        enabled: true,
        load: () => registerSkillInstaller(api),
      },
      {
        name: "记忆整合",
        tier: 1,
        enabled: config.memory?.enabled !== false,
        load: () => registerMemoryIntegrator(api, config.contextPruner),
      },
      {
        name: "章节标记",
        tier: 2,
        enabled: config.chapters?.enabled !== false,
        load: () => registerChapterMarks(api),
      },
      {
        name: "任务追踪",
        tier: 2,
        enabled: config.todos?.enabled !== false,
        load: () => registerTodoTracker(api, notifyQueue),
      },
      {
        name: "定时任务桥",
        tier: 2,
        enabled: config.scheduledTasks?.enabled !== false,
        load: () => registerScheduledTasksBridge(api),
      },
      {
        name: "历史会话搜索",
        tier: 2,
        enabled: config.transcriptSearch?.enabled !== false,
        load: () => registerTranscriptSearch(api),
      },
      {
        name: "工作流自动化",
        tier: 3,
        enabled: config.workflows?.enabled !== false,
        load: () => registerWorkflowHooks(api, config.workflows),
      },
      {
        name: "工具安全",
        tier: 3,
        enabled: config.safety?.enabled !== false,
        load: () => registerToolSafety(api, config.safety),
      },
      {
        name: "任务规划",
        tier: 3,
        enabled: true,
        load: () => registerTaskPlanner(api),
      },
      {
        name: "会话回顾",
        tier: 3,
        enabled: config.sessionRecap?.enabled !== false,
        load: () => registerSessionRecap(api, config.sessionRecap),
      },
      {
        name: "技能巡检",
        tier: 3,
        enabled: true,
        load: () => registerSkillDoctor(api),
      },

      // ── 非工具模块（不占 tool schema，tier 不影响）──
      {
        name: "提示词增强",
        tier: 1,
        enabled: config.prompt?.enabled !== false,
        load: () => registerPromptEnhancer(api, config.prompt),
      },
      {
        name: "输出自检",
        tier: 1,
        enabled: config.selfCheck?.enabled !== false,
        load: () => registerSelfCheck(api, config.selfCheck),
      },
      {
        name: "仪表盘",
        tier: 1,
        enabled: config.dashboard?.enabled !== false,
        load: () => registerDashboard(api, config.dashboard, notifyQueue, db),
      },
      {
        name: "共享知识库语料",
        tier: 1,
        enabled: config.kbCorpus?.enabled !== false,
        load: () => registerKbCorpus(api, config.kbCorpus),
      },
      {
        // v5.7.3: 启动期诊断 ~/.openclaw/openclaw.json 陷阱配置
        // tier=1，minimal 也启用——这是关键的 'Context limit exceeded' 兜底诊断
        name: "配置诊断",
        tier: 1,
        enabled: config.configDoctor?.enabled !== false,
        load: () => registerConfigDoctor(api, config.configDoctor, notifyQueue),
      },
      {
        // v5.7.5: 按用户需求挑已装 skill / 推荐未装 / 给自建规划
        // tier=2 balanced 默认启用；minimal 不暴露（用户多半已经知道用啥 skill）
        name: "技能推荐",
        tier: 2,
        enabled: config.skillRecommender?.enabled !== false,
        load: () => registerSkillRecommender(api, config.skillRecommender),
      },
      {
        // v5.7.7: 接入 openclaw 4.22 的 session_start/end/before_reset/subagent_* hook
        // tier=1 minimal 也启用——这是核心生命周期补全，零工具 schema（纯 hook 监听）
        name: "会话生命周期",
        tier: 1,
        enabled: config.sessionLifecycle?.enabled !== false,
        load: () => registerSessionLifecycle(api, config.sessionLifecycle, notifyQueue),
      },
      {
        // v5.7.10: 主动 surface 龙虾原生 .md memory 文件锚点
        // tier=1 minimal 也启用——零工具 schema（纯 before_prompt_build hook）+ 解决"第二天失忆"
        name: "原生记忆 surface",
        tier: 1,
        enabled: config.nativeMemorySurfacer?.enabled !== false,
        load: () => registerNativeMemorySurfacer(api, config.nativeMemorySurfacer),
      },
      // 智能贴士已合并到小火苗模块（before_prompt_build 统一输出）
      // {
      //   name: "智能贴士",
      //   tier: 3,
      //   enabled: config.tips?.enabled !== false,
      //   load: () => { console.error("[idx] loading spinner-tips..."); registerSpinnerTips(api, config.tips, notifyQueue); },
      // },
    ];

    const loaded: string[] = [];
    const skipped: string[] = [];
    for (const mod of modules) {
      if (!mod.enabled) continue;
      if (mod.tier > maxTier) {
        skipped.push(mod.name);
        continue;
      }
      try {
        mod.load();
        loaded.push(mod.name);
      } catch (err) {
        api.logger.error(`[enhance] 模块「${mod.name}」加载失败: ${err instanceof Error ? err.message : String(err)}`);
      }
    }
    if (skipped.length > 0) {
      api.logger.info(
        `[enhance] toolTier=${toolTier}：按分层策略跳过 ${skipped.length} 个模块（${skipped.join("、")}）。改 config.toolTier = "full" 可全部启用。`,
      );
    }

    // 首次启动提示：配套技能需手动安装（插件不执行外部命令，只给提示）
    try {
      const globalSkillsDir = join(openclawHome, "workspace", "skills");
      const missing = CLAW_HUB_SKILLS.filter(
        (s) => !existsSync(join(globalSkillsDir, s)),
      );
      if (missing.length > 0) {
        api.logger.info(
          `[enhance] 检测到 ${missing.length} 个配套技能未安装：${missing.join("、")}；` +
            `调用 enhance_install_skills 获取一键安装命令，或手动运行 clawhub install <技能名> --dir ${globalSkillsDir}`,
        );
      }
    } catch {
      // 静默跳过（非关键路径）
    }

    api.logger.info(`[enhance] 龙虾增强包 v5.6.0 已加载（toolTier=${toolTier}，非侵入式，不重复龙虾原生功能），启用模块: ${loaded.join("、")}`);
  },
});
