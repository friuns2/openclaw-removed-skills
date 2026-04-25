#!/usr/bin/env node

import { querySkills } from './query.mjs';
import { callMultimodal } from './multimodal.mjs';
import { runSkill } from './invoke.mjs';
import { getWorkspaceSkills } from './workspace.mjs';

const DEFAULT_CONFIDENCE_THRESHOLD = 0.7;
const MAX_SKILL_RETRIES = 3;

/**
 * Determine if we should use the skill based on confidence threshold.
 */
export function shouldUseSkill(skill, threshold = DEFAULT_CONFIDENCE_THRESHOLD) {
  return !!(skill && skill.epId && typeof skill.confidence === 'number' && skill.confidence >= threshold);
}

/**
 * Format the final result consistently.
 */
export function formatResult(mode, skill, detections = []) {
  return {
    success: true,
    mode,
    epId: skill?.epId || null,
    skillName: skill?.name || null,
    confidence: skill?.confidence || null,
    count: detections.length,
    detections
  };
}

/**
 * Extract detections array from a runSkill() result.
 */
function extractDetections(result) {
  if (result?.未检出) return [];
  const outputs = result?.result?.outputs;
  if (!outputs || outputs.length === 0) return [];
  const output = outputs[0];
  if (output?.parsedValue && Array.isArray(output.parsedValue)) {
    return output.parsedValue;
  }
  return [];
}

/**
 * Main orchestration function:
 * 1. Query router for skills matching intent
 * 2. Try top skills one by one (up to MAX_SKILL_RETRIES)
 * 3. If all skills fail, fallback to multimodal
 */
export async function intentInvoke(intent, imagePath, options = {}) {
  const { threshold = DEFAULT_CONFIDENCE_THRESHOLD, topK = 5 } = options;

  // Step 1: Query for matching skills
  let skills;
  try {
    skills = await querySkills(intent, { topK });
  } catch (err) {
    // Query failed, will fallback to multimodal
    skills = [];
  }

  // Step 2: Try top skills one by one
  const candidates = skills.filter(s => shouldUseSkill(s, threshold)).slice(0, MAX_SKILL_RETRIES);
  for (const skill of candidates) {
    try {
      const { result } = await runSkill(skill.epId, { input0: { image: imagePath } }, { autoROI: true });
      const detections = extractDetections(result);
      return formatResult('skill', skill, detections);
    } catch (err) {
      console.error(`Skill ${skill.epId} (${skill.name}) failed: ${err.message}`);
      // Continue to next skill
    }
  }

  // Step 3: Public skills all failed — search private workspace
  try {
    const privateSkills = await getWorkspaceSkills();
    if (privateSkills.length > 0) {
      return {
        success: true,
        mode: 'workspace-search',
        epId: null,
        skillName: null,
        confidence: null,
        count: 0,
        detections: [],
        privateSkills: privateSkills.map(s => ({
          epId: s.epId,
          displayName: s.displayName,
          description: s.description,
        })),
        hint: '公共技能无匹配。请从 privateSkills 列表中选择最匹配的技能，使用 invoke.mjs 调用。如无合适技能，可调用 multimodal.mjs 回退。',
      };
    }
  } catch (err) {
    console.error(`Private workspace search failed: ${err.message}`);
    // Continue to multimodal fallback
  }

  // Step 4: Fallback to multimodal
  try {
    const detections = await callMultimodal(intent, imagePath);
    return formatResult('multimodal', null, detections);
  } catch (err) {
    return {
      success: false,
      error: err.message,
      mode: 'multimodal',
      epId: null,
      detections: []
    };
  }
}

/**
 * CLI entry point.
 */
async function main() {
  const intent = process.argv[2];
  const imagePath = process.argv[3];
  const threshold = parseFloat(process.argv[4]) || DEFAULT_CONFIDENCE_THRESHOLD;

  if (!intent) {
    console.error('Usage: node intent-invoke.mjs <intent> [image-path] [threshold]');
    console.error('Example: node intent-invoke.mjs "detect people falling" photo.jpg 0.8');
    console.error('');
    console.error('Parameters:');
    console.error('  intent      - Description of what to detect (required)');
    console.error('  image-path  - Path to image file (optional)');
    console.error('  threshold   - Confidence threshold 0.0-1.0 (default: 0.7)');
    process.exit(1);
  }

  try {
    const result = await intentInvoke(intent, imagePath, { threshold });
    console.log(JSON.stringify(result, null, 2));
    process.exit(result.success ? 0 : 1);
  } catch (err) {
    console.error(JSON.stringify({
      success: false,
      error: err.message
    }, null, 2));
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
