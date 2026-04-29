/**
 * v5.7.3 配置诊断模块
 *
 * 启动期 + 工具按需，主动检查 ~/.openclaw/openclaw.json 里常见的"导致 Context limit exceeded"陷阱：
 *
 * 1. 缺失 agents.defaults.compaction.reserveTokensFloor — openclaw 4.22 默认值过小
 * 2. reserveTokensFloor 异常（< 5000 或 > 100000）
 * 3. 任意 model 的 maxTokens 占 contextWindow 一半以上 且 > 32000
 *    （openclaw 把 maxTokens 当作必须留给输出的 reserve，吃掉太多 budget）
 *
 * 红线：
 * - 完全只读 openclaw.json，绝不修改用户配置（红线 #1：不侵入式修改 openclaw）
 * - 不用 child_process（红线 #4）
 * - 修复命令通过 return-cliCmd 模式给出，让用户手工或 cron-cli 执行（红线 #5）
 */
import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { Type } from "@sinclair/typebox";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import type { OpenClawPluginToolContext } from "openclaw/plugin-sdk/core";
import { resolveOpenClawHome } from "../utils/resolve-home.js";
import type { ConfigDoctorConfig, NotificationQueue } from "../types.js";
import { DEFAULT_AGENT_ID } from "../types.js";

/**
 * v5.7.4: 检测某条 pluginApi / peerDep 范围是否是合规的 ranged spec。
 * "2026.4.11" → bare（精确匹配，被 openclaw 4.22 拒绝）
 * ">=2026.4.11" / "^2026.4.11" / "~2026.4.11" / "*" / undefined → OK
 *
 * 见 KB `~/.claude/projects/-Users-jobzhao/memory/openclaw_plugin_compat_rules.md`
 */
function isBarePluginApi(spec: unknown): spec is string {
  if (typeof spec !== "string") return false;
  const s = spec.trim();
  if (!s) return false;
  // 任何带前缀的 range 都 OK
  if (/^(>=|<=|>|<|\^|~|\*|=)/.test(s)) return false;
  // 含空格说明是组合 range（如 ">=1.0 <2.0"）也 OK
  if (/\s/.test(s)) return false;
  // 剩下的就是 bare 字符串（如 "2026.4.11"）
  return /^\d/.test(s);
}

/**
 * v5.7.4: 扫所有已装插件的 package.json 检测 bare pluginApi
 * 扫描路径：
 * - {openclawDir}/extensions/<plugin>/package.json
 * - {openclawDir}/node_modules/@huo15/<plugin>/package.json（旧 npm peerDep 残留）
 * - {openclawDir}/node_modules/<plugin>/package.json（无 scope 的）
 */
function scanInstalledPluginsForBarePluginApi(openclawDir: string): CheckResult[] {
  const results: CheckResult[] = [];
  const dirsToScan: string[] = [];

  // extensions 目录
  const extDir = join(openclawDir, "extensions");
  if (existsSync(extDir)) {
    try {
      for (const name of readdirSync(extDir)) {
        const p = join(extDir, name);
        if (statSync(p).isDirectory()) dirsToScan.push(p);
      }
    } catch {
      /* 静默 */
    }
  }

  // node_modules 下的 @huo15/* 和无 scope 的（不递归子 node_modules）
  const nmDir = join(openclawDir, "node_modules");
  if (existsSync(nmDir)) {
    try {
      for (const name of readdirSync(nmDir)) {
        if (name === ".bin" || name === ".package-lock.json") continue;
        const p = join(nmDir, name);
        try {
          if (!statSync(p).isDirectory()) continue;
        } catch {
          continue;
        }
        if (name.startsWith("@")) {
          // scope: 进入扫子目录
          try {
            for (const sub of readdirSync(p)) {
              const sp = join(p, sub);
              try {
                if (statSync(sp).isDirectory()) dirsToScan.push(sp);
              } catch {
                /* skip */
              }
            }
          } catch {
            /* skip */
          }
        } else {
          dirsToScan.push(p);
        }
      }
    } catch {
      /* 静默 */
    }
  }

  for (const dir of dirsToScan) {
    const pkgPath = join(dir, "package.json");
    if (!existsSync(pkgPath)) continue;
    let pkg: any;
    try {
      pkg = JSON.parse(readFileSync(pkgPath, "utf-8"));
    } catch {
      continue;
    }
    // 只扫声明了 openclaw extensions 的包
    if (!pkg?.openclaw?.extensions && !pkg?.peerDependencies?.openclaw) continue;
    const name = pkg?.name ?? dir;
    const compatApi = pkg?.openclaw?.compat?.pluginApi;
    if (isBarePluginApi(compatApi)) {
      const fixed = `>=${compatApi}`;
      results.push({
        ok: false,
        level: "warn",
        category: "plugin-bare-pluginApi",
        message: `已装插件 ${name}（${pkgPath}）的 openclaw.compat.pluginApi="${compatApi}" 是 bare 版本，会被解读为精确匹配，与当前 openclaw 不兼容时启动报错"插件要求 ${compatApi}"`,
        fixCommand: `python3 -c "import json,pathlib;p=pathlib.Path('${pkgPath}');c=json.loads(p.read_text());c.setdefault('openclaw',{}).setdefault('compat',{})['pluginApi']='${fixed}';p.write_text(json.dumps(c,indent=2,ensure_ascii=False));print('OK')"`,
      });
    }
  }
  return results;
}

