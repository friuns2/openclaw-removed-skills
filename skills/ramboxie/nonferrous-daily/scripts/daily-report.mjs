/**
 * daily-report.mjs
 * 调用 fetch-all-data.mjs，生成六板块有色日报，发送至 Telegram
 */

import { readFileSync, existsSync, mkdirSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { execFile } from 'child_process';
import { promisify } from 'util';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..');
const REPORT_CACHE_PATH = join(PROJECT_ROOT, 'memory', 'daily-report-state.json');
const execFileAsync = promisify(execFile);

// ────────────────────────────────────────────
// 读取 .env
// ────────────────────────────────────────────
function loadEnv() {
  const envPath = join(PROJECT_ROOT, '.env');
  const env = {};
  try {
    const content = readFileSync(envPath, 'utf-8');
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx = trimmed.indexOf('=');
      if (eqIdx === -1) continue;
      const key = trimmed.slice(0, eqIdx).trim();
      const value = trimmed.slice(eqIdx + 1).trim().replace(/^["']|["']$/g, '');
      env[key] = value;
    }
    process.stderr.write('[daily-report] ✅ 已读取 .env\n');
  } catch {
    process.stderr.write('[daily-report] ℹ️  未找到 .env\n');
  }
  return env;
}

function normText(s) {
  return (s || '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

function loadReportState() {
  try {
    if (!existsSync(REPORT_CACHE_PATH)) return null;
    const raw = readFileSync(REPORT_CACHE_PATH, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveReportState(state) {
  try {
    const dir = join(PROJECT_ROOT, 'memory');
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    writeFileSync(REPORT_CACHE_PATH, JSON.stringify(state, null, 2), 'utf-8');
  } catch (err) {
    process.stderr.write(`[daily-report] ⚠️ 寫入報告狀態失敗: ${err.message}\n`);
  }
}

function buildSection7Snapshot(d) {
  const ibItems = freshNews(d.ibNews || []);
  const cnNews = freshNews(d.news || []);
  const forum = d.forumSentiment || {};
  return {
    date: d.date,
    ibTitles: [...new Set(ibItems.map(x => normText(x.title)).filter(Boolean))],
    cnTitles: [...new Set(cnNews.map(x => normText(x.title)).filter(Boolean))],
    smmHighlights: normText(forum.smmHighlights),
    redditSurging: normText(forum.redditSurging),
  };
}

function diffSection7(prev, curr) {
  const prevIb = new Set(prev?.ibTitles || []);
  const prevCn = new Set(prev?.cnTitles || []);
  const ibNew = (curr.ibTitles || []).filter(t => !prevIb.has(t));
  const cnNew = (curr.cnTitles || []).filter(t => !prevCn.has(t));
  const smmChanged = !!curr.smmHighlights && curr.smmHighlights !== (prev?.smmHighlights || '');
  const redditChanged = !!curr.redditSurging && curr.redditSurging !== (prev?.redditSurging || '');
  return { ibNew, cnNew, smmChanged, redditChanged };
}

// ────────────────────────────────────────────
// 执行子脚本，返回解析后的 JSON
// ────────────────────────────────────────────
async function runScript(scriptName) {
  const scriptPath = join(__dirname, scriptName);
  const { stdout, stderr } = await execFileAsync(
    process.execPath,
    [scriptPath],
    { timeout: 60000, maxBuffer: 4 * 1024 * 1024 }
  );
  if (stderr) process.stderr.write(stderr);
  return JSON.parse(stdout);
}

// ────────────────────────────────────────────
// 格式化工具
// ────────────────────────────────────────────
function fmtNum(n, decimals = 0) {
  if (n == null) return null;
  const parts = Number(n).toFixed(decimals).split('.');
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return decimals > 0 ? parts.join('.') : parts[0];
}

function fmtPct(pct) {
  if (pct == null) return '—';
  const sign = pct >= 0 ? '▲' : '▼';
  return `${sign}${Math.abs(pct).toFixed(2)}%`;
}

function fmtChange(v) {
  if (v == null || v === 0) return '—';
  const sign = v > 0 ? '▲' : '▼';
  return `${sign}${fmtNum(Math.abs(v))}`;
}

function clamp(text, max = 160) {
  if (!text) return '';
  return text.length > max ? text.slice(0, max) + '…' : text;
}

function emoji(v) {
  if (v == null) return '⚪';
  if (v > 0.1) return '🟢';
  if (v < -0.1) return '🔴';
  return '🔵';
}

function arrow(v) {
  if (v == null) return '➖';
  if (v > 0) return '🔺';
  if (v < 0) return '🔻';
  return '➖';
}

function signScore(v, pos = 0, neg = 0) {
  if (v == null) return '0';
  if (v > pos) return '+';
  if (v < neg) return '-';
  return '0';
}

// ────────────────────────────────────────────
// 日期校验：只保留 48h 内的新闻
// ────────────────────────────────────────────
function freshNews(items) {
  if (!items || items.length === 0) return [];
  const cutoff = Date.now() - 48 * 60 * 60 * 1000;
  return items.filter(item => {
    if (!item.publishedAt) return true;
    const ts = Date.parse(item.publishedAt);
    return isNaN(ts) || ts >= cutoff;
  });
}

function buildImportParity(prices, fx) {
  const fxRate = fx?.price ?? null;
  const fee = { nickel: 1500, copper: 800, zinc: 500 };
  const metals = ['nickel', 'copper', 'zinc'];
  const result = {};
  for (const m of metals) {
    const usdRaw = prices?.[m]?.usd ?? null;
    const unit = prices?.[m]?.usdUnit ?? null;
    const usdPerTon = unit === 'USD/lb' ? (usdRaw != null ? usdRaw * 2204.62 : null) : usdRaw;
    const cny = prices?.[m]?.cny ?? null;
    if (usdPerTon == null || fxRate == null || cny == null) {
      result[m] = null;
      continue;
    }
    const landed = Math.round(usdPerTon * fxRate + fee[m]);
    const pnl = cny - landed; // >0 = 內盤升水，進口盈利
    const status = pnl > 200 ? '盈利' : (pnl < -200 ? '虧損' : '中性');
    result[m] = { usd: usdPerTon, fx: fxRate, landed, domestic: cny, pnl, status, fee: fee[m] };
  }
  return result;
}

function summarizeScores(scores) {
  const pos = Object.values(scores).filter(s => s === '+').length;
  const neg = Object.values(scores).filter(s => s === '-').length;
  if (pos > neg + 1) return '整體偏多（+）';
  if (neg > pos + 1) return '整體偏空（-）';
  return '中性觀望（0）';
}

function usdToCnyPerTon(usd, unit, fxRate) {
  if (usd == null || fxRate == null) return null;
  const usdPerTon = unit === 'USD/lb' ? usd * 2204.62 : usd;
  return usdPerTon * fxRate;
}

function fmtCnyPerTonFromUsd(usd, unit, fxRate, withRaw = false) {
  const cny = usdToCnyPerTon(usd, unit, fxRate);
  if (cny == null) return null;
  return withRaw
    ? `CNY ${fmtNum(cny)}/吨（USD ${fmtNum(usd, unit === 'USD/lb' ? 3 : 0)}${unit === 'USD/lb' ? '/lb' : '/t'}）`
    : `CNY ${fmtNum(cny)}/吨`;
}

function calcBasis(prices, fx, key) {
  const usdRaw = prices?.[key]?.usd ?? null;
  const unit = prices?.[key]?.usdUnit ?? null;
  const usd = unit === 'USD/lb' ? (usdRaw != null ? usdRaw * 2204.62 : null) : usdRaw;
  const cny = prices?.[key]?.cny ?? null;
  const rate = fx?.price ?? null;
  if (usd == null || cny == null || rate == null) return null;
  const importParity = usd * rate;
  return cny - importParity; // >0 = 內盤升水
}

// ────────────────────────────────────────────
// 组装报告
// ────────────────────────────────────────────
function buildReport(d, prevState = null) {
  const p = d.prices;
  const inv = d.inventory || {};
  const fwd = d.forwards?.copper;
  const idx = d.indices || [];
  const fx = d.fxRates?.usdCny || null;
  const fxRate = fx?.price ?? null;
  const macro = d.macro || [];
  const importParity = buildImportParity(p, fx);
  const section7Snapshot = buildSection7Snapshot(d);
  const section7Delta = diffSection7(prevState?.section7, section7Snapshot);
  // 目標品種：Cu / Zn / Ni / Co / Mg / Bi（不含 Al）

  const lines = [];

  // 标题
  const dateStr = new Date().toLocaleDateString('zh-TW', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric', month: '2-digit', day: '2-digit',
  });
  lines.push(`📊 *有色金屬日報* · ${dateStr}`);
  lines.push('');

  // ── 一、行情快照 ──
  lines.push('━━━ 一、行情快照 ━━━');

  // 铜
  const cu = p.copper;
  if (cu) {
    const usdDir = cu.usdChangePct;
    const cuEmoji = emoji(usdDir ?? cu.cnyChange);
    let line = `${cuEmoji} 銅（Cu）`;
    if (cu.usd != null) line += `${fmtCnyPerTonFromUsd(cu.usd, 'USD/lb', fxRate, true) || '—'} ${fmtPct(cu.usdChangePct)} [COMEX]`;
    if (cu.cny != null) line += `  |  CNY ${fmtNum(cu.cny)}/吨 ${fmtChange(cu.cnyChange)} [長江]`;
    lines.push(line);
  }

  // 锌
  const zn = p.zinc;
  if (zn) {
    const znEmoji = emoji(zn.usdChangePct ?? zn.cnyChange);
    let line = `${znEmoji} 鋅（Zn）`;
    if (zn.usd != null) line += `${fmtCnyPerTonFromUsd(zn.usd, 'USD/t', fxRate, true) || '—'} ${fmtPct(zn.usdChangePct)} [LME Cash]`;
    if (zn.cny != null) line += `  |  CNY ${fmtNum(zn.cny)}/吨 ${fmtChange(zn.cnyChange)} [長江]`;
    lines.push(line);
  }

  // 镍
  const ni = p.nickel;
  if (ni) {
    const niEmoji = emoji(ni.usdChangePct ?? ni.cnyChange);
    let line = `${niEmoji} 鎳（Ni）`;
    if (ni.usd != null) line += `${fmtCnyPerTonFromUsd(ni.usd, 'USD/t', fxRate, true) || '—'} ${fmtPct(ni.usdChangePct)} [LME Cash]`;
    if (ni.cny != null) line += `  |  CNY ${fmtNum(ni.cny)}/吨 ${fmtChange(ni.cnyChange)} [長江]`;
    lines.push(line);
  }

  // 钴
  const co = p.cobalt;
  if (co) {
    const coEmoji = emoji(co.cnyChange);
    let line = `${coEmoji} 鈷（Co）`;
    if (co.usd != null) {
      line += `${fmtCnyPerTonFromUsd(co.usd, 'USD/t', fxRate, true) || '—'}`;
      if (co.usdDataDate && co.usdDataDate !== d.date) line += ` (${co.usdDataDate})`;
    }
    if (co.cny != null) line += `  |  CNY ${fmtNum(co.cny)}/吨 ${fmtChange(co.cnyChange)} [長江]`;
    lines.push(line);
  }

  // 铋
  const bi = p.bismuth;
  if (bi) {
    const biEmoji = emoji(bi.cnyChangePct ?? 0);
    let line = `${biEmoji} 鉍（Bi）`;
    if (bi.usd != null) line += `${fmtCnyPerTonFromUsd(bi.usd, 'USD/t', fxRate, true) || '—'}`;
    if (bi.cny != null) line += `  |  CNY ${fmtNum(bi.cny)}/吨 ${fmtChange(bi.cnyChange)} [SMM]`;
    lines.push(line);
  }

  // 镁
  const mg = p.magnesium;
  if (mg?.cny != null) {
    lines.push(`${emoji(mg.cnyChange)} 鎂（Mg）CNY ${fmtNum(mg.cny)}/吨 ${fmtChange(mg.cnyChange)} [CCMN]`);
  } else {
    lines.push('⚪ 鎂（Mg）暫無數據');
  }

  // 铜期货结构
  if (fwd) {
    lines.push('');
    const spot = fwd.spot ? `${fwd.spot.expiry} ${fmtCnyPerTonFromUsd(fwd.spot.price, 'USD/lb', fxRate, true) || '—'}` : '—';
    const near = fwd.near ? `${fwd.near.expiry} ${fmtCnyPerTonFromUsd(fwd.near.price, 'USD/lb', fxRate, true) || '—'}` : '—';
    const far  = fwd.far  ? `${fwd.far.expiry} ${fmtCnyPerTonFromUsd(fwd.far.price, 'USD/lb', fxRate, true) || '—'}` : '—';
    lines.push(`📐 銅期貨結構：${spot} → ${near} → ${far}`);
    // 判断近端结构
    if (fwd.spot && fwd.near) {
      const spread = fwd.near.price - fwd.spot.price;
      const struct = spread < 0 ? '近端 Backwardation（現貨偏緊）' : '近端 Contango（現貨寬鬆）';
      lines.push(`   ${struct}`);
    }
  }

  lines.push('');

  // ── 二、行业指数 ──
  lines.push('━━━ 二、行業指數 ━━━');
  for (const ix of idx) {
    const ixEmoji = emoji(ix.changePct);
    const priceStr = ix.currency === 'USD'
      ? `USD ${fmtNum(ix.price, 2)}`
      : `CNY ${fmtNum(ix.price, 2)}`;
    lines.push(`${ixEmoji} ${ix.symbol}（${ix.name}）${priceStr} ${fmtPct(ix.changePct)}`);
  }
  // A/H 分化判断
  const xme = idx.find(i => i.symbol === 'XME');
  const sw  = idx.find(i => i.symbol === '000812.SS');
  if (xme && sw) {
    if (xme.changePct > 0 && sw.changePct < 0) {
      lines.push('⚡ A/H 分化：美礦走強，A股有色承壓');
    } else if (xme.changePct < 0 && sw.changePct > 0) {
      lines.push('⚡ A/H 分化：A股有色走強，美礦回調');
    }
  }
  lines.push('');

  // ── 三、技术面 ──
  lines.push('━━━ 三、技術面 ━━━');
  if (cu?.usd != null) {
    const cuPrice = cu.usd;
    const support = cuPrice * 0.97;
    const resist  = fwd?.far ? fwd.far.price : (cuPrice * 1.02);
    const cuNowCny = fmtCnyPerTonFromUsd(cuPrice, 'USD/lb', fxRate, true) || '—';
    const supportCny = fmtCnyPerTonFromUsd(support, 'USD/lb', fxRate, true) || '—';
    const resistCny = fmtCnyPerTonFromUsd(resist, 'USD/lb', fxRate, true) || '—';
    lines.push(`• 銅 COMEX：現報 ${cuNowCny}，支撐 ~${supportCny}，阻力參考遠月 ${resistCny}`);
  }
  if (zn?.usd != null) {
    const znTrend = (zn.usdChangePct ?? 0) < -1 ? '短線偏弱，關注支撐' : '橫盤整理，方向待確認';
    lines.push(`• 鋅 LME：${fmtCnyPerTonFromUsd(zn.usd, 'USD/t', fxRate, true) || '—'}，${znTrend}`);
  }
  if (ni?.usd != null) {
    const niTrend = (ni.usdChangePct ?? 0) < -1 ? '下跌通道，暫勿追多' : '區間震盪，等待突破';
    lines.push(`• 鎳 LME：${fmtCnyPerTonFromUsd(ni.usd, 'USD/t', fxRate, true) || '—'}，${niTrend}`);
  }
  if (co?.cny != null) {
    lines.push(`• 鈷 CNY：${fmtNum(co.cny)}/吨，${(co.cnyChange ?? 0) === 0 ? '橫盤，缺乏主導驅動' : ((co.cnyChange ?? 0) > 0 ? '小幅反彈，底部待確認' : '繼續尋底，謹慎')}`);
  }
  if (bi?.cny != null) {
    lines.push(`• 鉍 CNY：${fmtNum(bi.cny)}/吨，波動偏小，流動性受限`);
  }
  if (mg?.cny != null) {
    lines.push(`• 鎂 CNY：${fmtNum(mg.cny)}/吨，${(mg.cnyChange ?? 0) === 0 ? '價格平穩，供需均衡' : ((mg.cnyChange ?? 0) > 0 ? '小幅走高，能源成本驅動' : '回落，關注需求端跟進')}`);
  }
  lines.push('');

  // ── 四、庫存三件套 ──
  lines.push('━━━ 四、庫存三件套 ━━━');
  const exchLine = [
    `Cu ${inv.copper?.tonnes ? fmtNum(inv.copper.tonnes) + 't' : '—'} ${arrow(inv.copper?.change)}${fmtChange(inv.copper?.change)}`,
    `Zn ${inv.zinc?.tonnes ? fmtNum(inv.zinc.tonnes) + 't' : '—'} ${arrow(inv.zinc?.change)}${fmtChange(inv.zinc?.change)}`,
    `Ni ${inv.nickel?.tonnes ? fmtNum(inv.nickel.tonnes) + 't' : '—'} ${arrow(inv.nickel?.change)}${fmtChange(inv.nickel?.change)}`,
  ].join('  |  ');
  lines.push(`交易所 (LME)：${exchLine}`);
  lines.push('保稅區：暫缺（待接入，保留欄位不崩）');
  lines.push('社會庫存：暫缺（待接入，保留欄位不崩）');
  if (inv.copper?.dataDate) {
    lines.push(`_庫存截至 ${inv.copper.dataDate}_`);
  }
  lines.push('');

  // ── 五、進口盈虧 / 到岸成本 ──
  lines.push('━━━ 五、進口盈虧 / 到岸成本 ━━━');
  const fxLine = fx?.price ? `USD/CNY ${fx.price.toFixed(4)} ${fmtPct(fx.changePct)}` : 'USD/CNY 暫缺';
  lines.push(`匯率：${fxLine}；假設含稅費用 Ni ¥1,500 / Cu ¥800 / Zn ¥500`);
  function importLine(key, label) {
    const row = importParity[key];
    if (!row) return `${label}：數據暫缺（外盤或內盤或匯率缺失）`;
    const pnlEmoji = row.pnl > 200 ? '🟢' : (row.pnl < -200 ? '🔴' : '🔵');
    return `${pnlEmoji} ${label}：外盤折算 CNY ${fmtNum(row.usd * row.fx)}/吨（USD ${fmtNum(row.usd)}/t） → 到岸 CNY ${fmtNum(row.landed)}/吨（含費 CNY ${fmtNum(row.fee)}/吨） | 內盤 CNY ${fmtNum(row.domestic)}/吨 → 盈虧 ${row.pnl >= 0 ? '+' : ''}${fmtNum(row.pnl)}/吨（${row.status}）`;
  }
  lines.push(importLine('nickel', '鎳 Ni'));
  lines.push(importLine('copper', '銅 Cu'));
  lines.push(importLine('zinc',   '鋅 Zn'));
  lines.push('');

  // ── 六、信號摘要（+ / 0 / -） ──
  lines.push('━━━ 六、信號摘要（+ / 0 / -） ━━━');
  const invChanges = [inv.copper?.change, inv.zinc?.change, inv.nickel?.change].filter(v => v != null);
  const invDir = invChanges.length ? invChanges.reduce((a, b) => a + b, 0) / invChanges.length : null;
  const invScore = signScore(invDir != null ? -invDir : null); // 去庫為正

  const basisVals = ['copper', 'zinc', 'nickel']
    .map(k => calcBasis(p, fx, k))
    .filter(v => v != null);
  const basisAvg = basisVals.length ? basisVals.reduce((a, b) => a + b, 0) / basisVals.length : null;
  const basisScore = signScore(basisAvg, 100, -100);

  const importPnls = ['nickel', 'copper', 'zinc']
    .map(k => importParity[k]?.pnl)
    .filter(v => v != null);
  const importAvg = importPnls.length ? importPnls.reduce((a, b) => a + b, 0) / importPnls.length : null;
  const importScore = signScore(importAvg, 200, -200);

  const demandVals = [p.copper?.cnyChange, p.zinc?.cnyChange, p.nickel?.cnyChange].filter(v => v != null);
  const demandAvg = demandVals.length ? demandVals.reduce((a, b) => a + b, 0) / demandVals.length : null;
  const demandScore = signScore(demandAvg, 0, 0);

  const scores = { '庫存趨勢': invScore, '基差/升貼水': basisScore, '進口盈虧': importScore, '需求/成交': demandScore };
  lines.push(Object.entries(scores).map(([k, v]) => `${k}:${v}`).join('  |  '));
  lines.push(`總結：${summarizeScores(scores)}（+ 看多 / - 看空 / 0 中性）`);
  lines.push('');

  // ── 七、市场情绪与机构观点（简报版：结论 > 证据 > 影响） ──
  lines.push('━━━ 七、市場情緒與機構觀點 ━━━');

  const ibItems = freshNews(d.ibNews);
  const forum = d.forumSentiment;
  const cnNews = freshNews(d.news);

  function mapInstitutionPrefix(t) {
    if (/goldman/i.test(t)) return '高盛';
    if (/jpmorgan|jp morgan/i.test(t)) return '摩根大通';
    if (/citigroup|citi/i.test(t)) return '花旗';
    if (/morgan stanley/i.test(t)) return '摩根士丹利';
    if (/bank of america|bofa/i.test(t)) return '美銀';
    return '機構';
  }

  function institutionInsight(title) {
    const t = (title || '').toLowerCase();
    if (!t) return null;

    if (t.includes('copper') && (t.includes('range') || t.includes('target'))) {
      return {
        conclusion: '銅價進入高位區間博弈，追高性價比下降。',
        evidence: '機構維持區間/目標價表述，偏「估值錨定」而非趨勢上修。',
        impact: '交易上以回調承接優先，短線不宜在突破位重倉追多。',
      };
    }
    if (t.includes('nickel')) {
      return {
        conclusion: '鎳價主邏輯仍是供應擾動與需求韌性的拉鋸。',
        evidence: '機構新增鎳相關跟蹤，重點落在供應端變化與利潤再分配。',
        impact: '波動率可能抬升，建議分批與輕倉，避免單邊押注。',
      };
    }
    if (t.includes('zinc')) {
      return {
        conclusion: '鋅價偏區間震盪，方向取決於去庫能否延續。',
        evidence: '機構視角聚焦供給收縮與終端修復速度。',
        impact: '若庫存繼續去化可偏多，反之維持區間思路。',
      };
    }
    if (t.includes('forecast') || t.includes('outlook')) {
      return {
        conclusion: '市場進入預期重定價階段，敘事切換快。',
        evidence: '機構發布展望類內容，通常對中期預期有再錨定作用。',
        impact: '應提高對預期差的敏感度，降低純情緒交易比重。',
      };
    }
    return null;
  }

  const ibByTitle = new Map(
    ibItems.map(item => [normText(item.title), item]).filter(([k]) => !!k)
  );

  const institutionLines = section7Delta.ibNew
    .slice(0, 2)
    .map(key => {
      const item = ibByTitle.get(key);
      const raw = item?.title || '';
      if (!raw) return null;
      const inst = mapInstitutionPrefix(raw);
      const insight = institutionInsight(raw);
      if (!insight) {
        return `• ${inst}：未形成可交易新觀點（僅事件更新，暫不納入研判）。`;
      }
      return `• ${inst}｜結論：${insight.conclusion} 證據：${insight.evidence} 影響：${insight.impact}`;
    })
    .filter(Boolean);

  lines.push('*🏦 機構觀點（研報摘要）*');
  if (institutionLines.length) {
    institutionLines.forEach(x => lines.push(x));
  } else {
    lines.push('• 今日無可量化的新機構觀點，維持昨日框架。');
  }
  lines.push('');

  const sentimentEvidence = [];
  const sentimentImpact = [];

  for (const item of cnNews.slice(0, 6)) {
    const t = item.title || '';
    if (/ETF.*上漲|ETF.*反彈|ETF.*漲/.test(t)) {
      sentimentEvidence.push('場內有色ETF走強。');
      sentimentImpact.push('風險偏好修復，但持續性仍需成交配合。');
    }
    if (/現貨.*成交|成交.*清淡|清淡/.test(t)) {
      sentimentEvidence.push('現貨成交偏淡。');
      sentimentImpact.push('上漲更多由預期驅動，現貨跟隨不足。');
    }
    if (/普漲.*告一段落|避險.*失敗|漲幅.*剩/.test(t)) {
      sentimentEvidence.push('普漲敘事降溫。');
      sentimentImpact.push('板塊可能由全面上行轉向分化輪動。');
    }
  }

  if (forum?.smmHighlights) {
    if (/美元下跌/.test(forum.smmHighlights)) {
      sentimentEvidence.push('美元走弱。');
      sentimentImpact.push('對外盤金屬有短線支撐。');
    }
    if (/多晶硅|碳酸鋰|碳酸锂/.test(forum.smmHighlights)) {
      sentimentEvidence.push('新能源鏈波動加大。');
      sentimentImpact.push('鎳鈷情緒面承壓，彈性但不穩定。');
    }
  }

  lines.push('*📡 市場情緒（三句結論）*');
  const hasSentimentDelta = section7Delta.cnNew.length > 0 || section7Delta.smmChanged || section7Delta.redditChanged;
  if (hasSentimentDelta && (sentimentEvidence.length || sentimentImpact.length)) {
    const ev = [...new Set(sentimentEvidence)].slice(0, 3).join('、') || '新增證據有限';
    const im = [...new Set(sentimentImpact)].slice(0, 3).join('、') || '對價格影響中性';
    lines.push(`• 結論：短線情緒修復但分化加劇。`);
    lines.push(`• 證據：${ev}。`);
    lines.push(`• 影響：${im}。`);
  } else {
    lines.push('• 結論：情緒面無新增有效信號，維持中性。');
  }
  lines.push('');

  // ── 八、四维交叉推理与操作参考 ──
  lines.push('━━━ 八、四維交叉推理 ━━━');

  // 宏观维度
  let macroText = '';
  if (xme && sw) {
    if (xme.changePct > 1 && sw.changePct < -1) {
      macroText = `美礦 ETF（XME ${fmtPct(xme.changePct)}）大漲而申萬有色（${fmtPct(sw.changePct)}）同步下挫，A/H 顯著分化。`
        + '核心驅動在於美元定價的 LME 金屬受益於關稅博弈下的供應鏈重構預期，而 A 股有色板塊同時承壓於人民幣匯率波動與下游需求疲弱的雙重壓力。';
    } else if (xme.changePct > 0 && sw.changePct > 0) {
      macroText = `美礦與 A 股有色今日同向上行（XME ${fmtPct(xme.changePct)}，申萬 ${fmtPct(sw.changePct)}），宏觀風險偏好整體改善，短線多頭情緒佔優。`;
    } else if (xme.changePct < 0 && sw.changePct < 0) {
      macroText = `美礦（${fmtPct(xme.changePct)}）與申萬有色（${fmtPct(sw.changePct)}）同步回落，全球風險偏好收縮，基本金屬承壓。`;
    } else {
      macroText = `美礦（${fmtPct(xme.changePct)}）與申萬有色（${fmtPct(sw.changePct)}）方向分化，宏觀訊號混雜，需結合匯率與資金流向研判。`;
    }
  }
  lines.push(`① 宏觀維度：${macroText || '宏觀數據待觀察。'}`);
  lines.push('');

  // 库存维度
  let invText = '';
  const cuInv = inv.copper, znInv = inv.zinc, niInv = inv.nickel;
  const invParts = [];
  if (cuInv?.tonnes != null) {
    invParts.push(cuInv.change > 0
      ? `LME 銅庫存連續累積至 ${fmtNum(cuInv.tonnes)} 噸（+${fmtNum(cuInv.change)}），現貨升水受壓，提示中期需求尚未明顯改善`
      : `LME 銅庫存降至 ${fmtNum(cuInv.tonnes)} 噸（${fmtNum(cuInv.change)}），去庫支撐現貨溢價`);
  }
  if (znInv?.tonnes != null) {
    invParts.push(znInv.change < 0
      ? `鋅庫存持續去化（${fmtNum(znInv.tonnes)} 噸，${fmtNum(znInv.change)}），現貨供應偏緊格局強化`
      : `鋅庫存小幅累積（${fmtNum(znInv.tonnes)} 噸），短期壓力存在`);
  }
  if (niInv?.tonnes != null) {
    invParts.push(`鎳庫存 ${fmtNum(niInv.tonnes)} 噸，變動微小（${fmtNum(niInv.change)}），供需基本均衡`);
  }
  invText = invParts.join('；') + '。';
  lines.push(`② 庫存維度：${invText}`);
  lines.push('');

  // 期货结构维度
  let fwdText = '';
  if (fwd?.spot && fwd?.near && fwd?.far) {
    const nearSpread = fwd.near.price - fwd.spot.price;
    const farSpread  = fwd.far.price - fwd.spot.price;
    if (nearSpread < 0 && farSpread > 0) {
      fwdText = `銅期貨曲線呈「近端 Backwardation、遠端 Contango」V 型結構`
        + `（現月 ${fmtCnyPerTonFromUsd(fwd.spot.price, 'USD/lb', fxRate, true)} → ${fwd.near.expiry} ${fmtCnyPerTonFromUsd(fwd.near.price, 'USD/lb', fxRate, true)} → ${fwd.far.expiry} ${fmtCnyPerTonFromUsd(fwd.far.price, 'USD/lb', fxRate, true)}）。`
        + '近端偏緊反映當前現貨需求仍具支撐，但遠端升水有限，市場對中長期需求擴張持謹慎態度。';
    } else if (nearSpread < 0) {
      fwdText = `銅期貨近端 Backwardation（價差約 ${fmtCnyPerTonFromUsd(Math.abs(nearSpread), 'USD/lb', fxRate, true)}），現貨緊缺預期主導，短線多頭佔優。`;
    } else {
      fwdText = `銅期貨呈 Contango 結構（近月升水約 ${fmtCnyPerTonFromUsd(nearSpread, 'USD/lb', fxRate, true)}），現貨壓力存在，需警惕近月合約換倉成本。`;
    }
    // 高盛目标对比
    if (cu?.usd != null) {
      const cuPerTonne = cu.usd * 2204.62;
      const cuPerTonneCny = fxRate != null ? cuPerTonne * fxRate : null;
      if (cuPerTonne > 11000) {
        const targetCny = fxRate != null ? `約 CNY ${fmtNum(11000 * fxRate)}/吨，` : '';
        fwdText += `\n   ⚠️ 當前銅價折算約 ${cuPerTonneCny != null ? `CNY ${fmtNum(cuPerTonneCny)}/吨` : 'CNY 匯率暫缺'}（USD ${fmtNum(cuPerTonne)}/t），顯著高於高盛 2026/27 目標上限（${targetCny}USD 11,000/t），估值偏貴風險需關注。`;
      }
    }
  } else {
    fwdText = '期貨結構數據缺失，無法判斷曲線形態。';
  }
  lines.push(`③ 結構維度：${fwdText}`);
  lines.push('');

  // 情绪维度（基于当日信号汇总，中文表述，若為英文保留「英文原文」前缀以確保準確）
  const sentParts = [];
  if (sentimentEvidence.length > 0 || sentimentImpact.length > 0) sentParts.push('今日有色相關新聞/社群出現多條異動，詳見上文情緒研判');
  if (forum?.redditSurging) sentParts.push(`Reddit 熱點（英文原文）：${clamp(forum.redditSurging)}`);
  if (forum?.smmHighlights) sentParts.push(`SMM 摘要：${clamp(forum.smmHighlights)}`);
  const sentText = sentParts.length > 0
    ? sentParts.join('；') + '。'
    : '市場情緒中性，暫無顯著異動信號。';
  lines.push(`④ 情緒維度：${sentText}`);

  lines.push('');
  lines.push('━━━ 九、宏觀風險溫度計 ━━━');
  const dxy = macro.find(m => ['^DXY', 'DX-Y.NYB', 'DX=F'].includes(m.symbol));
  const vix = macro.find(m => m.symbol === '^VIX');
  const crb = macro.find(m => ['CRY', 'TRJEFFCR', '^CRB'].includes(m.symbol));
  const tnx = macro.find(m => m.symbol === '^TNX');
  const macroLines = [];
  const macroMsg = [];
  if (dxy) { macroLines.push(`DXY ${dxy.price?.toFixed(2)} ${fmtPct(dxy.changePct)}`); if (dxy.changePct > 0.3) macroMsg.push('美元走強對大宗偏空'); else if (dxy.changePct < -0.3) macroMsg.push('美元走弱利好商品定價'); }
  if (vix) { macroLines.push(`VIX ${vix.price?.toFixed(2)} ${fmtPct(vix.changePct)}`); if (vix.price > 18 || vix.changePct > 5) macroMsg.push('波動上升，風險偏好降'); }
  if (crb) macroLines.push(`CRB ${crb.price?.toFixed(2)} ${fmtPct(crb.changePct)}`);
  if (tnx) { macroLines.push(`美債10Y ${tnx.price?.toFixed(2)}% ${fmtPct(tnx.changePct)}`); if (tnx.changePct > 0.5) macroMsg.push('利率上行，成本壓力↑'); }
  lines.push(macroLines.length ? macroLines.join('  |  ') : '宏觀指標暫缺');
  lines.push(`溫度計：${macroMsg.length ? macroMsg.join('；') : '風險情緒中性'}`);

  lines.push('');
  lines.push('📌 *操作參考（非投資建議）*');

  // 铜（Cu）
  if (cu?.usd != null) {
    const cuP = cu.usd;
    const cuPerTonne = cuP * 2204.62;
    const reeval = fmtCnyPerTonFromUsd(cuP * 0.96, 'USD/lb', fxRate, true) || '—';
    const support = fmtCnyPerTonFromUsd(cuP * 0.97, 'USD/lb', fxRate, true) || '—';
    const resist = fmtCnyPerTonFromUsd(cuP * 1.02, 'USD/lb', fxRate, true) || '—';
    if (inv.copper?.change > 0 && cuPerTonne > 11000) {
      const spotCny = fxRate != null ? `CNY ${fmtNum(cuPerTonne * fxRate)}/吨` : 'CNY 匯率暫缺';
      lines.push(`• 銅：累庫疊加高估值（折噸約 ${spotCny}，USD ${fmtNum(cuPerTonne)}/t，高於高盛上限 USD 11,000/t），建議觀望；回落至 ${reeval} 區域可重新評估。`);
    } else if (fwd?.spot && fwd?.near && fwd.near.price < fwd.spot.price) {
      lines.push(`• 銅：近端偏緊支撐短線，多頭思路不變，${support} 為關鍵支撐，破位止損。`);
    } else {
      lines.push(`• 銅：趨勢偏多，${support} 逢回可關注，上方阻力 ${resist}。`);
    }
  } else {
    lines.push('• 銅：價格數據缺失，暫觀望。');
  }

  // 锌（Zn）
  if (zn?.cny != null) {
    const znC = inv.zinc?.change ?? 0;
    lines.push(znC < 0
      ? `• 鋅：去庫格局持續，供應偏緊支撐底部，CNY ${fmtNum(zn.cny - 500)}/吨 附近逢低可關注，上方壓力 CNY ${fmtNum(zn.cny + 500)}/吨。`
      : `• 鋅：庫存中性，CNY ${fmtNum(zn.cny)}/吨 區間震盪，輕倉觀望，方向明確後跟進。`);
  } else {
    lines.push('• 鋅：價格數據缺失，暫觀望。');
  }

  // 镍（Ni）
  if (ni?.cny != null) {
    const niDir = ni.cnyChange ?? 0;
    if (niDir < -200) {
      lines.push(`• 鎳：CNY ${fmtNum(ni.cny)}/吨 持續走弱，機構多空博弈激烈，建議暫觀望，不宜重倉追空。`);
    } else if (niDir > 200) {
      lines.push(`• 鎳：CNY ${fmtNum(ni.cny)}/吨 反彈，需觀察能否持續，可輕倉試多，嚴格止損。`);
    } else {
      lines.push(`• 鎳：CNY ${fmtNum(ni.cny)}/吨 橫盤整理，等待不銹鋼需求與新能源鏈回暖信號，暫觀望。`);
    }
  } else {
    lines.push('• 鎳：價格數據缺失，暫觀望。');
  }

  // 钴（Co）
  if (co?.cny != null) {
    const coDir = co.cnyChange ?? 0;
    if (coDir > 0) {
      lines.push(`• 鈷：CNY ${fmtNum(co.cny)}/吨 小幅回升，新能源電池需求預期驅動，謹慎追多，等量能確認。`);
    } else if (coDir < 0) {
      lines.push(`• 鈷：CNY ${fmtNum(co.cny)}/吨 繼續承壓，供應過剩格局未改，觀望為主。`);
    } else {
      lines.push(`• 鈷：CNY ${fmtNum(co.cny)}/吨 橫盤，供需再平衡進程緩慢，暫觀望。`);
    }
  } else {
    lines.push('• 鈷：價格數據缺失，暫觀望。');
  }

  // 铋（Bi）
  if (bi?.cny != null) {
    const biDir = bi.cnyChange ?? 0;
    if (Math.abs(biDir) < 1000) {
      lines.push(`• 鉍：CNY ${fmtNum(bi.cny)}/吨 窄幅震盪，市場流動性偏低，不建議短線操作。`);
    } else if (biDir > 0) {
      lines.push(`• 鉍：CNY ${fmtNum(bi.cny)}/吨 上行，半導體/醫藥需求帶動，可輕倉跟多。`);
    } else {
      lines.push(`• 鉍：CNY ${fmtNum(bi.cny)}/吨 回落，關注 CNY ${fmtNum(bi.cny * 0.95)}/吨 支撐。`);
    }
  } else {
    lines.push('• 鉍：價格數據缺失，暫觀望。');
  }

  // 镁（Mg）
  if (mg?.cny != null) {
    const mgDir = mg.cnyChange ?? 0;
    if (mgDir > 0) {
      lines.push(`• 鎂：CNY ${fmtNum(mg.cny)}/吨 上漲，汽車輕量化需求支撐，可關注趨勢多頭機會。`);
    } else if (mgDir < 0) {
      lines.push(`• 鎂：CNY ${fmtNum(mg.cny)}/吨 回落，能源成本下降但需求端偏弱，暫觀望。`);
    } else {
      lines.push(`• 鎂：CNY ${fmtNum(mg.cny)}/吨 平穩，供需均衡，暫觀望。`);
    }
  } else {
    lines.push('• 鎂：價格數據缺失，暫觀望。');
  }

  lines.push('');
  lines.push('_數據來源：Yahoo Finance / CCMN / SMM / Westmetall / TradingEconomics / Reuters_');

  return {
    message: lines.join('\n'),
    state: {
      generatedAt: new Date().toISOString(),
      section7: section7Snapshot,
    },
  };
}

// ────────────────────────────────────────────
// 发送 Telegram
// ────────────────────────────────────────────
async function sendTelegram(token, chatId, text) {
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: 'Markdown' }),
    signal: AbortSignal.timeout(15000),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(`Telegram API error: ${JSON.stringify(data)}`);
  return data;
}

// ────────────────────────────────────────────
// 主流程
// ────────────────────────────────────────────
async function main() {
  const t0 = Date.now();
  process.stderr.write('[daily-report] 开始抓取完整数据...\n');

  const data = await runScript('fetch-all-data.mjs');

  process.stderr.write('[daily-report] 数据抓取完成，生成报告...\n');

  const prevState = loadReportState();
  const { message, state } = buildReport(data, prevState);

  console.log('\n─── 报告预览 ───');
  console.log(message);
  console.log('────────────────\n');

  const env = loadEnv();
  const token = env.TELEGRAM_BOT_TOKEN;
  const chatId = env.TELEGRAM_CHAT_ID;
  const dryRun = process.env.DRY_RUN === '1' || process.env.DRY_RUN === 'true';

  if (!token) {
    process.stderr.write('[daily-report] ⚠️  未配置 TELEGRAM_BOT_TOKEN，跳过发送\n');
    return;
  }

  if (dryRun) {
    process.stderr.write('[daily-report] 🧪 DRY_RUN=1，僅打印預覽不發送 Telegram\n');
    return;
  }

  process.stderr.write(`[daily-report] 发送至 Telegram chat_id=${chatId}...\n`);
  await sendTelegram(token, chatId, message);
  saveReportState(state);
  const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
  process.stderr.write(`[daily-report] ✅ 发送成功！总耗时: ${elapsed}s\n`);
}

main().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
