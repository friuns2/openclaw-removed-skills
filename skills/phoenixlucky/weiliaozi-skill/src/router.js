"use strict";

const HISTORICAL_TIME_PATTERNS = [
  /战国末期/u,
  /战国/u,
  /秦统一前后/u,
  /秦统一/u,
  /秦末/u,
  /楚汉/u,
  /楚汉相争/u,
  /汉建立前/u,
  /二世而亡/u,
  /灭六国/u,
  /late warring states/i,
  /pre[-\s]?han/i,
  /chu[-\s]?han/i,
  /qin collapse/i,
  /fall of qin/i
];

const HISTORICAL_ACTOR_PATTERNS = [
  /魏国/u,
  /秦国/u,
  /楚国/u,
  /项羽/u,
  /刘邦/u,
  /秦王政/u,
  /嬴政/u,
  /李斯/u,
  /王翦/u,
  /王绾/u,
  /韩非/u,
  /张良/u,
  /韩信/u,
  /尉缭/u,
  /黄石公/u,
  /商山四皓/u,
  /\bwei\b/i,
  /\bqin\b/i,
  /\bchu\b/i,
  /\bli si\b/i,
  /\bhan fei\b/i,
  /\bzhang liang\b/i,
  /\bhan xin\b/i,
  /\bxiang yu\b/i,
  /\bliu bang\b/i,
  /\bwei liao\b/i
];

const HISTORICAL_EVENT_PATTERNS = [
  /秦灭亡/u,
  /秦为什么.*亡/u,
  /焚书坑儒/u,
  /陈胜吴广/u,
  /鸿门宴/u,
  /垓下/u,
  /乱局/u,
  /谁占先机/u,
  /统一六国/u,
  /collapse/i,
  /rebellion/i,
  /succession crisis/i,
  /contend/i
];

const HISTORICAL_DIRECT_PATTERNS = [
  /秦灭亡/u,
  /秦为什么.*二世而亡/u,
  /楚汉相争/u,
  /张良.*韩信.*尉缭/u,
  /韩信.*张良.*尉缭/u,
  /\bwhy did qin (fall|collapse)\b/i,
  /\bqin'?s? (fall|collapse)\b/i,
  /\bfall of qin\b/i,
  /\bchu[-\s]?han contention\b/i
];

const PERSONA_OPENING = "臣缭以为";

function findMatches(text, patterns) {
  return patterns
    .filter((pattern) => pattern.test(text))
    .map((pattern) => pattern.toString());
}

function detectLanguage(text) {
  const zh = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  const en = (text.match(/[A-Za-z]/g) || []).length;

  if (zh === 0 && en === 0) {
    return "unknown";
  }

  return zh >= en ? "zh" : "en";
}

function routeWeiliaoziMode(input) {
  const text = String(input || "").trim();
  const language = detectLanguage(text);

  const timeMatches = findMatches(text, HISTORICAL_TIME_PATTERNS);
  const actorMatches = findMatches(text, HISTORICAL_ACTOR_PATTERNS);
  const eventMatches = findMatches(text, HISTORICAL_EVENT_PATTERNS);
  const directMatches = findMatches(text, HISTORICAL_DIRECT_PATTERNS);

  const hasTimeSignal = timeMatches.length > 0;
  const hasActorSignal = actorMatches.length > 0;
  const hasEventSignal = eventMatches.length > 0;
  const matchedSignalCount = [hasTimeSignal, hasActorSignal, hasEventSignal].filter(Boolean).length;

  const historical =
    directMatches.length > 0 ||
    matchedSignalCount >= 2 ||
    (hasTimeSignal && (hasActorSignal || hasEventSignal)) ||
    (hasActorSignal && hasEventSignal);
  const confidence = historical && (directMatches.length > 0 || matchedSignalCount === 3) ? "high" : "medium";

  return {
    mode: historical ? "historical_persona" : "normal_analysis",
    language,
    confidence: historical ? confidence : "high",
    personaOpening: historical ? PERSONA_OPENING : null,
    signals: {
      direct: directMatches,
      time: timeMatches,
      actor: actorMatches,
      event: eventMatches
    },
    reasons: historical
      ? directMatches.length > 0
        ? [
            "Matched an explicit historical route pattern for a documented short prompt.",
            "Historical persona mode should override normal voice but preserve the full five-lens analysis."
          ]
        : [
            "Matched historical routing signals for time/actor/event within late Warring States to pre-Han scope.",
            "Historical persona mode should override normal voice but preserve the full five-lens analysis."
          ]
      : [
          "Did not match enough historical routing signals.",
          "Use the default Wei Liaozi analytical mode without the first-person historical persona."
        ]
  };
}

module.exports = {
  PERSONA_OPENING,
  routeWeiliaoziMode
};