interface CheckResult {
  ok: boolean;
  level: "info" | "warn" | "error";
  category: string;
  message: string;
  fixCommand?: string;
}

/**
 * 同步读 openclaw.json 并检查 — 调用方负责 try-catch 隔离启动失败
 */
export function checkOpenClawConfig(
  openclawDir: string,
  options: ConfigDoctorConfig = {},
): CheckResult[] {
  const minFloor = options.minReserveTokensFloor ?? 5000;
  const maxFloor = options.maxReserveTokensFloor ?? 100000;
  const maxModelMax = options.maxModelMaxTokens ?? 32000;

  const path = join(openclawDir, "openclaw.json");
  const results: CheckResult[] = [];

  if (!existsSync(path)) {
    return [
      {
        ok: false,
        level: "warn",
        category: "config-missing",
        message: `未找到 ${path}（openclaw 还没初始化过）`,
        fixCommand: "openclaw configure",
      },
    ];
  }

  let cfg: Record<string, any>;
  try {
    cfg = JSON.parse(readFileSync(path, "utf-8"));
  } catch (err) {
    return [
      {
        ok: false,
        level: "error",
        category: "config-parse-failed",
        message: `openclaw.json 解析失败：${(err as Error).message}`,
        fixCommand: "检查 ~/.openclaw/openclaw.json 的 JSON 语法（多余逗号 / 引号未闭合等）",
      },
    ];
  }

  // 1. agents.defaults.compaction.reserveTokensFloor
  const compaction = cfg?.agents?.defaults?.compaction ?? {};
  const reserveFloor = compaction.reserveTokensFloor;

  if (reserveFloor === undefined || reserveFloor === null) {
    results.push({
      ok: false,
      level: "warn",
      category: "compaction-missing-reserveTokensFloor",
      message:
        "缺少 agents.defaults.compaction.reserveTokensFloor — openclaw 4.22 默认值偏小，长 session 容易 'Context limit exceeded'。推荐 20000",
      fixCommand:
        `python3 -c "import json,pathlib;p=pathlib.Path.home()/'.openclaw'/'openclaw.json';c=json.loads(p.read_text());c.setdefault('agents',{}).setdefault('defaults',{}).setdefault('compaction',{})['reserveTokensFloor']=20000;p.write_text(json.dumps(c,indent=2,ensure_ascii=False));print('OK: reserveTokensFloor=20000')"`,
    });
  } else if (typeof reserveFloor !== "number") {
    results.push({
      ok: false,
      level: "error",
      category: "compaction-invalid-type",
      message: `agents.defaults.compaction.reserveTokensFloor=${JSON.stringify(reserveFloor)} 不是 number`,
      fixCommand: "改 ~/.openclaw/openclaw.json: agents.defaults.compaction.reserveTokensFloor = 20000（数字，不带引号）",
    });
  } else if (reserveFloor < minFloor) {
    results.push({
      ok: false,
      level: "warn",
      category: "compaction-low-reserveTokensFloor",
      message: `agents.defaults.compaction.reserveTokensFloor=${reserveFloor} 偏低（推荐 ≥ 20000，至少 ≥ ${minFloor}）`,
      fixCommand: "改 ~/.openclaw/openclaw.json: agents.defaults.compaction.reserveTokensFloor = 20000",
    });
  } else if (reserveFloor > maxFloor) {
    results.push({
      ok: false,
      level: "error",
      category: "compaction-huge-reserveTokensFloor",
      message: `agents.defaults.compaction.reserveTokensFloor=${reserveFloor} 太大（≥ ${maxFloor}），可能让每次压缩都失败`,
      fixCommand: "改 ~/.openclaw/openclaw.json: agents.defaults.compaction.reserveTokensFloor = 20000",
    });
  }

  // 2. 各 model maxTokens 检查
  const providers = cfg?.models?.providers ?? {};
  if (typeof providers === "object" && providers !== null) {
    for (const [pname, pval] of Object.entries(providers)) {
      const models = (pval as any)?.models ?? [];
      if (!Array.isArray(models)) continue;
      for (const m of models) {
        const ctx = Number(m?.contextWindow ?? 0);
        const maxT = Number(m?.maxTokens ?? 0);
        const id = String(m?.id ?? "?");
        if (!ctx || !maxT) continue;
        // maxTokens 占 contextWindow 一半以上 且 > maxModelMax 阈值
        if (maxT >= ctx / 2 && maxT > maxModelMax) {
          results.push({
            ok: false,
            level: "warn",
            category: "model-maxTokens-too-large",
            message: `${pname}/${id}: maxTokens=${maxT} 占 contextWindow=${ctx} 一半以上（${Math.round((maxT / ctx) * 100)}%），每轮预留输出会吃掉太多 budget。建议 ≤ 16384`,
            fixCommand: `改 ~/.openclaw/openclaw.json: models.providers.${pname}.models[].maxTokens（id=${id}）从 ${maxT} 改为 16384`,
          });
        }
      }
    }
  }

  // v5.7.4: 扫所有已装插件的 bare pluginApi（违反 ">=X.Y.Z" 规则的会被 openclaw 拒绝）
  const pluginIssues = scanInstalledPluginsForBarePluginApi(openclawDir);
  results.push(...pluginIssues);

  if (results.length === 0) {
    return [
      {
        ok: true,
        level: "info",
        category: "config-ok",
        message: "openclaw 配置 + 已装插件 pluginApi 全部健康（reserveTokensFloor / model maxTokens / plugin compat 均合规）",
      },
    ];
  }
  return results;
}

