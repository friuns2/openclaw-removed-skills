#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const CACHE_DIR = path.join(__dirname, '..', '.cache');

function ensureCacheDir() {
  if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
  }
}

/**
 * Read a JSON cache file. Returns null if missing, expired, or invalid.
 */
export function readCache(filePath, ttl) {
  if (!fs.existsSync(filePath)) return null;
  try {
    const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    if (ttl && Date.now() - data.timestamp > ttl) return null;
    return data;
  } catch {
    return null;
  }
}

/**
 * Write a JSON cache file.
 */
export function writeCache(filePath, data) {
  ensureCacheDir();
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
}

/**
 * Get the cache directory path.
 */
export function getCacheDir() {
  return CACHE_DIR;
}
