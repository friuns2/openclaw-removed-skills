#!/usr/bin/env node

import https from 'https';
import http from 'http';

/**
 * Make an HTTPS (or HTTP) request. Returns a Promise that resolves to { statusCode, headers, body }.
 */
export function httpsRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const mod = parsedUrl.protocol === 'https:' ? https : http;
    const reqOptions = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
      path: parsedUrl.pathname + parsedUrl.search,
      method: options.method || 'GET',
      headers: options.headers || {},
    };

    const req = mod.request(reqOptions, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => {
        const body = Buffer.concat(chunks).toString('utf-8');
        resolve({ statusCode: res.statusCode, headers: res.headers, body });
      });
    });

    req.on('error', reject);

    if (options.body) {
      req.write(options.body);
    }
    req.end();
  });
}

/**
 * Get the API key from environment. Throws if not set.
 */
export function getApiKey() {
  const key = process.env.YIJIAN_API_KEY;
  if (!key) {
    throw new Error('YIJIAN_API_KEY environment variable is not set. Please configure it in ~/.claude/settings.json under "env".');
  }
  return key;
}

/**
 * Construct the metadata URL for a given ep-id.
 */
export function metadataUrl(epId) {
  return `https://yijian-next.cloud.baidu.com/api/skills/v1/${epId}/metadata`;
}

/**
 * Construct the run URL for a given ep-id.
 */
export function runUrl(epId) {
  return `https://yijian-next.cloud.baidu.com/api/skills/v1/${epId}/run`;
}

/**
 * Construct the router query URL for intent-based skill matching.
 */
export function routerQueryUrl() {
  return 'https://yijian.baidubce.com/harness/v1/router/query';
}

/**
 * Construct the router multimodal URL for direct inference.
 */
export function routerMultimodalUrl() {
  return 'https://yijian.baidubce.com/harness/v1/router/multimodal';
}

/**
 * Construct the workspaces get URL.
 */
export function workspacesGetUrl() {
  return 'https://yijian-next.cloud.baidu.com/api/vistudio/v1/workspaces/get';
}

/**
 * Construct the workspace skills get URL.
 */
export function workspaceSkillsGetUrl(workspaceId) {
  return `https://yijian-next.cloud.baidu.com/api/vistudio/v1/workspaces/${workspaceId}/skills/get`;
}