function formatResults(results: CheckResult[]): string {
  return results
    .map((r) => {
      const icon = r.ok ? "✅" : r.level === "error" ? "❌" : "⚠️";
      let line = `${icon} [${r.category}] ${r.message}`;
      if (r.fixCommand) line += `\n   → 修复: ${r.fixCommand}`;
      return line;
    })
    .join("\n\n");
}

export function registerConfigDoctor(
  api: OpenClawPluginApi,
  config: ConfigDoctorConfig | undefined,
  notifyQueue: NotificationQueue,
) {
  const openclawDir = resolveOpenClawHome(api);

  // 启动期检查（fire-and-forget，绝不阻塞插件加载）
  try {
    const results = checkOpenClawConfig(openclawDir, config);
    const issues = results.filter((r) => !r.ok);
    if (issues.length > 0) {
      api.logger.warn(`[enhance-config-doctor] 检测到 ${issues.length} 项 openclaw.json 配置问题:`);
      for (const r of issues) {
        api.logger.warn(`  • [${r.level}] ${r.category}: ${r.message}`);
        if (r.fixCommand) api.logger.warn(`    → 修复: ${r.fixCommand}`);
      }
      const hasError = issues.some((r) => r.level === "error");
      notifyQueue.emit(
        DEFAULT_AGENT_ID,
        hasError ? "warn" : "warn",
        "config-doctor",
        `enhance: openclaw.json 检测到 ${issues.length} 项配置问题`,
        formatResults(issues) + "\n\n（运行 enhance_config_doctor 工具看完整诊断）",
      );
    } else {
      api.logger.info("[enhance-config-doctor] openclaw.json 配置健康");
    }
  } catch (err) {
    // 启动检查失败不能让插件 crash —— 静默 + log
    api.logger.error(
      `[enhance-config-doctor] 启动检查失败（不影响插件其它功能）: ${(err as Error).message}`,
    );
  }

  // 工具：手动触发完整诊断（输出可粘贴的 fix 命令）
  api.registerTool(
    ((_ctx: OpenClawPluginToolContext) => ({
      name: "enhance_config_doctor",
      description: "诊断 ~/.openclaw/openclaw.json 是否有 reserveTokensFloor / maxTokens 等导致 'Context limit exceeded' 的陷阱配置；只读，给修复命令不自动改",
      parameters: Type.Object({}),
      async execute() {
        const results = checkOpenClawConfig(openclawDir, config);
        const text = formatResults(results);
        return { content: [{ type: "text" as const, text }] };
      },
    })) as any,
    { name: "enhance_config_doctor" },
  );

  api.logger.info("[enhance] 配置诊断模块已加载（只读，不修改用户配置）");
}
