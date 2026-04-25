#!/usr/bin/env node

import { querySkills } from './query.mjs';

/**
 * List skills matching a query intent.
 * This helps users discover what skills are available for their use case.
 *
 * Usage: node list.mjs "detect people"
 */

async function main() {
  const intent = process.argv[2];
  const topK = parseInt(process.argv[3], 10) || 10;

  if (!intent) {
    console.log('Usage: node list.mjs <intent> [topK]');
    console.log('Example: node list.mjs "detect people falling" 5');
    console.log('');
    console.log('This queries the Yijian platform for skills matching your intent.');
    process.exit(0);
  }

  try {
    const skills = await querySkills(intent, { topK });

    if (skills.length === 0) {
      console.log('No skills found matching your intent.');
      console.log('You can still use multimodal inference: node intent-invoke.mjs "' + intent + '" <image>');
      process.exit(0);
    }

    console.log(`Found ${skills.length} skill(s) matching "${intent}":\n`);

    skills.forEach((skill, index) => {
      const confidence = (skill.confidence * 100).toFixed(1);
      console.log(`${index + 1}. ${skill.name || skill.epId}`);
      console.log(`   ID: ${skill.epId}`);
      console.log(`   Match: ${confidence}%`);
      if (skill.description) {
        console.log(`   Description: ${skill.description}`);
      }
      console.log('');
    });

    console.log('To use a skill directly:');
    console.log(`  node intent-invoke.mjs "${intent}" <image-path>`);
  } catch (err) {
    console.error('Error:', err.message);
    process.exit(1);
  }
}

main();
