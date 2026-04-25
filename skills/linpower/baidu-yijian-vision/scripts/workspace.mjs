#!/usr/bin/env node

import path from 'path';
import { fileURLToPath } from 'url';
import { httpsRequest, getApiKey, workspacesGetUrl, workspaceSkillsGetUrl } from './utils.mjs';
import { readCache, writeCache, getCacheDir } from './cache.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const CACHE_DIR = getCacheDir();
const WORKSPACE_CACHE_FILE = path.join(CACHE_DIR, 'workspace-cache.json');
const SKILLS_CACHE_FILE = path.join(CACHE_DIR, 'skills-cache.json');
const SKILLS_CACHE_TTL = 60 * 60 * 1000; // 1 hour in ms

function buildEpId(workspaceId, localName) {
  // localName format: c-sk-XXXXX → extract XXXXX part
  const suffix = localName.replace(/^c-sk-/, '');
  return `ep-${workspaceId}-${suffix}`;
}

// ── API Functions ────────────────────────────────────────────────────

/**
 * Get the default workspace ID. Uses long-lived cache (tied to API key).
 */
export async function getDefaultWorkspaceId() {
  const cached = readCache(WORKSPACE_CACHE_FILE);
  if (cached?.workspaceId) return cached.workspaceId;

  const apiKey = getApiKey();
  const url = workspacesGetUrl();
  const { statusCode, body } = await httpsRequest(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
  });

  if (statusCode !== 200) {
    throw new Error(`workspaces/get failed: HTTP ${statusCode} - ${body}`);
  }

  const resp = JSON.parse(body);
  if (!resp.success || !resp.page?.result) {
    throw new Error(`workspaces/get unexpected response: ${body}`);
  }

  const defaultWorkspace = resp.page.result.find(ws => ws.type === 'default');
  if (!defaultWorkspace) {
    throw new Error('No default workspace found');
  }

  const workspaceId = defaultWorkspace.id;
  writeCache(WORKSPACE_CACHE_FILE, { workspaceId, timestamp: Date.now() });
  return workspaceId;
}

/**
 * Get all released SkillApi skills from the default workspace.
 * Uses file cache with 1-hour TTL. Each skill includes pre-constructed epId.
 */
export async function getWorkspaceSkills() {
  const cached = readCache(SKILLS_CACHE_FILE, SKILLS_CACHE_TTL);
  if (cached?.skills) return cached.skills;

  const workspaceId = await getDefaultWorkspaceId();
  const apiKey = getApiKey();
  const url = workspaceSkillsGetUrl(workspaceId);

  const allSkills = [];
  let pageNo = 1;
  const pageSize = 50;

  // Paginate to fetch all skills
  while (true) {
    const { statusCode, body } = await httpsRequest(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        workspaceID: workspaceId,
        orderBy: 'last_published_at',
        order: 'desc',
        pageNo,
        pageSize,
        publicationKinds: ['SkillApi'],
        status: 'Released',
      }),
    });

    if (statusCode !== 200) {
      throw new Error(`skills/get failed: HTTP ${statusCode} - ${body}`);
    }

    const resp = JSON.parse(body);
    if (!resp.success || !resp.page?.result) {
      throw new Error(`skills/get unexpected response: ${body}`);
    }

    const skills = resp.page.result.map(skill => ({
      epId: buildEpId(workspaceId, skill.localName),
      displayName: skill.displayName,
      description: skill.description || '',
      localName: skill.localName,
      workspaceId,
    }));

    allSkills.push(...skills);

    const totalCount = resp.page.totalCount || 0;
    if (allSkills.length >= totalCount || skills.length < pageSize) break;
    pageNo++;
  }

  writeCache(SKILLS_CACHE_FILE, { workspaceId, skills: allSkills, timestamp: Date.now() });
  return allSkills;
}

// ── CLI ──────────────────────────────────────────────────────────────

async function main() {
  const command = process.argv[2];

  if (command === 'list-skills') {
    try {
      const skills = await getWorkspaceSkills();
      if (skills.length === 0) {
        console.log('No private workspace skills found.');
        return;
      }
      console.log(`Private workspace skills (${skills.length} total):\n`);
      for (const skill of skills) {
        const desc = skill.description ? ` - ${skill.description}` : '';
        console.log(`  ${skill.epId}  ${skill.displayName}${desc}`);
      }
    } catch (err) {
      console.error(`Error: ${err.message}`);
      process.exit(1);
    }
  } else {
    console.log('Usage: node workspace.mjs list-skills');
    console.log('');
    console.log('Commands:');
    console.log('  list-skills    List all released private workspace skills');
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
